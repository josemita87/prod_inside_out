from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Literal, Optional


class Config(BaseSettings):
    
    # Kafka Settings
    kafka_broker_address: str = Field(..., env='KAFKA_BROKER_ADDRESS') 
    kafka_output_topic: str = Field(..., env='KAFKA_OUTPUT_TOPIC')

    # Time Settings
    years: int = Field(None, env='YEARS') 
    mode: Literal['historical', 'live', 'last_quarter'] = Field('historical', env='MODE')
    
    # Buffer Settings
    buffer_size: int = Field(1000, env='BUFFER_SIZE')
    form_type: str = Field(None, env='FORM_TYPE') 

    #Live Settings
    num_pages: int = Field(..., env='NUM_PAGES')
    live_iterations: int = Field(..., env='LIVE_ITERATIONS')
    secs_between_iterations: int = Field(..., env='SECS_BETWEEN_ITERATIONS')
    
    @field_validator('form_type')
    def validate_form_type(cls, v):
        if v not in ['4', '13F-HR']:
            raise ValueError('form_type must be either 4 or 13F-HR')
        return v
    
config = Config()


# Dev settings
kafka_broker_address: str = 'localhost:19092'
kafka_output_topic: str = 'form_4_dictionary'
years: Optional[int] = 5 
form_type: Optional[str] = '4'