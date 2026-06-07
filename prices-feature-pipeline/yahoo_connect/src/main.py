"""Entry point for fetching Yahoo Finance prices into the feature store."""

import logging

import numpy as np
import pandas as pd
import yfinance as yf
from tqdm import tqdm

from src.clean import reduce_mem_storage
from src.config import config
from src.feature_store import Connection

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)


class YahooDataFetcher:
    """Fetch and process price data from Yahoo Finance.

    Attributes:
        feature_store: Connection to the feature store backend.
    """

    def __init__(self):
        """Initialize the fetcher with a feature store connection."""
        self.feature_store = Connection()

    def fetch_data_from_yahoo(self, prices: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
        """Fetches the latest data from Yahoo Finance for the given tickers.

        Args:
            prices (pd.DataFrame): Current prices data for the buffer of tickers.
            tickers (list[str]): List of tickers to fetch data for.

        Returns:
            pd.DataFrame: Updated prices data with the new data only.
        """
        all_prices = pd.DataFrame()

        for ticker in tickers:
            try:
                offset = prices.loc[prices['ticker'] == ticker]['date'].max() if not prices.empty else None

                if offset:
                    offset = pd.to_datetime(offset)
                    new_data = yf.download(ticker, start=offset + pd.Timedelta(days=1))['Close']
                else:
                    new_data = yf.download(ticker)['Close']

                new_data.reset_index(inplace=True)
                new_data['ticker'] = ticker
                new_data.columns = ['date', 'close', 'ticker']
                new_data = reduce_mem_storage(new_data)

                all_prices = pd.concat([all_prices, new_data], axis=0) if not all_prices.empty else new_data

            except Exception as e:
                logger.error(f'Failed to fetch data for {ticker}: {e}')
                continue

        all_prices.sort_values(by=['ticker', 'date'], inplace=True)
        return reduce_mem_storage(all_prices)

    def process_tickers(self) -> None:
        """Process the tickers in batches and fetch data from Yahoo Finance."""
        # Route to the correct feature group
        if config.system_inference:
            data = self.feature_store.fetch_BI4()
        elif config.system_training:
            data = self.feature_store.fetch_BT4(key=config.filter_key, value=config.acquired_disposed)

        # Get the unique tickers from the 'ticker' column
        tickers = np.unique(data['ticker'].tolist())
        logger.debug(len(tickers))

        # Process the tickers in batches
        for i in tqdm(range(0, len(tickers), config.buffer_size), desc='Processing tickers', unit='batch'):
            processing_tickers = tickers[i : i + config.buffer_size]
            current_data = self.feature_store.fetch_P(processing_tickers)
            new_data = self.fetch_data_from_yahoo(current_data, processing_tickers)
            self.feature_store.push_P(new_data)

        logger.debug('Finished processing all tickers')


def main():
    """Main function to initiate the YahooDataFetcher."""
    """time.sleep(config.delay)
    fetcher = YahooDataFetcher()
    fetcher.process_tickers()"""


if __name__ == '__main__':
    main()
