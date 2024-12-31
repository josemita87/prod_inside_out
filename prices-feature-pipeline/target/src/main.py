from src.feature_store import Connection, validate_and_reduce_mem_storage, data_cleaning
from src.config import config
import pandas as pd
import dask.dataframe as dd
from src import returns_module
from datetime import timedelta
import time
from loguru import logger




def handle_delta_buffer(
        txs: pd.DataFrame, 
        current_time: int, 
        delta_buffer:dict, 
        delta_counter:int
    )-> tuple[dict, int]:
    """Handle the delta buffer and update the delta table"""

    timestamp = int(txs['date'].max().timestamp())
    ticker = txs['ticker'].iloc[0]

    if timestamp > current_time:
        delta_buffer[ticker] = current_time
    else:
        delta_buffer[ticker] = timestamp

    delta_counter +=1
    logger.debug(f'Delta Counter : {delta_counter}')
    # Update offsets
    if delta_counter > config.delta_buffer_size:
        feature_store.update_delta_table_batch(delta_buffer)
        delta_counter = 0
        delta_buffer = {}

    return delta_buffer, delta_counter


if __name__ == "__main__":
        
    # Get the current time in milliseconds
    time_ms = int(time.time() * 1000)

    # Initialize connection to Hopsworks
    feature_store = Connection()

    # Get each transaction in the feature store
    txs: list[dict] = feature_store.fetch_4f_transactions()

    # Get the unique tickers to process
    tickers_to_process = sorted(list(set(tx['ticker'] for tx in txs)))
   
    # Get historical prices and convert to a Dask DataFrame
    ddprices: dd.DataFrame = dd.from_pandas(
        feature_store.fetch_price_data(tickers_to_process), 
        npartitions=config.npartitions
    )

    #Initialize buffers
    delta_buffer:dict = {}
    delta_counter:int = 0

    #Initialize mapper  
    pct_change_mapper = returns_module.Mapper(ddprices)

    # Process transactions by ticker
    for ticker in tickers_to_process:

        if ticker == 'DUM':
            continue
        
        # Get the offset for the ticker
        offset:int = feature_store.fetch_delta_table(ticker)

        # Filter transactions to process
        txs_to_process = [
            tx for tx in txs if \
            (tx['ticker']==ticker) & 
            (tx['date'].timestamp() > offset)  &
            ((tx['date']+timedelta(days=config.delta_period)).timestamp()<time_ms)         
        ]
        
        if txs_to_process == []:
            continue

        # Work on the ticker's unprocessed transactions and compute returns
        updated_txs:pd.DataFrame = pct_change_mapper.process_ticker(
            ticker,
            txs_to_process, 
            timedelta(days=config.delta_period)
        )

        # Add ticker to the delta buffer and handle it
        delta_buffer, delta_counter = handle_delta_buffer(
            updated_txs, 
            time_ms,
            delta_buffer,
            delta_counter
        )

        # Clean data & reduce memory space
        updated_txs = validate_and_reduce_mem_storage(
            data_cleaning(updated_txs)
        )

        logger.debug(
            f"Processed {len(updated_txs)} transactions for {ticker}"
        )
        # Push data to fs
        if not updated_txs.empty:
            feature_store.push_returns_data(updated_txs)
    

    #TODO 

    # Change the logic of extracting and updating prices feature group to only update those of the transactions being processed!