from src.feature_store import Connection, validate_and_reduce_mem_storage, data_cleaning
from src.config import config
import pandas as pd
import dask.dataframe as dd
from src import computations
import time
from loguru import logger


if __name__ == "__main__":
   
    # Initialize connection to Hopsworks
    feature_store = Connection()

    # Get transactions in the feature store
    txs: pd.DataFrame = feature_store.fetch_4f_transactions(
        key=config.filter_key, value=config.acquired_disposed
    )
                         
    # Get the unique tickers to process
    tickers_to_process:list = sorted(txs['ticker'].unique())

    # Get the latest price data from the feature store
    prices = feature_store.fetch_price_data(tickers_to_process)

    # Initialize mapper  
    pct_change_mapper = computations.Mapper(prices)

    # Aggregate data
    aggregated_df = pct_change_mapper.data_aggregation(txs, config.agg_dict)
    
    #Get targets & price-related data
    target_df = pct_change_mapper.compute_returns(txs, config.delta_period)
    
    # Clean data & reduce memory space
    target_df = validate_and_reduce_mem_storage(
        data_cleaning(target_df)
    )

    # Push data to fs
    if not target_df.empty:
        feature_store.push_returns_data(target_df)
