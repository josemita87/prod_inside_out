from config import config
from loguru import logger
from quixstreams import Application
from datetime import datetime
from parser import Form4Parser
import xxhash
import json
from confluent_kafka import TopicPartition
import pandas as pd

app = Application(
    broker_address=config.kafka_broker_address,
    consumer_group=config.consumer_group,
    auto_offset_reset=config.auto_offset_reset,
    #consumer_extra_config={'enable.auto.offset.store': True}  
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


def consume_data(consumer) -> tuple[list[str], any]:
    """Consumes a batch of urls from the input topic 
    and returns them as a list of strings with their offsets"""
    urls = []    
    while True:
        
        message = consumer.poll(config.poll_timeout)
        if message is None:
            logger.warning('No new messages')
            return urls, consumer
        
        if len(urls) >= config.buffer_size:
            return urls, consumer
        
        try:
            # Decode the message
            msg = json.loads(message.value().decode('utf-8'))

            # Extract the URL and date
            url = msg['file_path']
            date = pd.to_datetime(msg['timestamp'], unit='ms') 

            if config.mode == "live":
                # Check if the filing is too old
                if date < datetime.now() - pd.Timedelta(days=config.days_back):
                    continue

            #Store the URL and its offset
            urls.append((url, message.offset()))
            
        except:
            logger.error('Couldn\'t extract URL from message')
            continue   

    
def parse_and_produce_4Fs(urls: list[str]) -> None:

    buffer = []
    if config.test_trial == 'True':
        urls = urls[:config.test_size]

    for url, offset in urls:
        
        filing_transactions = Form4Parser(url, config.sleep_time).create_txs()
        
        if filing_transactions:
            buffer.extend(filing_transactions)
        
        if len(buffer) >= config.buffer_size:
            produce_data(buffer)
            #Store the url offset of the last message produced
            commit_offset(offset)
            buffer = []
        
    #If there are any remaining transactions in the buffer
    if buffer:
        produce_data(buffer)
        commit_offset(offset)


def produce_data(data: list[dict]) -> None:
    
    with app.get_producer() as producer:
        for record in data:
            try:
                timestamp = int(datetime.strptime(
                    record['date'], '%Y-%m-%d').timestamp()
                ) * 1000
                
            except:
                try:
                    if len(record['date'].split('-')) > 3:
                        # If the date has time information, split out the date part
                        date_str = '-'.join(record['date'].split('-')[:3])
                        timestamp = int(datetime.strptime(
                            date_str, '%Y-%m-%d').timestamp()
                        ) * 1000
                except:
                    logger.error(f'Timestamp errror (Producer) {record}')
                
            #Add timestamp to the record for future reference
            record['timestamp'] = timestamp

            try:
                key = xxhash.xxh64(
                    record['link'] + str(record['remaining_shares']) +
                    ('1' if record['derivative'] else '0')
                ).hexdigest()

            except:
                #Create a key for the record without using link 
                key = xxhash.xxh64(
                    str(record['remaining_shares']) +
                    ('1' if record['derivative'] else '0')
                ).hexdigest()

            #Add key as a value as well
            record['key'] = key

            message = output_topic.serialize(
                key=key,
                value=record,
            )

            producer.produce(
                topic=output_topic.name,
                value=message.value,
                key=message.key,
                timestamp=timestamp
            )
                
    logger.debug(f"Produced {len(data)} messages")

#Auxiliary function to commit the offset after processing
def commit_offset(offset: int) -> None:
    """Commit the latest offset after processing."""
    partition = TopicPartition(topic=input_topic.name, partition=0, offset=offset + 1)
    consumer.commit(offsets=[partition])


if __name__ == '__main__':

    #time.sleep(config.delay)
    consumer = app.get_consumer(auto_commit_enable=False)
    consumer.subscribe(topics = [input_topic.name])

    # Logs
    logger.info(f'Scraper Microservice Started')
    logger.info(f'Connected to redpanda broker at {config.kafka_broker_address}')
    logger.info(f'Input topic: {config.kafka_input_topic}')
    logger.info(f'Output topic: {config.kafka_output_topic}')
   
    while True:
        urls, consumer = consume_data(consumer)
        transactions = parse_and_produce_4Fs(urls)


logger.info(f'Scraper Finished scraping!. Exiting...')



