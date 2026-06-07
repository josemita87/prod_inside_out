"""Environment-driven configuration for the master-index microservice."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Settings for the master-index service loaded from environment variables."""

    # Kafka Settings
    kafka_broker_address: str = Field(..., env='KAFKA_BROKER_ADDRESS')
    kafka_output_topic: str = Field(..., env='KAFKA_OUTPUT_TOPIC')

    # System Settings
    buffer_size: int = Field(..., env='BUFFER_SIZE')
    mode: Literal['historical', 'live', 'last_quarter'] = Field(..., env='MODE')

    # Training Settings
    years: int = Field(5, env='YEARS')

    # Inference Settings
    num_pages: int = Field(1, env='NUM_PAGES')
    live_iterations: int = Field(1, env='LIVE_ITERATIONS')
    secs_between_iterations: int = Field(10, env='SECS_BETWEEN_ITERATIONS')


config = Config()
