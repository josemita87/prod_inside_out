import hopsworks
import pandas as pd
from loguru import logger
import time
from hsfs.feature import Feature
import numpy as np
from config import config

class Connection:
    """Class to manage the connection to Hopsworks and feature groups."""
    
    WRITE_OPTIONS = {
        'start_offline_materialization': True,
        'mode': 'append'
    }

    def __init__(self) -> None:
        self.project = hopsworks.login(
            project=config.project_name,
            api_key_value=config.hopsworks_api_key,
        )
        self.fs = self.project.get_feature_store()

        self.P = self.fs.get_or_create_feature_group(
            name="p",
            online_enabled=False,
            stream=False,
            version=config.feature_group_version,
            primary_key=['ticker', 'date'],
            event_time='date'
        )
        self.BT4 = self.fs.get_or_create_feature_group(
            name="bt4",  
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )

        self.materialization_counter = 0
        self.job = None

        self.RT4 = self.fs.get_or_create_feature_group(
            name="rt4",
            online_enabled=False,
            stream=False,
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )
        self.BI4 = self.fs.get_or_create_feature_group(
            name="bi4",
            online_enabled=False,
            stream=False,
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )   
        self.BIR4 = self.fs.get_or_create_feature_group(
            name="bir4",
            online_enabled=False,
            stream=False,
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )
       
    def fetch_P(self, tickers):
        """Fetch price data for the given tickers."""
        P = self.P
        try:
            P=P.filter(P['ticker'].isin(tickers))
        except Exception as e:
            return pd.DataFrame()
        
        return P.read(read_options={"use_hive": True})
    
    def push_P(self, data):
        
        if not data.empty:
            self.P.insert(
                features=data, 
                write_options=self.WRITE_OPTIONS
            )
    
    def fetch_BT4(self, key, value):
        BT4 = self.BT4
        if key and value:
            BT4 = BT4.filter(
                BT4[key] == value
            )
        return BT4.read(read_options={"use_hive": True})
    
    def push_BT4(self, data):
        if not data.empty:
            self.BT4.insert(
                features=data, 
                write_options=self.WRITE_OPTIONS
            )

    def fetch_RT4(self):
        return self.RT4.read(read_options={"use_hive": True})
    
    def push_RT4(self, data):
        if not data.empty:
            self.RT4.insert(
                features=data, 
                write_options=self.WRITE_OPTIONS
            )

    def fetch_BI4(self):
        return self.BI4.read(read_options={"use_hive": True})
    
    def push_BI4(self, data):
        if not data.empty:
            self.BI4.insert(
                features=data, 
                write_options=self.WRITE_OPTIONS
            )
    def fetch_BIR4(self):
        return self.BIR4.read(read_options={"use_hive": True})
    
    def push_BIR4(self, data):
        if not data.empty:
            self.BIR4.insert(
                features=data, 
                write_options=self.WRITE_OPTIONS
            )
