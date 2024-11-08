from config import config
import hopsworks
import pandas as pd
from typing import Tuple
from loguru import logger
import time

def connect_feature_group(tickers_to_process: list[str]) -> Tuple:
    
    project = hopsworks.login(
        project=config.project_name,
        api_key_value=config.api_key,
    )
    
    fs = project.get_feature_store()
    
    prices_fg = fs.get_or_create_feature_group(
        name=config.feature_group_name,
        version=config.feature_group_version,
        primary_key=['ticker', 'date'],
        event_time='date'
    )

    #Initialize data for inference
    """data = {
            "ticker": ["INFERENCE_VALUE"],
            "price": [-1.0],
            "date": pd.to_datetime(["1999-01-01"])
    }
    df = pd.DataFrame(data)
    prices_fg.insert(df)
    """
    try:
        prices_fv = fs.get_or_create_feature_view(
            name=config.feature_view_name,
            version=config.feature_view_version,
            query=prices_fg.filter(prices_fg.ticker.isin(tickers_to_process))
        )

    except:
        logger.debug("Unable to access feature view")
        prices_fv = None
   
    return prices_fg, prices_fv


def push_data_to_feature_store(data: pd.DataFrame) -> None:
    prices_fg, _ = connect_feature_group()
    
    prices_fg.insert(
        data, write_options = {
            'start_offline_materialization':False,
            'mode':'append' 
        }
    )

    logger.debug(f"Data pushed to feature store")
    time.sleep(30)