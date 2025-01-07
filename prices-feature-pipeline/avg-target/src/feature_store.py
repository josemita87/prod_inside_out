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
        self.fg_f4_target = self.fs.get_or_create_feature_group(
            name=config.feature_group_target,
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )
        self.fg_f4_avg = self.fs.get_or_create_feature_group(
            name=config.feature_group_avg,
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )
        self.fg_offset_avg = self.fs.get_or_create_feature_group(
            name=config.feature_group_offset_avg,
            version=config.feature_group_version,
            primary_key=['ticker'],
            event_time='date'
        )

    
    def fetch_4f_transactions(self) -> pd.DataFrame:
        # Read and return data from the feature store
        return self.fg_f4_target.read(read_options={"use_hive": True})
    

    def push_returns_data(self, data: pd.DataFrame) -> None:
        
        if not data.empty: 
         
            self.fg_f4_avg.insert(
                data, 
                write_options = {
                    'start_offline_materialization':True,
                    'mode':'append' 
                }
            )
           
        
   
#Auxiliary function
def data_cleaning(data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the data by replacing 'None' and '---' with NaN, 
    dropping duplicates and removing rows with NaN values.
    """

    # Replace 'None' and '---' with NaN
    data.replace(['None', '---'], np.nan, inplace=True)
    
    # Drop duplicate rows
    data.drop_duplicates(inplace=True)
    
    # Drop rows with NaN values (optional)
    data.dropna(inplace=True)

    

    return data


#Auxiliary function
def validate_and_reduce_mem_storage(data: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce the memory usage of the DataFrame by downcasting the numeric columns.
    Invalid rows for each conversion will be dropped.
    """
    data['link'] = data['link'].astype('str')

    # Convert columns to categorical where appropriate
    for col in ['company_cik', 'ticker', 'insider_cik', 'insider_name', 
                'owner_code', 'exchange', 'acquired_disposed', 'coding', 'sic']:
        data[col] = data[col].astype('category')

    # Convert booleans to actual boolean dtype
    for col in ['rule105b1', 'derivative', 'equity_swap', 'ownership']:
        data[col] = data[col].astype('bool')

    # Convert numeric columns to more memory-efficient types
    numeric_columns = {
        'shares': 'int32',
        'price': 'float32',
        'remaining_shares': 'int32',
        'direct_holding': 'int32',
        'indirect_holding': 'int32',
        'market_cap': 'int64',
        'timestamp': 'int64',
        'pct_change': 'float32',
        'avg_return': 'float32'
    }
    
    for col, dtype in numeric_columns.items():
        data[col] = pd.to_numeric(data[col], errors='coerce').astype(dtype)
        data = data.dropna(subset=[col])  # Drop rows where conversion failed

    # Convert 'date' to datetime
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    data = data.dropna(subset=['date'])  # Drop rows where 'date' conversion failed

    return data