from quixstreams import Application
from config import config
from api_handler import ApiHandler
from loguru import logger
import json
import time
from confluent_kafka import TopicPartition

app = Application(
    broker_address=config.kafka_broker_address,
    consumer_group=config.consumer_group,
    auto_offset_reset=config.auto_offset_reset,
    consumer_extra_config={'enable.auto.offset.store': True}
)

input_topic = app.topic(
    name=config.kafka_input_topic,
    value_deserializer='json',
    key_deserializer='string'
)

output_topic = app.topic(
    name=config.kafka_output_topic,
    value_serializer='json',
    key_serializer='string'
)

def consume_data(consumer)-> list[tuple[dict, int]]:

    buffer:list[tuple] = []
    consumer.subscribe(topics=[input_topic.name])
    while True:
        message = consumer.poll(config.poll_timeout)

        if message is None:
            if buffer:
                return buffer


        #Append the message to the buffer with its offset
        try:
            buffer.append((
                json.loads(message.value().decode('utf-8')),
                message.offset()
            ))

        
        except Exception as e:
            logger.error(f'Error consuming message: {e}')
        
        #If buffer is full, yield the data
        if len(buffer) >= config.buffer_size:
            return buffer

def produce_data(data: list[tuple[dict, int]]) -> None:
    
    with app.get_producer() as producer:    
        for tx, offset in data:
            message = output_topic.serialize(
                key=tx['key'],
                value=tx
            )
            last_offset = offset
            producer.produce(
                topic=output_topic.name,
                key=message.key,
                value=message.value,
                timestamp=tx['timestamp']
            )
        #Once the buffer is processed, commit the offset
        commit_offset(last_offset)
        logger.info(f'Enricher Microservice Enriched {len(data)} Transactions')
    
#Auxiliary function to commit the offset after processing
def commit_offset(offset: int) -> None:
    """Commit the latest offset after processing."""
    partition = TopicPartition(topic=input_topic.name, partition=0, offset=offset + 1)
    consumer.commit(offsets=[partition])


if __name__ == '__main__':
    
    
    time.sleep(config.delay * 3)
    logger.info(f'Enricher Microservice Started')
    logger.info(f'Connected to redpanda broker at {config.kafka_broker_address}')
    logger.info(f'Input topic: {config.kafka_input_topic}')
    logger.info(f'Output topic: {config.kafka_output_topic}')
   
    consumer = app.get_consumer(auto_commit_enable = False)

    while True: 
        # Consume the data
        data = consume_data(consumer)

        # Process the data
        processed_data = ApiHandler(
            data,
            config.mcaps_path,
            config.mapper_path,
            config.failed_mcaps_path,
            config.failed_date_path,
            config.failed_sic_path,
            config.failed_exchange_path,
            config.buffer_size
        ).get_enriched_data()

        # Produce the data and commit the offset
        produce_data(processed_data)
      