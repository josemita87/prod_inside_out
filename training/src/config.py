from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import pandas as pd

# Load the main .env file and then the credentials.env file
load_dotenv(".env")
load_dotenv(".credentials.env")

class Config(BaseSettings):
    project_name: str = Field(..., json_schema_extra={'env': 'PROJECT_NAME'})
    feature_group_training: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_TRAINING'})
    feature_group_version: int = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_VERSION'})
    api_key: str = Field(..., json_schema_extra={'env': 'API_KEY'})
    
    class Config:
        # Specify only the main .env file here for Pydantic’s internal use
        env_file = ".env"
        env_file_encoding = "utf-8"

config = Config()
