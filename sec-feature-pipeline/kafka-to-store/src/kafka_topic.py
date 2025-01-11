
from quixstreams import Application
import json
from typing import Generator, Tuple
import pandas as pd
from datetime import datetime
from config import config

class Connection:
    def __init__(self):
        
        self.app = Application(
            broker_address=config.kafka_broker_address,
            consumer_group=config.consumer_group,
            auto_offset_reset=config.auto_offset_reset,
            consumer_extra_config={'enable.auto.offset.store': True}
        )

        self.input_topic = self.app.topic(
            name=config.kafka_input_topic,
            value_deserializer='json',
            key_deserializer='string'
        )

         
    def consume_data(self, buffer_size:int, timeout:int) -> Generator[Tuple[bool, pd.DataFrame], None, None]:
        """ In this method, we consume data from the Kafka topic and return a buffer of transactions.
        We do not use generators because the aim is to push data in batches to the feature store."""

        buffer = []
        with self.app.get_consumer(auto_commit_enable=True) as consumer:
            consumer.subscribe(topics=[self.input_topic.name])

            while True:
                
                message = consumer.poll(timeout)
                if not message:
                    return True, pd.DataFrame(buffer)
            
                if message:
        
                    updated_values = json.loads(message.value().decode('utf-8'))
                    if 'date' in updated_values:
                        updated_values['date'] = datetime.strptime(updated_values['date'][:10], '%Y-%m-%d')
                    
                    buffer.append(updated_values)
                    
                
                if len(buffer) >= buffer_size:
                    return False, pd.DataFrame(buffer)
                    

        