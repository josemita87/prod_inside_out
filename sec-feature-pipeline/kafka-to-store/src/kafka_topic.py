"""Kafka topic connection and batch consumption for the kafka-to-store service."""

import json
from datetime import datetime
from typing import Generator, Tuple

import pandas as pd
from config import config
from quixstreams import Application


class Connection:
    """Manage the Kafka application and input topic used to consume transactions.

    Attributes:
        app: The quixstreams Application bound to the configured broker.
        input_topic: The configured Kafka input topic to consume from.
    """

    def __init__(self):

        self.app = Application(
            broker_address=config.kafka_broker_address,
            consumer_group=config.consumer_group,
            auto_offset_reset=config.auto_offset_reset,
            consumer_extra_config={'enable.auto.offset.store': True},
        )

        self.input_topic = self.app.topic(
            name=config.kafka_input_topic, value_deserializer='json', key_deserializer='string'
        )

    def consume_data(self, buffer_size: int, timeout: int) -> Generator[Tuple[bool, pd.DataFrame], None, None]:
        """Consume messages from the Kafka topic and return a batch of transactions.

        Data is returned in batches rather than streamed so it can be pushed to the
        feature store in bulk. The ``date`` field of each message is parsed to a datetime.

        Args:
            buffer_size: Number of messages to accumulate before returning a batch.
            timeout: Poll timeout in seconds for each consumer poll.

        Returns:
            A tuple of a finished flag and a DataFrame of buffered transactions. The
            flag is True when the topic is exhausted and False when the buffer is full.
        """
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
