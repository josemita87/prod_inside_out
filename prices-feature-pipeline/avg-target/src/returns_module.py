import dask.dataframe as dd
import pandas as pd
from loguru import logger
from datetime import timedelta
class Mapper:
    def __init__(self):
         pass
      
    def process_ticker(self, ticker: str, transactions: list[dict], period: timedelta) -> pd.DataFrame:
        """
        Processes all transactions for a given ticker, and calculates the average return 
        for each of them, considering transactions for which target has been already computed.

        This we will finetune (bc, for example in year periods is prob. a simplistic approach).
        """
        # Process all transactions for this ticker

        df = pd.DataFrame(transactions)
        for tx in transactions:
            
            # Get returns belonging to the past.
            date_limit = tx['date'] + period
            data_until_tx = df[df['date'] <= date_limit]

            # Compute the average % change in price
            avg_return = data_until_tx['pct_change'].mean()

        data_until_tx['avg_return'] = avg_return
            

        return data_until_tx
