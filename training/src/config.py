from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import pandas as pd

# Load the main .env file and then the credentials.env file
load_dotenv(".env")
load_dotenv(".credentials.env")

class Config(BaseSettings):
    # Hopsworks settings
    project_name: str = Field(..., json_schema_extra={'env': 'PROJECT_NAME'})
    feature_group_training: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_TRAINING'})
    feature_group_version: int = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_VERSION'})
    api_key: str = Field(..., json_schema_extra={'env': 'API_KEY'})
    
    # Paths
    models_directory: str = Field(..., json_schema_extra={'env': 'MODELS_DIRECTORY'})
    data_source_path: str = Field(..., json_schema_extra={'env': 'DATA_SOURCE_PATH'})
    plot_path: str = Field(..., json_schema_extra={'env': 'PLOT_PATH'})
    log_path: str = Field(..., json_schema_extra={'env': 'LOG_PATH'})

    # Training settings
    max_runtime_secs: int = Field(..., json_schema_extra={'env': 'MAX_RUNTIME_SECS'})
    class Config:
        # Specify only the main .env file here for Pydantic’s internal use
        env_file = ".env"
        env_file_encoding = "utf-8"

config = Config()
