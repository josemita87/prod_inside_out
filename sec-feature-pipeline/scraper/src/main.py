"""Entry point that consumes filing URLs, parses Form 4s, and produces transactions."""

import logging
import time
from datetime import datetime

import pandas as pd
import xxhash
from config import config
from secform4strategy_clients.messaging import KafkaClient
from parser import parse_filing

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)

# Shared Kafka infra client (manual-commit consume + produce).
kafka = KafkaClient(
    broker_address=config.kafka_broker_address,
    consumer_group=config.consumer_group,
    auto_offset_reset=config.auto_offset_reset,
)


def select_urls(records: list) -> list:
    """Extract ``(url, offset)`` pairs from consumed records, dropping stale ones.

    In ``live`` mode, filings older than ``config.days_back`` are skipped; this is
    domain policy and stays in the service rather than the Kafka client.

    Args:
        records: ``(record, offset)`` pairs as returned by the Kafka client.

    Returns:
        The ``(url, offset)`` pairs to parse.
    """
    urls = []
    for msg, offset in records:
        try:
            url = msg['file_path']
            date = pd.to_datetime(msg['timestamp'], unit='ms')

            if config.mode == 'live' and date < datetime.now() - pd.Timedelta(days=config.days_back):
                logger.info(f'Filing too old: {date}')
                continue

            urls.append((url, offset))
        except Exception:
            logger.error("Couldn't extract URL from message")
            continue
    return urls


def parse_and_produce_4Fs(urls: list) -> None:
    """Parse Form 4 filings from URLs and produce their transactions in batches.

    Args:
        urls: Sequence of ``(url, offset)`` pairs to parse and produce.
    """
    buffer = []
    if config.test_trial == 'True':
        urls = urls[: config.test_size]

    for url, offset in urls:
        filing_transactions = parse_filing(url, config.sleep_time)

        if filing_transactions:
            buffer.extend(filing_transactions)

        if len(buffer) >= config.buffer_size:
            produce_data(buffer)
            # Commit the offset of the last message produced.
            kafka.commit_offset(offset)
            buffer = []

    # If there are any remaining transactions in the buffer
    if buffer:
        produce_data(buffer)
        kafka.commit_offset(offset)


def produce_data(data: list[dict]) -> None:
    """Shape transaction records (key + timestamp) and produce them to Kafka.

    Args:
        data: Transaction records to publish, each with date and link fields.
    """
    messages = []
    for record in data:
        try:
            timestamp = int(datetime.strptime(record['date'], '%Y-%m-%d').timestamp()) * 1000

        except Exception:
            try:
                if len(record['date'].split('-')) > 3:
                    # If the date has time information, split out the date part
                    date_str = '-'.join(record['date'].split('-')[:3])
                    timestamp = int(datetime.strptime(date_str, '%Y-%m-%d').timestamp()) * 1000
            except Exception:
                logger.error(f'Timestamp errror (Producer) {record}')

        # Add timestamp to the record for future reference
        record['timestamp'] = timestamp

        try:
            key = xxhash.xxh64(
                record['link'] + str(record['remaining_shares']) + ('1' if record['derivative'] else '0')
            ).hexdigest()

        except Exception:
            # Create a key for the record without using link
            key = xxhash.xxh64(str(record['remaining_shares']) + ('1' if record['derivative'] else '0')).hexdigest()

        # Add key as a value as well
        record['key'] = key

        messages.append((key, record, timestamp))

    kafka.produce(config.kafka_output_topic, messages)
    logger.debug(f'Produced {len(data)} messages')


if __name__ == '__main__':
    time.sleep(config.delay)

    # Logs
    logger.info('Scraper Microservice Started')
    logger.info(f'Connected to redpanda broker at {config.kafka_broker_address}')
    logger.info(f'Input topic: {config.kafka_input_topic}')
    logger.info(f'Output topic: {config.kafka_output_topic}')

    while True:
        records = kafka.consume_with_offsets(config.kafka_input_topic, config.buffer_size, config.poll_timeout)
        urls = select_urls(records)
        parse_and_produce_4Fs(urls)

    logger.info('Scraper Finished scraping!. Exiting...')
