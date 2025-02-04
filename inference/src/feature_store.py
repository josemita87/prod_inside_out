import hopsworks
import pandas as pd
from typing import Tuple, Any
from loguru import logger
from config import config
import time

class FeatureStoreConnection:  
    def __init__(self):
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
            event_time='trade_date'
        )

    def fetch_new_trades(self) -> pd.DataFrame:
        """
        Fetch new trades from the feature group.
        """
        try:
            query = self.fg_trades.select_all()
            new_trades = query.read()

            # Clean the trade data
            new_trades = self.clean_trade_data(new_trades)
            return new_trades
        
        except Exception as e:
            logger.error(f"Failed to fetch new trades: {e}")
            return pd.DataFrame()

    def clean_trade_data(self, data: list[dict]) -> pd.DataFrame:
        """
        Clean the trade data by replacing 'None' and '---' with NaN, 
        dropping duplicates and removing rows with NaN values.
        """
        # Convert the list of dicts to a DataFrame
        data = pd.DataFrame(data)

        # Drop duplicate rows
        data = data.drop_duplicates()

        # Drop rows with NaN values in any column
        data = data.dropna()

        return data


