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
def reduce_mem_storage(data: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce the memory usage of the DataFrame by downcasting the numeric columns.
    """
    try:
        # Convert columns to categorical type
        categorical_columns = ['company_cik', 'ticker', 'insider_cik', 'insider_name', 'owner_code', 
        'acquired_disposed', 'ownership', 'coding', 'direct_holding', 'indirect_holding','exchange', 'sic']
        for col in categorical_columns:
            data[col] = data[col].astype('category')

        # Convert booleans to actual boolean dtype
        data['rule105b1'] = data['rule105b1'].astype('bool')
        data['derivative'] = data['derivative'].astype('bool')

       # Ensure numerical columns are correctly typed
        numerical_columns = ['shares', 'price', 'remaining_shares', 'market_cap', 'pct_change', 'avg_return']
        for col in numerical_columns:
            # Convert to numeric (coerce invalid entries to NaN)
            data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # Check if the column has only integer-compatible values
            if data[col].dropna().mod(1).eq(0).all():
                # Convert to int32 if all values are integers
                data[col] = data[col].fillna(0).astype('int32')
            else:
                # Otherwise, convert to float32
                data[col] = data[col].astype('float32')

        # Convert 'date' to datetime
        data['date'] = pd.to_datetime(data['date'])
    
        return data
    
    except Exception as e:
        logger.error(e)
        return data