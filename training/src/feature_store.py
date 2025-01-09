import hopsworks
import pandas as pd
from loguru import logger
import time
from hsfs.feature import Feature
import numpy as np
from config import config

class Connection:  
    def __init__(self)-> None:

        #Initialize connection to Hopsworks
        self.project = hopsworks.login(
            project=config.project_name,
            api_key_value=config.api_key,
        )
        self.fs = self.project.get_feature_store()

        # Initialize feature group connections
        self.fg = self.fs.get_or_create_feature_group(
            name=config.feature_group_training,  
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )
        
    
    def fetch_training_data(self) -> pd.DataFrame:
           
        return self.fg.read(read_options={"use_hive": True})
        



    

