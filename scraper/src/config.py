from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Literal, Optional


class Config(BaseSettings):
    
    # Dev settings
    kafka_broker_address: str = 'localhost:19092'
    kafka_input_topic: str = 'master-form-4'
    kafka_output_topic: str = 'form_4_dictionary'

    years: Optional[int] = 5 
    form_type: Optional[str] = '4'
    
    
    
config = Config()





kafka_broker_address: str = Field(..., env='KAFKA_BROKER_ADDRESS')
kafka_input_topic: str = Field(..., env='KAFKA_INPUT_TOPIC') 
kafka_output_topic: str = Field(..., env='KAFKA_OUTPUT_TOPIC')