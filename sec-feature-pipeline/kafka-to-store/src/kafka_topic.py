
from quixstreams import Application
import json
from typing import Dict, Generator, Tuple


class Connection:
    def __init__(self, broker_address, input_topic_name):
        
        
        self.app = Application(
            broker_address=broker_address,
            consumer_group='form-4-enriched',
            auto_offset_reset='earliest',
            )

        self.input_topic = self.app.topic(
            name=input_topic_name,
            value_deserializer='json',
            key_deserializer='string'
        )

         
    def consume_data(self, buffer_size) -> Tuple[bool, list[Dict]]:

        buffer = []
        with self.app.get_consumer() as consumer:
            consumer.subscribe(topics=[self.input_topic.name])

            while True:

                if message:= consumer.poll() is None:
                    return True, buffer
                breakpoint()
                buffer.append(json.loads(message.value().decode('utf-8')))
                
                if len(buffer) >= buffer_size:
                    return False, buffer
                    

        