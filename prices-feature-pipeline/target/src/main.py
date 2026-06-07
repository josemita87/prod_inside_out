"""Entry point for the target microservice training and inference flows."""

import logging
import time

import pandas as pd
from inside_out_clients.feature_store import HopsworksClient

from src import clean, computations
from src.config import config

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)

_KEYED = {'primary_key': ['key'], 'event_time': 'date', 'online_enabled': False, 'stream': False}
# Catalog mapping this service's references to feature-group specs.
FEATURE_GROUPS = {
    'p': {
        'name': 'p',
        'version': config.feature_group_version,
        'primary_key': ['ticker', 'date'],
        'event_time': 'date',
        'online_enabled': False,
        'stream': False,
    },
    'bt4': {'name': 'bt4', 'version': config.feature_group_version, 'primary_key': ['key'], 'event_time': 'date'},
    'bi4': {'name': 'bi4', 'version': config.feature_group_version, **_KEYED},
    'rt4': {'name': 'rt4', 'version': config.feature_group_version, **_KEYED},
    'bir4': {'name': 'bir4', 'version': config.feature_group_version, **_KEYED},
}


class DataProcessor:
    """Process data for the target microservice.

    Attributes:
        feature_store: Connection to the feature store backend.
    """

    def __init__(self):
        """Initialize the processor with a feature store connection."""
        self.feature_store = HopsworksClient(config.project_name, config.hopsworks_api_key, FEATURE_GROUPS)

    def process_data(self):
        """Process the data based on the system configuration."""
        # Run system in training mode
        if config.system_training:
            # Fetch transactions data
            BT4 = self.feature_store.read(
                'bt4',
                where=lambda fg: fg.filter(fg[config.filter_key] == config.acquired_disposed),
                read_options={'use_hive': True},
            )
            # Get unique tickers
            tickers_to_process = clean.get_unique_tickers(BT4)

            logger.warning(tickers_to_process)
            # Fetch P (price data)
            try:
                P = self.feature_store.read(
                    'p',
                    where=lambda fg: fg.filter(fg['ticker'].isin(tickers_to_process)),
                    read_options={'use_hive': True},
                )
            except Exception:
                P = pd.DataFrame()
            logger.warning(P)

            # Assert and format data
            BT4, P = clean.normalize_data(BT4, P)

            # Aggregate the data on a daily basis, as defined by config.adg_dict
            BT4_AGG = computations.data_aggregation(BT4, config.agg_dict)

            # Compute percentage change in price after config.delta_period days
            semiRT4 = computations.compute_target(BT4_AGG, P, config.delta_period)

            # Compute RT4 (form4 + computations)
            RT4 = computations.compute_RT4(df=semiRT4, timedelta=config.delta_period)
            RT4 = clean.data_cleaning(RT4)

            # Push RT4 to the feature store
            self.feature_store.push('rt4', RT4)

        # Run system in inference mode
        elif config.system_inference:
            # Fetch transactions data
            BI4 = self.feature_store.read(
                'bi4',
                where=lambda fg: fg.filter(fg[config.filter_key] == config.acquired_disposed),
                read_options={'use_hive': True},
            )
            # Normalize tickers
            BI4 = clean.normalize_data(BI4)

            # Aggregate the data on a daily basis, as defined by config.adg_dict
            BI4_AGG = computations.data_aggregation(BI4, config.agg_dict)

            # Get unique tickers
            tickers_to_process = clean.get_unique_tickers(BI4_AGG)

            # Fetch RT4 (form4 + computations)
            RT4 = self.feature_store.read('rt4', read_options={'use_hive': True})

            # Map the average pct_change to BIR4
            BIR4 = computations.map_RT4_to_BIR4(RT4)
            BIR4 = clean.data_cleaning(BIR4)

            # Push BIR4 to the feature store
            self.feature_store.push('bir4', BIR4)


def main():
    """Main function to initiate the DataProcessor."""
    time.sleep(config.delay)
    processor = DataProcessor()
    processor.process_data()


if __name__ == '__main__':
    main()
