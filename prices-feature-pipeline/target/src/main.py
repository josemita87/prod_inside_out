
from src.config import config
from src import computations
from src import clean
from src import feature_store
import time
from loguru import logger

class DataProcessor:
    """Class to process data for the target microservice."""
    
    def __init__(self):
        self.feature_store = feature_store.Connection()
       
    def process_data(self):
        """Process the data based on the system configuration."""

        # Run system in training mode
        if config.system_training:

            # Fetch transactions data
            BT4 = self.feature_store.fetch_BT4(
                key=config.filter_key, 
                value=config.acquired_disposed
            )
            # Get unique tickers
            tickers_to_process = clean.get_unique_tickers(BT4)

            logger.warning(tickers_to_process)
            # Fetch P (price data)
            P = self.feature_store.fetch_P(tickers_to_process)
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
            self.feature_store.push_RT4(RT4)
            
        # Run system in inference mode
        elif config.system_inference:
            # Fetch transactions data
            BI4 = self.feature_store.fetch_BI4(
                key=config.filter_key, 
                value=config.acquired_disposed
            )
            # Normalize tickers
            BI4 = clean.normalize_data(BI4)

            # Aggregate the data on a daily basis, as defined by config.adg_dict
            BI4_AGG = computations.data_aggregation(BI4, config.agg_dict)

            # Get unique tickers
            tickers_to_process = clean.get_unique_tickers(BI4_AGG)

            # Fetch RT4 (form4 + computations)
            RT4 = self.fetch_RT4()

            # Map the average pct_change to BIR4
            BIR4 = computations.map_RT4_to_BIR4(RT4)
            BIR4 = clean.data_cleaning(BIR4)
            
            # Push BIR4 to the feature store
            self.feature_store.push_BIR4(BIR4)

        
def main():
    """Main function to initiate the DataProcessor."""
    time.sleep(config.delay)
    processor = DataProcessor()
    processor.process_data()

if __name__ == "__main__":
    main()

