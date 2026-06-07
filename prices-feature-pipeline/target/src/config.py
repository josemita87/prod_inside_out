"""Pydantic settings for the target microservice."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration settings for the target microservice."""

    # Hopsworks settings
    project_name: str = Field(..., json_schema_extra={'env': 'PROJECT_NAME'})
    hopsworks_api_key: str = Field(..., json_schema_extra={'env': 'HOPSWORKS_API_KEY'})
    feature_group_version: int = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_VERSION'})
    event_time: str = Field(..., json_schema_extra={'env': 'EVENT_TIME'})

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

    # Investment settings
    delta_period: int = Field(..., json_schema_extra={'env': 'DELTA_PERIOD'})
    filter_key: str = Field(..., json_schema_extra={'env': 'FILTER_KEY'})
    acquired_disposed: str = Field(..., json_schema_extra={'env': 'ACQUIRED_DISPOSED'})

    # Aggregation settings
    agg_dict: dict = Field(
        {
            'company_cik': 'first',
            'key': 'first',
            'timestamp': 'first',
            'date': 'first',
            'market_cap': 'first',
            'shares': 'sum',
            'remaining_shares': 'sum',
            'direct_holding': 'sum',
            'indirect_holding': 'sum',
            'equity_swap': 'any',
            'rule105b1': 'any',
            'derivative': lambda x: x.mode()[0],
            'owner_code': lambda x: x.mode()[0],
            'ownership': lambda x: x.mode()[0],
            'coding': lambda x: x.mode()[0],
            'price': 'mean',
        }
    )

    # System settings
    system_training: bool = Field(False, json_schema_extra={'env': 'SYSTEM_TRAINING'})
    system_inference: bool = Field(False, json_schema_extra={'env': 'SYSTEM_INFERENCE'})
    delay: int = Field(0, json_schema_extra={'env': 'DELAY'})

    class Config:
        """Pydantic configuration controlling environment loading."""

        env_file = '.env'
        env_file_encoding = 'utf-8'


# Instantiate the configuration
config = Config()
