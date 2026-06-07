"""Entry point that fetches SEC master-index filings and produces them to Kafka."""

import logging
import time
from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING, Generator

import pandas as pd
import requests
import xxhash
from config import config
from monitor_live import SECLinkMonitor
from quixstreams import Application

if TYPE_CHECKING:
    from typing import Dict, List

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

# Create a connection to the redpanda broker
app = Application(config.kafka_broker_address, loglevel='CRITICAL')
output_topic = app.topic(name=config.kafka_output_topic, value_serializer='json', key_serializer='string')


def fetch_parse_data(year, quarter):
    """Fetch and parse the SEC master index for a given year and quarter.

    Args:
        year: Calendar year of the master index to retrieve.
        quarter: Quarter identifier (e.g. ``QTR1``) of the master index.

    Returns:
        A DataFrame of filing records when the request succeeds, otherwise None.
    """
    url = f'https://www.sec.gov/Archives/edgar/full-index/{year}/{quarter}/master.idx'

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        content_str = response.content.decode('utf-8')
        lines = content_str.splitlines()

        start_index = 0
        # Crop the header
        for i, line in enumerate(lines):
            if '|' in line:
                start_index = i + 2
                break

        data_str = '\n'.join(lines[start_index:])

        data = BytesIO(data_str.encode('utf-8'))

        # Now read the data into a DataFrame
        df = pd.read_csv(
            data,
            sep='|',
            header=None,
            names=['cik', 'company', 'form_type', 'date', 'file_path'],
            dtype=str,
            encoding='utf-8',
        )

        time.sleep(1)
        logger.debug(f'Fetched data for {year} {quarter}')
        return df


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
    records: List[Dict] = data.to_dict(orient='records')

    with app.get_producer() as producer:
        # Split the records into batches
        batch: Generator = batch_records(records, config.buffer_size)

        for records in batch:
            for record in records:
                key = record.pop('key')
                message = output_topic.serialize(
                    key=key,
                    value=record,
                )

                producer.produce(
                    topic=output_topic.name, value=message.value, key=message.key, timestamp=record['timestamp']
                )

            # Flush the producer
            producer.flush()


def get_historic_data(years: int, form_type: str = '4') -> None:
    """Fetch and produce filings of a form type across past years and quarters.

    Args:
        years: Number of past years to include up to the current year.
        form_type: SEC form type to filter on.
    """
    for year in range(datetime.now().year - years, datetime.now().year + 1):
        for quarter in ['QTR1', 'QTR2', 'QTR3', 'QTR4']:
            df = fetch_parse_data(year, quarter)
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
    df = fetch_parse_data(datetime.now().year, quarter)
    if isinstance(df, pd.DataFrame):
        if not df.empty:
            filings = df[df['form_type'] == form_type]
            produce_data(filings)


def get_live_data() -> None:
    """Poll SEC EDGAR for new filing links and produce them at fixed intervals."""
    # Instantiate the SECLinkMonitor
    monitor = SECLinkMonitor(config.num_pages)

    # Refresh the links every `time_between_iterations` seconds
    for _ in range(config.live_iterations):
        df = pd.DataFrame(monitor.parse_links(), columns=['file_path'])

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
