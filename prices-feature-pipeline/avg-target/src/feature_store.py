import hopsworks
import pandas as pd
from loguru import logger
import time
from hsfs.feature import Feature
import numpy as np

class Connection:  
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
    
    
    def fetch_4f_transactions(
        self,
        feature_group_name: hopsworks,
        feature_group_version: int,
        filters: list[dict] = None
        ) -> pd.DataFrame:
        
        fg = self.fs.get_or_create_feature_group(
            name=feature_group_name,
            version=feature_group_version,
            primary_key='key',
            event_time='date'
        )
       
        # Apply filters
        if filters:        
            for filter_dict in filters:
                for key, value in filter_dict.items():
                    fg = fg.filter(Feature(key) == value)

        # Read and return data from the feature store
        data: pd.DataFrame = fg.read(read_options={"use_hive": True})
        return data.to_dict('records')
        
    
    def push_data(
        self,
        data: pd.DataFrame,
        fg_name:str,
        fg_version:int,
  
    ) -> None:
        
        fg = self.fs.get_or_create_feature_group(
            name=fg_name,
            version=fg_version,
            primary_key=['key'],
            event_time='date',
            online_enabled=False,
            start_offline_materialization=True,
            description='Feature group containing returns data for insider transactions given specific filters'
        )


        if not data.empty: 
            
            logger.debug(data.head())
            fg.insert(
                data, write_options = {
                    'start_offline_materialization':True,
                    'mode':'append' 
                }
            )

            logger.debug(f"Data pushed to feature store")
            time.sleep(30)


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

    logger.debug(f"Data cleaned with shape: {data.shape}")

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
        'avg_change': 'float32'
    }
    
    for col, dtype in numeric_columns.items():
        data[col] = pd.to_numeric(data[col], errors='coerce').astype(dtype)
        data = data.dropna(subset=[col])  # Drop rows where conversion failed

    # Convert 'date' to datetime
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    data = data.dropna(subset=['date'])  # Drop rows where 'date' conversion failed

    return data