"""Hopsworks feature store connection for fetching and cleaning trade data."""

import logging

import hopsworks
import pandas as pd
from config import config

logger = logging.getLogger(__name__)


class FeatureStoreConnection:
    """Connection to the Hopsworks feature store and trades feature group.

    Attributes:
        fs: The Hopsworks feature store handle.
        fg_trades: The trades feature group.
    """

    def __init__(self):
        """Log in to Hopsworks and open the trades feature group."""
        # Initialize Feature Store Object
        project = hopsworks.login(
            project=config.project_name,
            api_key_value=config.hopsworks_api_key,
        )
        self.fs = project.get_feature_store()

        # Initialize feature group connections
        self.fg_trades = self.fs.get_or_create_feature_group(
            name=config.feature_group_trades,
            version=config.feature_group_version,
            primary_key=['trade_id'],
            event_time='trade_date',
        )

    def fetch_new_trades(self) -> pd.DataFrame:
        """Fetch and clean new trades from the trades feature group.

        Returns:
            A cleaned DataFrame of trades, or an empty DataFrame on failure.
        """
        try:
            query = self.fg_trades.select_all()
            new_trades = query.read()

            # Clean the trade data
            new_trades = self.clean_trade_data(new_trades)
            return new_trades

        except Exception as e:
            logger.error(f'Failed to fetch new trades: {e}')
            return pd.DataFrame()

    def clean_trade_data(self, data: list[dict]) -> pd.DataFrame:
        """Clean trade data by dropping duplicate rows and rows with NaN values.

        Args:
            data: Raw trade records to clean.

        Returns:
            A DataFrame with duplicates and NaN-containing rows removed.
        """
        # Convert the list of dicts to a DataFrame
        data = pd.DataFrame(data)

        # Drop duplicate rows
        data = data.drop_duplicates()

        # Drop rows with NaN values in any column
        data = data.dropna()

        return data
