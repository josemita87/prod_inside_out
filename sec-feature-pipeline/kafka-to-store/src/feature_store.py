
import hopsworks
import pandas as pd
from typing import Tuple
from loguru import logger
import time



class Connection:  

    INFERENCE_BLUEPRINT = {
        "ticker": ["INFERENCE_VALUE"],
        "price": [-1.0],
        "date": pd.to_datetime(["1999-01-01"])
    }

    def __init__(self, project_name, api_key):
        self.project_name = project_name
        self.api_key = api_key
        self.project = hopsworks.login(
            project=self.project_name,
            api_key_value=self.api_key,
        )
        self.fs = self.project.get_feature_store()
    

    def connect_feature_group(
            self, 
            feature_group_name, 
            feature_group_version, 
            primary_key, 
            event_time
        ) -> hopsworks:

        #Get feature group object
        prices_fg = self.fs.get_or_create_feature_group(
            name=feature_group_name,
            version=feature_group_version,
            primary_key=primary_key,
            event_time=event_time
        )
        #Initialize data for inference (if fg doesn't exist)
        prices_fg.insert(pd.DataFrame(self.INFERENCE_BLUEPRINT))

        return prices_fg
    

    def push_data(
            self, 
            data: pd.DataFrame,
            feature_group: any,
            
        ) -> None:

        feature_group.insert(
            data = data
        )

        logger.debug(f"Data pushed to feature store")
        time.sleep(30)
