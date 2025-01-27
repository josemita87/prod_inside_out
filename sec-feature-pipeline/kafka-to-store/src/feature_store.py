import hopsworks
import pandas as pd
from typing import Tuple, Any
from loguru import logger
from config import config
import time

class Connection:  

    def __init__(self):
        
        # Initialize Feature Store Object
        project = hopsworks.login(
            project=config.project_name,
            api_key_value=config.hopsworks_api_key,
        )
        self.fs = project.get_feature_store()
    
        # Initialize feature group connections
        self.fg_form4 = self.fs.get_or_create_feature_group(
            name=config.feature_group_form_4_basic,
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )
        
        # Initialize the job and materialization counter
        self.job = None
        self.materialization_counter = 0
    
    def _validate_dataframe_types(self, data: pd.DataFrame, expected_schema: dict) -> pd.DataFrame:
        """
        Validate and coerce the data types of the DataFrame to match the expected schema.
        """
        # In next weeks , will develop type validation and coercion in this method
        return data

    def push_data(self, data: pd.DataFrame, schema: dict) -> None:

        # Increment the materialization counter
        self.materialization_counter += 1
        # Validate and coerce the DataFrame
        data = self._validate_dataframe_types(data, schema)
       
        # Insert the data into the feature group
        try:
            self.job, _ = self.fg_form4.insert(
                data, 
                write_options = {'start_offline_materialization': False}
            )
            logger.debug(f"Data pushed to feature store successfully.")

        except Exception as e:
            logger.error(f"Failed to push data to feature store: {e}")
            logger.debug(f"Data: {data}")
            self.job=None

        if self.job and self.materialization_counter >= config.materialization_batch_size:
            self.job.run()
            self.materialization_counter = 0

    def last_materialization(self):
        if self.job:
            self.job.run()


def data_cleaning(data: list[dict]) -> pd.DataFrame:
    """
    Clean the data by replacing 'None' and '---' with NaN, 
    dropping duplicates and removing rows with NaN values.
    """

    #Drop specific columns from the dataframe
    #if config.api_drop:
       # data.drop([config.api_drop], axis=1, inplace = True)

    # Convert the list of dicts to a DataFrame
    data = pd.DataFrame(data)

    # Drop duplicate rows
    data = data.drop_duplicates()

    # Drop rows with NaN values in any column
    data = data.dropna()

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
        if col in data.columns:
            data[col] = data[col].astype('category')

    # Convert booleans to actual boolean dtype
    for col in ['rule105b1', 'derivative', 'equity_swap', 'ownership']:
        if col in data.columns:
            data[col] = data[col].astype('bool')
   
    # Convert numeric columns to more memory-efficient types
    numeric_columns = {
        'shares': 'int32',
        'price': 'float64',
        'remaining_shares': 'int32',
        'direct_holding': 'int64',
        'indirect_holding': 'int64',
        'market_cap': 'int64',
        'timestamp': 'int64',
    }
    for col, dtype in numeric_columns.items():
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce').astype(dtype)
            data = data.dropna(subset=[col])  # Drop rows where conversion failed

    # Convert 'date' to datetime
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    data = data.dropna(subset=['date'])  # Drop rows where 'date' conversion failed

    return data


