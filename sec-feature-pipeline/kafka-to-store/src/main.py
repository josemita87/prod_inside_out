
import hopsworks
import quixstreams
from config import config
import pandas as pd
import kafka_topic, feature_store



topic = kafka_topic.Connection(
    broker_address=config.kafka_broker_address,
    input_topic_name=config.kafka_input_topic,
)

feature_store = feature_store.Connection(
    project_name=config.project_name,
    api_key=config.api_key,
)

feature_group = feature_store.connect_feature_group(
    feature_group_name=config.feature_group_name,
    feature_group_version=config.feature_group_version,
    primary_key=config.primary_key,
    event_time=config.event_time
)


if __name__ == "__main__":
    is_finished = False

    while not is_finished:
        is_finished, data = topic.consume_data(buffer_size=config.buffer_size)

        if data:
            feature_store.push_data(
                data, 
                feature_group, 
            )
