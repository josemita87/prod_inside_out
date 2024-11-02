from config import config
from typing import List, Dict
from loguru import logger
from quixstreams import Application
from datetime import datetime
from parser import Form4Parser
from io import BytesIO
import xxhash
import json
from itertools import islice
headers = {
    'User-Agent': 'CompanyE InvestmentServices admin@companye.com',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov'
}


app = Application(
    broker_address=config.kafka_broker_address,
    consumer_group='master-form-4-',
    auto_offset_reset='earliest',
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


def consume_data() -> List[str]:
    
    urls = []
    with app.get_consumer() as consumer:

        consumer.subscribe(topics = [input_topic.name])
        counter = 0

        while True:
            message = consumer.poll(1)
            counter += 1
            if counter > 100:
                break
            try:
                url = json.loads(message.value().decode('utf-8'))['file_path']
                urls.append(url)
                
            except:
                break    
                
    return urls

### UP TO HERE IS GOOD
def parse_4Fs(urls: List[str]) -> List[Dict]:

    transactions = []

    for url in islice(urls, 10):
        parser = Form4Parser(url)
        transactions.extend(
            parser.create_txs()
        )

    return transactions


def produce_data(data: List[dict]) -> None:

    for record in data:

        timestamp = int(datetime.strptime(
            record['date'], '%Y-%m-%d').timestamp()
        ) * 1000
        
        key = xxhash.xxh64(
            record['link'] + record['remaining_shares'] +
            ('1' if record['derivative'] else '0')
        ).hexdigest()
        
        with app.get_producer() as producer:

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
            logger.debug('Produced message to topic: {topic}', topic=output_topic.name)
            import time
            time.sleep(10)
if __name__ == '__main__':

    urls = consume_data()
    transactions = parse_4Fs(urls)
    produce_data(transactions)


# TODO
# 1. Create a connection to the redpanda broker & retrieve urls
# 2. Fetch the data from the urls
# 3. Parse the data
# 3.1 Developed Trade classes structures for 4Fs
# 3.2 Hashing logic for key with xxhash

# 4 Refactor Const and makefile to be one single file for all commands in the project
# 3.3 Configure all the APIs & data providers
# 4. Produce the data to the redpanda broker
# 5. Develop logic to consume data based on last days' trades