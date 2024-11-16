from src.config import config
import hopsworks
import pandas as pd
from typing import Tuple
from loguru import logger
import time


class Connection:  

    INFERENCE_BLUEPRINT = {
        "ticker": ["INFERENCE_VALUE"],
        "close": [-1.0],
        "date": pd.to_datetime(["1999-01-01"])
    }

    def __init__(
            self, 
            project_name, 
            api_key
        )-> None:

        #Initialize connection to Hopsworks
        self.project_name = project_name
        self.api_key = api_key
        self.project = hopsworks.login(
            project=self.project_name,
            api_key_value=self.api_key,
        )
        self.fs = self.project.get_feature_store()
    
    

    def fetch_ticker_data(
        self,
        feature_group_name: hopsworks,
        feature_group_version: int,
        ) -> pd.DataFrame:
        
        fg = self.fs.get_or_create_feature_group(
            name=feature_group_name,
            version=feature_group_version,
            primary_key='key',
            event_time='date'
        )
       
        data: pd.DataFrame = fg.read()
        tickers = data['ticker'].unique()
        logger.debug(f"Data fetched from feature store")

        return tickers
    

    def fetch_price_data(
        self,
        tickers_to_process: list,
        feature_group_name: hopsworks,
        feature_group_version: int,
        feature_view_name: str = None,
        feature_view_version: int = 1,
        ) -> pd.DataFrame:
        
        fg = self.fs.get_or_create_feature_group(
            name=feature_group_name,
            version=feature_group_version,
            primary_key=['ticker', 'date'],
            event_time='date'
        )

        #Insert dummy data infer schema
        fg.insert(pd.DataFrame(self.INFERENCE_BLUEPRINT))
        try:
            prices_fv = self.fs.get_or_create_feature_view(
                name=feature_view_name,
                version=feature_view_version,
                query=fg.filter(
                    fg.ticker.isin(tickers_to_process)
                )
            )

        except:  
            prices_fv = None
    

        if prices_fv:
            logger.debug(f"Data fetched from feature store")
            return prices_fv.get_batch_data()
        
        else:
            logger.debug('Could not find data in feature store')
            return pd.DataFrame()
        

    def push_data(
            self,
            data: pd.DataFrame,
            feature_group_name: str,
            feature_group_version: int

        ) -> None:
        
        fg = self.fs.get_or_create_feature_group(
            name=feature_group_name,
            version=config.feature_group_version,
            primary_key=['ticker', 'date'],
            event_time='date'
        )
        data.reset_index(inplace=True, drop=True)
        data.drop(columns=['index'], inplace=True)
 
        fg.insert(
            data, write_options = {
                'start_offline_materialization':False,
                'mode':'append' 
            }
        )

        logger.debug(f"Data pushed to feature store")
        time.sleep(30)