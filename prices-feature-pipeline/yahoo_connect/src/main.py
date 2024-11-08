import yfinance as yf
import pandas as pd
from typing import Tuple
from datetime import datetime
from loguru import logger
from config import config
import feature_store



def tickers_to_process() -> list[str]:
    """Will have to connect to the feature store to get the transactions data and extract the list of present tickers"""
    return ['INFERENCE_VALUE', 'AAPL', 'GOOGL', 'AMZN', 'MSFT', 'TSLA']


def fetch_current_data(tickers_to_process: list[str]) -> Tuple[pd.DataFrame, list[str]]:
    """Fetches the current data from the feature store for the given tickers"""
    _, prices_fv = feature_store.connect_feature_group(tickers_to_process)
    
    current_data: pd.DataFrame = prices_fv.get_batch_data()
    
    if current_data:
        return current_data, tickers_to_process
    


def fetch_data_from_yahoo(prices: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Fetches the latest data from Yahoo Finance for the given tickers"""
    new_prices = pd.DataFrame()

    for ticker in tickers:
        # Get the latest date for each ticker in the current prices data (if any)
        offset:datetime = prices[prices['ticker'] == ticker].index.max() if not prices.empty else None

        if offset:
            new_data = yf.download(ticker, start=offset + pd.Timedelta(days=1))['close'] 
        
        else:
            # If no previous data, fetch from a default start date
            new_data = yf.download(ticker)['close']
        
        # Add ticker column to allow concatenation
        new_data['ticker'] = ticker

        
        logger.debug(f"Fetching data for {ticker} from {offset}...")
        import time
        time.sleep(1)

        new_prices = pd.concat([new_prices, new_data], axis=0)
    
    
    new_prices.reset_index(inplace=True)
    new_prices.sort_values(by=['ticker', 'Date'], inplace=True)
    new_prices.set_index('Date', inplace=True)

    return new_prices


    



if __name__ == '__main__':
    
    tickers = tickers_to_process()

    for i in range(0, len(tickers)):#, config.buffer_size):

        processing_tickers = tickers #When finish initial testing, change to i+config.buffer_size
        current_data = fetch_current_data(processing_tickers)
        updated_data = fetch_data_from_yahoo(current_data, processing_tickers)
        feature_store.push_data(current_data, updated_data)

    transactions, tickers = fetch_current_data()
    transactions = fetch_data_from_yahoo(transactions, tickers)
    feature_store.push_data_to_feature_store(transactions)