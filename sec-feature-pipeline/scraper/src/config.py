"""Environment-driven configuration for the scraper microservice."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Settings for the scraper service loaded from environment variables."""

    # Kafka settings
    kafka_broker_address: str = Field(..., env='KAFKA_BROKER_ADDRESS')
    kafka_input_topic: str = Field(..., env='KAFKA_INPUT_TOPIC')
    kafka_output_topic: str = Field(..., env='KAFKA_OUTPUT_TOPIC')
    auto_offset_reset: str = Field(..., env='AUTO_OFFSET_RESET')
    consumer_group: str = Field(..., env='CONSUMER_GROUP')

    # System Settings
    buffer_size: int = Field(..., env='BUFFER_SIZE')
    sleep_time: float = Field(..., env='SLEEP_TIME')
    poll_timeout: int = Field(..., env='POLL_TIMEOUT')
    delay: int = Field(..., env='DELAY')
    mode: Literal['historical', 'live', 'last_quarter'] = Field(..., env='MODE')

    # Training Settings
    test_size: int = Field(400, env='TEST_SIZE')
    test_trial: str = Field('False', env='TEST_TRIAL')

    # Inference Settings
    days_back: int = Field(1, env='DAYS_BACK')


config = Config()
