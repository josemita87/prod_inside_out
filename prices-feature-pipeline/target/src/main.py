from src.feature_store import Connection, validate_and_reduce_mem_storage, data_cleaning
from src.config import config
import pandas as pd
import dask.dataframe as dd
from src import returns_module
from datetime import timedelta


# Initialize connection to Hopsworks
feature_store = Connection(
    project_name=config.project_name,
    api_key=config.api_key,
)

# Get the data corresponding to each transaction in the feature store
txs: list[dict] = feature_store.fetch_4f_transactions(
    feature_group_name=config.feature_group_form4,
    feature_group_version=config.feature_group_version,
    filters=config.fourf_filters,
)

# Get data of the historical prices and convert to a Dask DataFrame
ddprices: dd.DataFrame = dd.from_pandas(
    feature_store.fetch_price_data(
        feature_group_name=config.feature_group_prices,
        feature_group_version=config.feature_group_version,
        #filters=config.prices_filters,
    ), 
    npartitions=config.npartitions
)


#Initialize mapper  
pct_change_mapper = returns_module.Mapper(ddprices)


# Process transactions by ticker
for ticker in set(tx['ticker'] for tx in txs):
    if ticker == 'DUM':
        continue

    # Process all the ticker's transactions and compute returns
    updated_txs:pd.DataFrame = pct_change_mapper.process_ticker(
        ticker,
        [tx for tx in txs if tx['ticker'] == ticker], 
        timedelta(days = config.delta_period)
    )
    from loguru import logger
    logger.debug(f"Processed {len(updated_txs)} transactions for {ticker}")

    # Clean data & reduce memory space
    updated_txs = validate_and_reduce_mem_storage(
        data_cleaning(updated_txs)
    )
    
    # Push data to fs
    if not updated_txs.empty:
        feature_store.push_data(
            updated_txs,
            fg_name = config.feature_group_returns,
            fg_version = config.feature_group_version,
        )
   

