from config import config
import time
import pandas as pd
from src.feature_store import Connection, validate_and_reduce_mem_storage, data_cleaning
import src.kafka_topic as kafka_topic
from loguru import logger 

# Connect to the Kafka topic
topic = kafka_topic.Connection()

# Connect to the feature store
feature_store = Connection()


if __name__ == "__main__":
    
    time.sleep(config.delay*3)
    is_finished = False

    # Logs
    logger.info('Kafka to Feature Store Microservice Started')
    logger.info(f'Connected to Kafka broker at {config.kafka_broker_address}')
    logger.info(f'Input topic: {config.kafka_input_topic}')
   
    while not is_finished:
        
        is_finished, data = topic.consume_data(
            buffer_size=config.buffer_size, 
            timeout=config.poll_timeout
        )
            
        if not data.empty:
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
    logger.info('No more messages to consume. Exiting kafka-to-store...')
    feature_store.last_materialization()