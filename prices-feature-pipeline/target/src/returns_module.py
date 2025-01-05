import dask.dataframe as dd
import pandas as pd
from loguru import logger

class Mapper:
    def __init__(self, prices: pd.DataFrame):
        self.prices = prices
       
      
    def compute_returns(
        self, 
        transactions:dd.DataFrame, 
        period: int) -> dd.DataFrame:
       
        processed_transactions = []
        # 1. Sort both dataframes by ticker and date
        transactions = transactions.sort_values(['ticker', 'date'])
        self.prices = self.prices.sort_values(['ticker', 'date'])

        # 2. Repartition by ticker and date to avoid partition overlap
        transactions = transactions.repartition(npartitions='auto', partition_size='100MB')
        self.prices = self.prices.repartition(npartitions='auto', partition_size='100MB')

        # 3. Now set the index on the 'date' column with sorted=True
        transactions = transactions.set_index('date', sorted=True)
        self.prices = self.prices.set_index('date', sorted=True)

        # 2. Backward merge_asof to get the start price
        start_state = dd.merge_asof(
            transactions,
            self.prices,
            on='date',
            by='ticker',
            direction='backward'
        ).rename(columns={'close': 'start_price'})

        # 3. Create future_date column and filter out dates in the future
        latest_date = self.prices['date'].max()
        transactions = transactions.assign(
            future_date=transactions['date'] + pd.to_timedelta(period, unit='D')
        )
        latest_date = self.prices['date'].max().compute()  # Compute the scalar max date

        transactions = transactions[transactions['future_date'] <= latest_date]

       #perform forward merge_asof to get the end price
        end_state = dd.merge_asof(
            transactions,
            self.prices,
            left_on='future_date',
            right_on='date',
            by='ticker',
            direction='forward'
        ).rename(columns={'close': 'end_price'})

       # 5. Combine start_state and end_state with the transactions DataFrame
        transactions = transactions.assign(
            start_price=start_state['start_price'],
            end_price=end_state['end_price']
        )
        
        # 6. Calculate % change
        transactions = transactions.assign(
            pct_change=((transactions['end_price'] - transactions['start_price']) / 
                        transactions['start_price']).round(5)
        )

        # 7. Drop the future_date column
        transactions = transactions.drop(columns=['future_date'])

        return transactions






















        for tx in transactions.to_dict(orient='records'):
            processed_tx = self.compute_returns(tx, ticker, period)
            processed_transactions.append(processed_tx)

        # Convert the processed transactions to a DataFrame
        processed_transactions = pd.DataFrame(processed_transactions)
        
        # Remove the ticker's data (using Dask) to enhance performance
        self.prices = self.prices[self.prices['ticker'] != ticker]

        return processed_transactions
