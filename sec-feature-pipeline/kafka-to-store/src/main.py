from config import config
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
    logger.info(f'Connected to Kafka broker at {config.kafka_broker_address}')
    logger.info(f'Connected to input topic at {config.kafka_input_topic}')
    logger.info(f'Connected to Hopsworks project at {config.project_name}')
    logger.info(f'Connected to Hopsworks feature store at {config.feature_group_form_4_basic}')

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
                data.to_csv(config.csv_path, mode='a', header=False, index=False)

        else:
            logger.info('No more messages to consume. Exiting kafka-to-store...')
            break

    # Run the last materialization
    logger.info('No more messages to consume. Exiting kafka-to-store...')
    feature_store.last_materialization()