"""Consume SEC transactions, enrich them with market cap/exchange/SIC, re-produce.

Domain orchestration only: it leverages the shared clients (Kafka, market data)
and keeps the enricher-specific logic — date handling, source ordering, and the
local parquet/JSON caches — here, since none of that is general-purpose infra.
"""

import json
import logging
import os
import time
from datetime import datetime

import pandas as pd
from config import config
from secform4strategy_clients.market_data import MarketDataClient
from secform4strategy_clients.messaging import KafkaClient

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)

# Shared infra clients.
kafka = KafkaClient(
    broker_address=config.kafka_broker_address,
    consumer_group=config.consumer_group,
    auto_offset_reset=config.auto_offset_reset,
)
market_data = MarketDataClient()

# Local datasets, loaded once: cached market caps and the CIK -> metadata mapper.
mcaps = pd.read_parquet(config.mcaps_path)
mapper = json.load(open(config.mapper_path))

FAILED_PATHS = {
    'missing_mcap': config.failed_mcaps_path,
    'missing_date': config.failed_date_path,
    'missing_sic': config.failed_sic_path,
    'missing_exchange': config.failed_exchange_path,
}


def _append_to_parquet(path: str, data: pd.DataFrame) -> None:
    """Append rows to a parquet file, creating it if it does not yet exist."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        data = pd.concat([pd.read_parquet(path), data], ignore_index=True)
    data.to_parquet(path, index=False)


def record_failure(tx: dict, kind: str) -> None:
    """Append a failed transaction to the parquet log for the given failure kind."""
    path = FAILED_PATHS[kind]
    if kind == 'missing_mcap':
        try:
            _date = datetime.strptime(tx.get('date'), '%Y-%m-%d').date()
            fbd = pd.date_range(start=_date.replace(day=1), periods=1, freq='BMS')[0].date()
            _append_to_parquet(path, pd.DataFrame([[tx.get('ticker').upper(), fbd]], columns=['ticker', 'date']))
        except Exception:
            record_failure(tx, 'missing_date')
    elif kind == 'missing_date':
        _append_to_parquet(path, pd.DataFrame([tx.get('ticker').upper()], columns=['ticker']))
    elif kind in {'missing_sic', 'missing_exchange'}:
        _append_to_parquet(path, pd.DataFrame([tx.get('company_cik')], columns=['cik']))


def get_market_cap(tx: dict):
    """Resolve the market cap from Yahoo Finance (recent) or the local cache."""
    try:
        _date = datetime.strptime(tx.get('date'), '%Y-%m-%d').date()
        fbd = pd.date_range(start=_date.replace(day=1), periods=1, freq='BMS')[0].date()
    except (ValueError, TypeError):
        fbd = None
        record_failure(tx, 'missing_date')

    if fbd:
        if fbd >= datetime(2024, 9, 1).date():
            ticker = tx.get('ticker')
            try:
                mcap = market_data.market_cap(ticker)
                pd.DataFrame([[ticker, mcap, fbd]], columns=['ticker', 'mcap', 'date']).to_parquet(
                    config.mcaps_path, engine='pyarrow', append=True
                )
                return mcap
            except Exception:
                return None
    try:
        row = mcaps[(mcaps['ticker'] == tx.get('ticker').upper()) & (mcaps['fbd'] == fbd)]
        return int(row['marketcap'].iloc[0])
    except Exception:
        record_failure(tx, 'missing_mcap')


def get_exchange(tx: dict):
    """Resolve the exchange from the mapper, falling back to Yahoo Finance."""
    try:
        return mapper['exchange'].get(tx.get('company_cik'), None)
    except Exception:
        try:
            return market_data.exchange(tx.get('ticker'))
        except Exception:
            record_failure(tx, 'missing_exchange')


def get_sic(tx: dict):
    """Resolve the SIC code from the mapper."""
    try:
        return mapper['sic'].get(tx.get('company_cik'), None)
    except Exception:
        record_failure(tx, 'missing_sic')


def enrich(transactions: list) -> list:
    """Enrich each ``(transaction, offset)`` with market cap, exchange and SIC."""
    enriched = []
    for tx, offset in transactions:
        tx['market_cap'] = get_market_cap(tx)
        tx['exchange'] = get_exchange(tx)
        tx['sic'] = get_sic(tx)
        enriched.append((tx, offset))
    return enriched


if __name__ == '__main__':
    time.sleep(config.delay * 3)
    logger.info('Enricher Microservice Started')
    logger.info(f'Connected to redpanda broker at {config.kafka_broker_address}')
    logger.info(f'Input topic: {config.kafka_input_topic}')
    logger.info(f'Output topic: {config.kafka_output_topic}')

    while True:
        # Consume a batch of (transaction, offset) pairs (manual commit).
        data = kafka.consume_with_offsets(config.kafka_input_topic, config.buffer_size, config.poll_timeout)

        processed = enrich(data)
        if not processed:
            continue

        # Produce the enriched transactions, then commit the last consumed offset.
        messages = [(tx['key'], tx, tx['timestamp']) for tx, _ in processed]
        kafka.produce(config.kafka_output_topic, messages)
        kafka.commit_offset(processed[-1][1])
        logger.info(f'Enricher Microservice Enriched {len(processed)} Transactions')
