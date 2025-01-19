from config import config
import time
import pandas as pd
from src.feature_store import Connection, validate_and_reduce_mem_storage, data_cleaning
import src.kafka_topic as kafka_topic
from loguru import logger 




if __name__ == "__main__":
    
    # Connect to the Kafka topic
    topic = kafka_topic.Connection()

    if config.hopsworks_connect:
        
        # Connect to the feature store
        feature_store = Connection()

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
            
            if config.hopsworks_connect:
                feature_store.push_data(
                    data, 
                    schema = config.expected_schema
                )
            # If Hopsworks is not connected, save the data to a CSV file
            else:
                pd.to_csv(data, config.file_path, mode='a', header=False, index=False)

        else:
            logger.info('No more messages to consume. Exiting kafka-to-store...')
            break

    # Run the last materialization
    logger.info('No more messages to consume. Exiting kafka-to-store...')
    feature_store.last_materialization()