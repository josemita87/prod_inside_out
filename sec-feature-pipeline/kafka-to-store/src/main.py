"""Entry point that consumes Kafka transactions and pushes them to the feature store."""

import logging

import pandas as pd
from config import config

from src import clean, kafka_topic
from src.feature_store import Connection

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)


if __name__ == '__main__':
    # Connect to the Kafka topic
    topic = kafka_topic.Connection()

    # Connect to the feature store
    feature_store = Connection()

    is_finished = False

    # Logs
    logger.info(f'Connected to Kafka broker at {config.kafka_broker_address}')
    logger.info(f'Connected to input topic at {config.kafka_input_topic}')
    logger.info(f'Connected to Hopsworks project at {config.project_name}')
    logger.info(f'Connected to Hopsworks feature store at {"BI4" if config.system_inference else "BT4"}')

    while not is_finished:
        is_finished, data = topic.consume_data(buffer_size=config.buffer_size, timeout=config.poll_timeout)

        if not data.empty:
            data: pd.DataFrame = clean.data_cleaning(data)
            data: pd.DataFrame = clean.validate_and_reduce_mem_storage(data)

            # Route to the correct feature group (inference / training)
            if config.system_inference:
                feature_store.push_BI4(
                    data,
                    # schema = config.expected_schema
                )

            elif config.system_training:
                feature_store.push_BT4(
                    data,
                    # schema = config.expected_schema
                )

        else:
            logger.info('No more messages to consume. Exiting kafka-to-store...')
            break
