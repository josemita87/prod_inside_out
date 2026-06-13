"""Price-ingestion domain logic: refresh the prices (P) feature group.

Reads the tickers referenced by the transaction feature groups, pulls their
latest close history through the market-data client, and upserts it into the
price feature group. The market-data vendor (currently yfinance) is an
implementation detail hidden behind ``MarketDataClient``.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from inside_out_clients.feature_store import HopsworksClient, load_feature_group_catalog
from inside_out_clients.market_data import MarketDataClient
from tqdm import tqdm

from src.config import config
from src.constants import FeatureGroup

logger = logging.getLogger(__name__)

# Catalog of feature groups this service touches, loaded from the YAML spec template.
FEATURE_GROUPS = load_feature_group_catalog(Path(__file__).parent / 'feature_groups.yaml', config.feature_group_version)


class PriceIngestor:
    """Pull close-price history and upsert it into the price feature group.

    Attributes:
        feature_store: Connection to the feature store backend.
        market_data: Vendor-agnostic market-data client.
    """

    def __init__(self):
        """Wire the feature-store and market-data clients."""
        self.feature_store = HopsworksClient(config.project_name, config.hopsworks_api_key, FEATURE_GROUPS)
        self.market_data = MarketDataClient()

    def fetch_new_prices(self, prices: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
        """Fetch close history for ``tickers``, resuming each from its latest stored date.

        Args:
            prices (pd.DataFrame): Current prices data for the buffer of tickers.
            tickers (list[str]): List of tickers to fetch data for.

        Returns:
            pd.DataFrame: New close-price rows, tagged by ticker.
        """
        # Resume each known ticker from the day after its latest stored price; the
        # rest fall back to full history. The per-ticker loop, downcast and
        # skip-on-failure now live in MarketDataClient.close_histories.
        starts = {}
        if not prices.empty:
            latest = prices.groupby('ticker')['date'].max()
            # Skip NaT maxima: an unresumable ticker falls back to full history
            # (start absent → None) rather than feeding NaT into the download.
            starts = {
                ticker: pd.to_datetime(date) + pd.Timedelta(days=1)
                for ticker, date in latest.items()
                if pd.notna(date)
            }

        return self.market_data.close_histories(tickers, starts=starts)

    def process_tickers(self) -> None:
        """Refresh the price feature group for every referenced ticker, in batches."""
        # Route to the correct feature group
        if config.system_inference:
            data = self.feature_store.read(FeatureGroup.BI4, read_options={'use_hive': True})
        elif config.system_training:
            data = self.feature_store.read(
                FeatureGroup.BT4,
                where=lambda fg: fg.filter(fg[config.filter_key] == config.acquired_disposed),
                read_options={'use_hive': True},
            )
        else:
            raise RuntimeError('No run mode selected: set SYSTEM_INFERENCE or SYSTEM_TRAINING')

        # Get the unique tickers from the 'ticker' column
        tickers = np.unique(data['ticker'].tolist())
        logger.debug(len(tickers))

        # Process the tickers in batches
        for i in tqdm(range(0, len(tickers), config.buffer_size), desc='Processing tickers', unit='batch'):
            processing_tickers = tickers[i : i + config.buffer_size]
            try:
                # Bind the batch into the lambda so it captures this iteration's value.
                current_data = self.feature_store.read(
                    FeatureGroup.PRICES,
                    where=lambda fg, batch=processing_tickers: fg.filter(fg['ticker'].isin(batch)),
                    read_options={'use_hive': True},
                )
            except Exception:
                current_data = pd.DataFrame()
            new_data = self.fetch_new_prices(current_data, processing_tickers)
            self.feature_store.push(FeatureGroup.PRICES, new_data)

        logger.debug('Finished processing all tickers')
