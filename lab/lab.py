import hopsworks
import pandas as pd
import time
from hsfs.feature import Feature
import numpy as np




class Connection:
    """Class to manage the connection to Hopsworks and feature groups."""
    
    def __init__(self) -> None:
        """Initialize connection to Hopsworks and feature groups."""
        self.project = hopsworks.login(
            project="ml_system_c1"
            api_key_value=config.hopsworks_api_key,
        )
        self.fs = self.project.get_feature_store()

       
        self.fg_returns = self.fs.get_or_create_feature_group(
            name=config.feature_group_target,
            online_enabled=False,
            stream=False,
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )
        self.fg_inference = self.fs.get_or_create_feature_group(
            name="form4_inference_v1",
            online_enabled=False,
            stream=False,
            version=1,
            primary_key=['key'],
            event_time='date'
        )
    
    def push_returns_data(self, data: pd.DataFrame):
        """Push returns data to the feature group."""
        if not data.empty:
            self.fg_returns.insert(
                features=data, 
                write_options={
                    'start_offline_materialization': True,
                    'mode': 'append'
                }
            )

    def push_inference_data(self, data: pd.DataFrame):
        """Push inference data to the feature group."""
        if not data.empty:
            self.fg_inference.insert(
                features=data, 
                write_options={
                    'start_offline_materialization': True,
                    'mode': 'append'
                }
            )

