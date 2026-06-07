"""Entry point that fetches SEC master-index filings and produces them to Kafka."""

import logging
import time
from collections.abc import Generator
from datetime import datetime

import pandas as pd
import xxhash
from config import config
from inside_out_clients.edgar import EdgarClient
from inside_out_clients.messaging import KafkaClient

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)

headers = {
    'User-Agent': 'CompanyE InvestmentServices admin@companye.com',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov',
}

# SEC EDGAR HTTP client (carries the required User-Agent) and Kafka producer.
edgar = EdgarClient(headers=headers)
kafka = KafkaClient(config.kafka_broker_address, loglevel='CRITICAL')


def produce_data(data: pd.DataFrame) -> None:
    """Serialize filing records and produce them to the Kafka output topic.

    Args:
        data: Filing records to publish, with file paths and dates.
    """
    data = data.copy()

    # Convert the date to a timestamp in milliseconds
    if config.mode == 'live':
        data['timestamp'] = int(datetime.now().timestamp() * 1000)

    else:
        data['timestamp'] = pd.to_datetime(data['date']).astype(int) // 10**6

    # Convert the file path to a unique key
    data['key'] = data['file_path'].apply(lambda x: xxhash.xxh64(x).hexdigest())

    # Convert the data to a list of dictionaries
    records: list[dict] = data.to_dict(orient='records')

    # Produce one batch at a time (KafkaClient.produce flushes per call). The key
    # is popped from the record so it is not duplicated inside the message value.
    for batch in batch_records(records, config.buffer_size):
        messages = [(record.pop('key'), record, record['timestamp']) for record in batch]
        kafka.produce(config.kafka_output_topic, messages)


def get_historic_data(years: int, form_type: str = '4') -> None:
    """Fetch and produce filings of a form type across past years and quarters.

    Args:
        years: Number of past years to include up to the current year.
        form_type: SEC form type to filter on.
    """
    for year in range(datetime.now().year - years, datetime.now().year + 1):
        for quarter in ['QTR1', 'QTR2', 'QTR3', 'QTR4']:
            df = edgar.fetch_master_index(year, quarter)
            if isinstance(df, pd.DataFrame):
                if not df.empty:
                    filings = df[df['form_type'] == form_type]
                    produce_data(filings)


def get_last_quarter_data(form_type: str = '4') -> None:
    """Fetch and produce filings of a form type for the current quarter.

    Args:
        form_type: SEC form type to filter on.
    """
    quarter = f'QTR{(datetime.now().month - 1) // 3 + 1}'
    df = edgar.fetch_master_index(datetime.now().year, quarter)
    if isinstance(df, pd.DataFrame):
        if not df.empty:
            filings = df[df['form_type'] == form_type]
            produce_data(filings)


def get_live_data() -> None:
    """Poll SEC EDGAR for new filing links and produce them at fixed intervals."""
    # Refresh the links every `time_between_iterations` seconds
    for _ in range(config.live_iterations):
        df = pd.DataFrame(edgar.fetch_live_links(config.num_pages), columns=['file_path'])

        logger.debug(df)
        produce_data(df)
        time.sleep(config.secs_between_iterations)


# Auxiliary function to batch records when producing data
def batch_records(records: list, buffer_size: int) -> Generator:
    """Yield successive batches of size ``buffer_size`` from ``records``.

    Args:
        records: Records to split into batches.
        buffer_size: Maximum number of records per batch.

    Returns:
        A generator yielding lists of records of at most ``buffer_size`` items.
    """
    for i in range(0, len(records), buffer_size):
        yield records[i : i + buffer_size]


if __name__ == '__main__':
    # Log the configuration
    logger.info('Master Index Microservice Started')
    logger.info(f'Connected to Kafka broker at {config.kafka_broker_address}')
    logger.info(f'Output topic: {config.kafka_output_topic}')
    logger.info(f'Buffer size: {config.buffer_size}')
    logger.info(f'Mode: {config.mode}')

    if config.mode == 'historical':
        logger.info(f'Years: {config.years}')
        get_historic_data(config.years)

    elif config.mode == 'last_quarter':
        get_last_quarter_data()

    elif config.mode == 'live':
        logger.info(f'Number of pages: {config.num_pages}')
        logger.info(f'Live iterations: {config.live_iterations}')
        logger.info(f'Seconds between iterations: {config.secs_between_iterations}')
        get_live_data()

    else:
        logger.error('Invalid mode. Exiting...')
