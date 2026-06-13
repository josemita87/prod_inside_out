"""Entry point for the price-ingestion service: refresh the prices (P) feature group."""

import logging
import time

from src.config import config
from src.ingestion import PriceIngestor

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)


if __name__ == '__main__':
    # Fetch the latest prices and update the prices (P) feature group.
    time.sleep(config.delay)
    ingestor = PriceIngestor()
    ingestor.process_tickers()
