from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic.class_validators import root_validator

from dotenv import load_dotenv  

load_dotenv(".env")
load_dotenv(".credentials.env")

class Config(BaseSettings):
    project_name: str = Field(..., json_schema_extra={'env': 'PROJECT_NAME'})
    feature_group_prices: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_PRICES'})
    feature_group_form4: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_FORM4'})
    feature_group_version: int = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_VERSION'})
    event_time: str = Field(..., json_schema_extra={'env': 'EVENT_TIME'})
    api_key: str = Field(..., json_schema_extra={'env': 'API_KEY'})
    #prices_filters: list[dict] = Field([{'acquired_disposed': 'D'}])
    fourf_filters: list[dict] = Field([{'acquired_disposed': 'D'}])
    npartitions: int = Field(1, json_schema_extra={'env': 'NPARTITIONS'})
    delta_period: int = Field(30, json_schema_extra={'env': 'DELTA_PERIOD'})
    feature_group_returns: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_RETURNS'})
    feature_group_delta: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_DELTA'})
    delta_buffer_size: int = Field(10, json_schema_extra={'env': 'DELTA_BUFFER_SIZE'})

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate the configuration
config = Config()
