from src.feature_store import Connection, assert_and_format_data, data_cleaning
from src.config import config
import pandas as pd
from src import computations
from loguru import logger

def initialize_data_source():
    if config.hopsworks_connect:
        return Connection()
    return None

def fetch_transactions(data_source)->pd.DataFrame:
    if config.hopsworks_connect:
        return data_source.fetch_4f_transactions(key=config.filter_key, value=config.acquired_disposed)
    df = pd.read_csv(config.csv_path_form4, names=config.headers)
    df[config.filter_key] = df[config.filter_key].astype(str).str.upper().str.strip()
    return df[df[config.filter_key] == config.acquired_disposed]

def fetch_prices(data_source, tickers_to_process):
    if config.hopsworks_connect:
        return data_source.fetch_price_data(tickers_to_process)
    return pd.read_csv(config.csv_path_prices, names=config.prices_headers)

def main():
    # Initialize connection to data source
    data_source = initialize_data_source()

    # Get transactions
    transactions = fetch_transactions(data_source)
    logger.debug(f"Transactions: {transactions}")
    transactions['ticker'] = transactions['ticker'].astype(str).str.upper()

    # Aggregate data
    aggregated_df = computations.data_aggregation(transactions, config.agg_dict)

    # Get the unique tickers to process
    tickers_to_process = transactions['ticker'].unique().tolist()

    # Get the latest price data for the tickers to process
    prices = fetch_prices(data_source, tickers_to_process)

    # Ensure the data is in the correct format
    transactions, prices = assert_and_format_data(transactions, prices)

    # Get targets & price-related features
    target_df = computations.compute_target(aggregated_df, prices, config.delta_period)

    # Compute the average target price
    final_df = computations.compute_avg_target_price(df=target_df, timedelta=config.delta_period)

    # Clean data & reduce memory space
    final_df = data_cleaning(final_df)

    # Save final dataframe to CSV
    final_df.to_csv(config.csv_path_final, index=False)

    # Push data to feature store if not empty
    if config.hopsworks_connect and not final_df.empty:
        data_source.push_returns_data(final_df)

if __name__ == "__main__":
    main()

