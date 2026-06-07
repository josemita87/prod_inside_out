"""Environment-driven configuration settings for the api-enricher service."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application settings loaded from environment variables for api-enricher."""

    # Kafka settings
    kafka_broker_address: str = Field(..., env='KAFKA_BROKER_ADDRESS')
    kafka_input_topic: str = Field(..., env='KAFKA_INPUT_TOPIC')
    kafka_output_topic: str = Field(..., env='KAFKA_OUTPUT_TOPIC')
    auto_offset_reset: str = Field(..., env='AUTO_OFFSET_RESET')
    consumer_group: str = Field(..., env='CONSUMER_GROUP')

    poll_timeout: int = Field(..., env='POLL_TIMEOUT')
    buffer_size: int = Field(..., env='BUFFER_SIZE')

    # Api  Paths
    mcaps_path: str = Field(..., env='MCAPS_PATH')
    mapper_path: str = Field(..., env='MAPPER_PATH')

    # Failed paths
    failed_mcaps_path: str = Field(..., env='FAILED_MCAPS_PATH')
    failed_date_path: str = Field(..., env='FAILED_DATE_PATH')
    failed_sic_path: str = Field(..., env='FAILED_SIC_PATH')
    failed_exchange_path: str = Field(..., env='FAILED_EXCHANGE_PATH')

    # Docker Compose settings
    delay: int = Field(..., env='DELAY')
    sleep_time: float = Field(..., env='SLEEP_TIME')


config = Config()
