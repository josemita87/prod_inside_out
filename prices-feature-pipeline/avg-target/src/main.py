from src.feature_store import Connection
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

# Get the data corresponding to each transaction in the feature store with target computed
txs: list[dict] = feature_store.fetch_4f_transactions(
    feature_group_name=config.feature_group_form_4_target,
    feature_group_version=config.feature_group_version,
    filters=config.fourf_filters,
)


#Initialize mapper  
avg_change_mapper = returns_module.Mapper(txs)

tickers = set(tx['ticker'] for tx in txs)

# Process transactions by ticker
for ticker in tickers:

    # Compute avg returns for the given ticker
    updated_txs:pd.DataFrame = avg_change_mapper.process_ticker(
        ticker,
        [tx for tx in txs if tx['ticker'] == ticker], 
        period=timedelta(days=config.delta_period)
    )

    # Clean data & reduce memory space
    updated_txs = returns_module.reduce_mem_storage(
        returns_module.data_cleaning(updated_txs)
    )

    # Push data to fs
    if not updated_txs.empty:
        feature_store.push_data(
            updated_txs,
            fg_name = config.feature_group_push,
            fg_version = config.feature_group_version,
        )
   

