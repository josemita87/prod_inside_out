from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Literal, Optional, ClassVar, Dict
from dotenv import load_dotenv, find_dotenv
from datetime import datetime



class Config(BaseSettings):
    
    # Kafka settings
    kafka_broker_address: str = Field(..., env='KAFKA_BROKER_ADDRESS')
    kafka_input_topic: str = Field(..., env='KAFKA_INPUT_TOPIC') 
    buffer_size: int = Field(1000, env='BUFFER_SIZE')  # Default buffer size is 1000

    # Hopsworks settings
    project_name: str = Field(..., env='PROJECT_NAME')
    api_key: str = Field(..., env='API_KEY')
    feature_group_name: str = Field(..., env='FEATURE_GROUP_NAME')
    feature_group_version: int = Field(1, env='FEATURE_GROUP_VERSION')  # Default version is 1

    # Expected schema as a class-level constant
    expected_schema: ClassVar[Dict[str, type]] = {
        "key": str,
        "company_cik": str,
        "ticker": str,
        "insider_cik": str,
        "insider_name": str,
        "owner_code": str,
        "rule105b1": str,
        "derivative": str,
        "link": str,
        "shares": str,
        "acquired_disposed": str,
        "price": str,
        "date": datetime,
        "remaining_shares": str,
        "ownership": str,
        "coding": str,
        "direct_holding": str,
        "indirect_holding": str,
        "market_cap": str,
        "exchange": str,
        "sic": str,
    }
    
    class Config:
        env_file = ".env"  # Specify the .env file for local development

config = Config()