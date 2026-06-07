"""Pydantic settings for the Yahoo Connect microservice."""

import pandas as pd
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration settings for the Yahoo Connect microservice."""

    # Hopsworks Settings
    project_name: str = Field(..., json_schema_extra={'env': 'PROJECT_NAME'})
    feature_group_version: int = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_VERSION'})
    feature_view_version: int = Field(..., json_schema_extra={'env': 'FEATURE_VIEW_VERSION'})
    feature_view_name: str = Field(..., json_schema_extra={'env': 'FEATURE_VIEW_NAME'})
    event_time: str = Field(..., json_schema_extra={'env': 'EVENT_TIME'})
    hopsworks_api_key: str = Field(..., json_schema_extra={'env': 'HOPSWORKS_API_KEY'})
    inference_blueprint: dict = Field(
        {
            'date': pd.to_datetime(['1999-01-01']),
            'close': [-1.0],
            'ticker': ['INFERENCE_VALUE'],
        }
    )

    # System Settings
    buffer_size: int = Field(..., json_schema_extra={'env': 'BUFFER_SIZE'})
    delay: int = Field(0, json_schema_extra={'env': 'DELAY'})
    system_training: bool = Field(False, json_schema_extra={'env': 'SYSTEM_TRAINING'})
    system_inference: bool = Field(False, json_schema_extra={'env': 'SYSTEM_INFERENCE'})
    filter_key: str = Field(..., json_schema_extra={'env': 'FILTER_KEY'})
    acquired_disposed: str = Field(..., json_schema_extra={'env': 'ACQUIRED_DISPOSED'})

    # CSV Headers
    headers: list = Field(
        default=[
            'company_cik',
            'ticker',
            'insider_cik',
            'insider_name',
            'owner_code',
            'rule105b1',
            'derivative',
            'link',
            'shares',
            'acquired_disposed',
            'price',
            'date',
            'remaining_shares',
            'ownership',
            'coding',
            'direct_holding',
            'indirect_holding',
            'equity_swap',
            'timestamp',
            'key',
        ],
        json_schema_extra={'env': 'CSV_HEADERS'},
    )
    prices_headers: list = Field(default=['date', 'close', 'ticker'], json_schema_extra={'env': 'PRICES_HEADERS'})


# Instantiate the configuration
config = Config()
