from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic.class_validators import root_validator

from dotenv import load_dotenv  

load_dotenv(".env")
load_dotenv(".credentials.env")

class Config(BaseSettings):

    project_name: str = Field(..., json_schema_extra={'env': 'PROJECT_NAME'})
    api_key: str = Field(..., json_schema_extra={'env': 'API_KEY'})

    # Feature group names
    feature_group_target: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_TARGET'})
    feature_group_avg: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_AVG'})
    feature_group_offset_avg: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_OFFSET_AVG'})
    feature_group_version: int = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_VERSION'})

    #Other parameters
    delta_period: int = Field(..., json_schema_extra={'env': 'DELTA_PERIOD'})
    event_time: str = Field(..., json_schema_extra={'env': 'EVENT_TIME'})
    offset_buffer_size: int = Field(..., json_schema_extra={'env': 'OFFSET_BUFFER_SIZE'})
    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate the configuration
config = Config()
