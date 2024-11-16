
import hopsworks
import pandas as pd
from typing import Tuple, Any
from loguru import logger
import time
from datetime import datetime


class Connection:  

    INFERENCE_BLUEPRINT = {
    "key": "000000000",  # Dummy key
    "company_cik": "0000000000",  # Dummy CIK
    "ticker": "DUM",
    "insider_cik": "0000000001",  # Dummy insider CIK
    "insider_name": "DOE JOHN",
    "owner_code": "9999",
    "rule105b1": "False",
    "derivative": "False",
    "link": "https://www.example.com/test-dummy-data",
    "shares": "1",
    "acquired_disposed": "D",
    "price": "1.01",
    "date": datetime.strptime("2000-01-01",'%Y-%m-%d'),  # Use a fictional date
    "remaining_shares": "1",
    "ownership": "D",
    "coding": "T",
    "direct_holding": "1",
    "indirect_holding": "0",
    "market_cap": "1.0",
    "exchange": "DUMMY",
    "sic": "0000"
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
        fg = self.fs.get_or_create_feature_group(
            name=feature_group_name,
            version=feature_group_version,
            primary_key=[primary_key],
            event_time=event_time
        )
        
        #Initialize data for inference (if fg doesn't exist)
        fg.insert(pd.DataFrame([self.INFERENCE_BLUEPRINT]))

        return fg
    

    def _validate_dataframe_types(self, data: pd.DataFrame, expected_schema: dict) -> pd.DataFrame:
        """
        Validate and coerce the data types of the DataFrame to match the expected schema.
        """
        # In next weeks , will develop type validation and coercion in this method
        return data


    def push_data(
            self,
            data: pd.DataFrame,
            feature_group: Any, 
            expected_schema:dict
        ) -> None:

        # Validate and coerce the DataFrame
        data = self._validate_dataframe_types(data, expected_schema)
        
        # Insert the data into the feature group
        try:
            feature_group.insert(data)
            logger.debug(f"Data pushed to feature store successfully.")

        except Exception as e:
            logger.error(f"Failed to push data to feature store: {e}")
            raise
        
