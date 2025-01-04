from src.feature_store import Connection, validate_and_reduce_mem_storage, data_cleaning
from src.config import config
import pandas as pd
from src import returns_module
from datetime import timedelta
from loguru import logger
import time


def handle_delta_buffer(
    txs: pd.DataFrame, 
    current_time: int, 
    delta_buffer:dict, 
    delta_counter:int
)-> tuple[dict, int]:
    """Handle the delta buffer and update the delta table"""

    timestamp = txs['date'].max().timestamp()
    ticker = txs['ticker'].iloc[0]

    if timestamp > current_time:
        delta_buffer[ticker] = current_time
    else:
        delta_buffer[ticker] = timestamp

    delta_counter +=1
    logger.debug(f'Delta Counter : {delta_counter}')
    # Update offsets
    if delta_counter > config.offset_buffer_size:
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
    txs: pd.DataFrame = feature_store.fetch_4f_transactions()

    # Get the unique tickers to process
    tickers_to_process:list = sorted(txs['ticker'].unique())
   
    #Initialize buffers
    offset_buffer:dict = {}
    offset_counter:int = 0

    #Initialize mapper  
    avg_change_mapper = returns_module.Mapper()

    # Process transactions by ticker
    for ticker in tickers_to_process:

        # Get the offset (datetime) for the ticker
        offset = feature_store.fetch_offset(ticker)

        # Filter transactions to process
        txs_to_process = txs[
            (txs['ticker'] == ticker)
            &(txs['date'] > offset)
        ]
       
        if txs_to_process.empty:
            continue

        # Work on the ticker's unprocessed transactions and compute returns
        updated_txs:pd.DataFrame = avg_change_mapper.process_ticker(
            txs_to_process, 
            timedelta(days=config.delta_period)
        )

        # Add ticker to the delta buffer and handle it
        offset_buffer, offset_counter = handle_delta_buffer(
            updated_txs, 
            time_ms,
            offset_buffer,
            offset_counter
        )
   
        # Clean data & reduce memory space
        updated_txs = validate_and_reduce_mem_storage(
            data_cleaning(updated_txs)
        )

        logger.debug(
            f"Processed {updated_txs} transactions for {ticker}"
        )
        # Push data to fs
        feature_store.push_returns_data(updated_txs)
    
    # Finish remaining materializations
    feature_store.last_materialization_jobs()