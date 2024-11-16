from config import config
import time
import pandas as pd
import kafka_topic, feature_store


# Connect to the Kafka topic
topic = kafka_topic.Connection(
    broker_address=config.kafka_broker_address,
    input_topic_name=config.kafka_input_topic,
)

# Connect to the feature store
feature_store = feature_store.Connection(
    project_name=config.project_name,
    api_key=config.api_key,
)

# Connect to the feature group
feature_group = feature_store.connect_feature_group(
    feature_group_name=config.feature_group_name,
    feature_group_version=config.feature_group_version,
    primary_key='key',
    event_time='date'
)


if __name__ == "__main__":
    is_finished = False

    while not is_finished:
        is_finished, data = topic.consume_data(buffer_size=config.buffer_size)

        #Sleep to avoid overloading the feature store
        time.sleep(60)
        
        if data:
            feature_store.push_data(
                pd.DataFrame(data), 
                feature_group, 
                config.expected_schema
            )
