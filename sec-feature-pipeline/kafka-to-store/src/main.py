from config import config
import time
import pandas as pd
from src.feature_store import Connection, validate_and_reduce_mem_storage, data_cleaning
import src.kafka_topic as kafka_topic
from loguru import logger 

# Connect to the Kafka topic
topic = kafka_topic.Connection(
    config.kafka_broker_address,
    config.kafka_input_topic,
    config.consumer_group, 
    config.auto_offset_reset,
    config.processing_guarantee
    
)

# Connect to the feature store
feature_store = Connection()


if __name__ == "__main__":
    
    time.sleep(config.delay*3)
    is_finished = False

    # Logs
    logger.info('Kafka to Feature Store Microservice Started')
    logger.info(f'Connected to Kafka broker at {config.kafka_broker_address}')
    logger.info(f'Input topic: {config.kafka_input_topic}')
    logger.info(f'ENV VARIABLES:\n ->Buffer Size: {config.buffer_size}\n ->Feature Group Name: {config.feature_group_form_4_basic}\n ->Feature Group Version: {config.feature_group_version}')
    
    while not is_finished:
        
        is_finished, data = topic.consume_data(
            buffer_size=config.buffer_size, 
            timeout=config.poll_timeout
        )
            
        if data:
            data:pd.DataFrame = data_cleaning(data)
            data:pd.DataFrame = validate_and_reduce_mem_storage(data)
            
            feature_store.push_data(
                data, 
                schema = config.expected_schema
            )
        else:
            logger.info('No more messages to consume. Exiting kafka-to-store...')
            break

    # Run the last materialization
    feature_store.last_materialization()