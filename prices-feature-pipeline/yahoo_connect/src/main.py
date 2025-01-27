import yfinance as yf
import pandas as pd
from datetime import datetime
from loguru import logger
from src.config import config
from src.feature_store import Connection, reduce_mem_storage
import time
import os
from tqdm import tqdm


def initialize_data_source():
    if config.hopsworks_connect:
        return Connection()
    return None

def fetch_data_from_yahoo(prices: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Fetches the latest data from Yahoo Finance for the given tickers
    
    Args: 
        prices (pd.DataFrame): Current prices data for the buffer of tickers
        tickers (list[str]): List of tickers to fetch data for
    Returns:
        pd.DataFrame: Updated prices data with the new data only
    """
    all_prices = pd.DataFrame()

    for ticker in tickers:
        try:
            offset = prices.loc[prices['ticker'] == ticker]['date'].max() if not prices.empty else None
            if offset:
                offset = pd.to_datetime(offset)  # Ensure offset is a Timestamp
                new_data = yf.download(ticker, start=offset + pd.Timedelta(days=1))['Close']
            else:
                new_data = yf.download(ticker)['Close']

            new_data.reset_index(inplace=True)
            new_data['ticker'] = ticker
            new_data.columns = ['date', 'close', 'ticker']
            new_data = reduce_mem_storage(new_data)

            all_prices = pd.concat([all_prices, new_data], axis=0) if not all_prices.empty else new_data
        except Exception as e:
            #logger.error(f"Failed to fetch data for {ticker}: {e}")
            continue

    all_prices.sort_values(by=['ticker', 'date'], inplace=True)
    return reduce_mem_storage(all_prices)

def fetch_tickers(data_source):
    if config.hopsworks_connect:
        return data_source.fetch_ticker_data().unique().tolist()
    
    # Read the CSV file with the specified headers
    df = pd.read_csv(config.csv_path_form4, names=config.headers)
    
    # Ensure the 'ticker' column is in uppercase
    df['ticker'] = df['ticker'].astype(str).str.upper()
    
    return df['ticker'].unique().tolist()

def fetch_current_data(data_source, processing_tickers):
    if config.hopsworks_connect:
        return data_source.fetch_price_data(processing_tickers=processing_tickers)
    current_data = pd.read_csv(config.csv_path_prices, names=config.prices_headers)
    return current_data[current_data['ticker'].isin(processing_tickers)]

def push_data(data, data_source):
  
    if data_source:
        data_source.push_data(data)
        return
    with open(config.csv_path_prices, 'a') as f:
        data.to_csv(f, header=False, index=False)

def main():
    data_source = initialize_data_source()
    tickers = fetch_tickers(data_source)
    logger.debug(len(tickers))

    # Use tqdm to display the progress bar
    for i in tqdm(range(0, len(tickers), config.buffer_size), desc="Processing tickers", unit="batch"):
        processing_tickers = tickers[i:i+config.buffer_size]
        logger.debug(f"Processing tickers {processing_tickers}...")

        current_data = fetch_current_data(data_source, processing_tickers)
        new_data = fetch_data_from_yahoo(current_data, processing_tickers)
        push_data(new_data, data_source)

    logger.debug('Finished processing all tickers')
    if data_source:
        data_source.materialization_jobs()

if __name__ == '__main__':
    main()