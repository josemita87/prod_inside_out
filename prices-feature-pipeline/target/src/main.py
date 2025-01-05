from src.feature_store import Connection, validate_and_reduce_mem_storage, data_cleaning
from src.config import config
import pandas as pd
import dask.dataframe as dd
from src import returns_module
import time
from loguru import logger


if __name__ == "__main__":
   
    # Get the current time in milliseconds
    time_ms = pd.to_datetime(int(time.time() * 1000), unit='ms', utc=True)

    # Initialize connection to Hopsworks
    feature_store = Connection()

    # Get each transaction in the feature store
    txs: pd.DataFrame = feature_store.fetch_4f_transactions()
    
    # Get the unique tickers to process
    tickers_to_process:list = sorted(txs['ticker'].unique())

    dd_txs: dd.DataFrame = dd.from_pandas(
        txs[txs['acquired_disposed'] == config.acquired_disposed], 
        npartitions=config.npartitions
    )

    # Get historical prices and convert to a Dask DataFrame
    dd_prices: dd.DataFrame = dd.from_pandas(
        feature_store.fetch_price_data(tickers_to_process), 
        npartitions=config.npartitions
    )

    #Initialize buffers
    offset_buffer:dict = {}
    offset_counter:int = 0

    #Initialize mapper  
    pct_change_mapper = returns_module.Mapper(dd_prices)
    target_df = pct_change_mapper.compute_returns(dd_txs, config.delta_period)

    # Clean data & reduce memory space
    target_df = validate_and_reduce_mem_storage(
        data_cleaning(target_df)
    )

    target_df.compute()
    # Push data to fs
    if not updated_txs.empty:
        feature_store.push_returns_data(updated_txs)

    # Apply last materialization jobs
    feature_store.last_materialization_jobs()

