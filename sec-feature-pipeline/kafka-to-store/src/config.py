from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Literal, Optional
from dotenv import load_dotenv, find_dotenv



class Config(BaseSettings):
    
    # Kafka settings
    kafka_broker_address: str = Field(..., env='KAFKA_BROKER_ADDRESS')
    kafka_input_topic: str = Field(..., env='KAFKA_INPUT_TOPIC') 
    buffer_size: int = Field(..., env='BUFFER_SIZE')

    #Hopsworks settings
    project_name: str = Field(..., env='PROJECT_NAME')
    api_key: str = Field(..., env='API_KEY')
    feature_group_name: str = Field(..., env='FEATURE_GROUP_NAME')
    feature_group_version: int = Field(..., env='FEATURE_GROUP_VERSION')
    primary_key: str = Field(..., env='PRIMARY_KEY')
    event_time: str = Field(..., env='EVENT_TIME')
    

    

config = Config()
