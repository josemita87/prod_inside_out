import dask.dataframe as dd
import pandas as pd
from loguru import logger

class Mapper:
    def __init__(self, prices: pd.DataFrame):
        self.prices = prices  
      
    def compute_returns(self, tx: dict, period: pd.Timedelta) -> dict:

        try:
            # Get the historical prices for the given ticker
            ticker_prices = self.prices[
                self.prices['ticker'] == tx['ticker']
            ].sort_values(by = 'date').compute() 

            # Get the last price before the transaction date
            start_price = ticker_prices[
                ticker_prices['date'] <= tx['date']
            ]['close'].values[-1]  
            
            # Get the first price after the period
            end_price = ticker_prices[
                ticker_prices['date'] >= tx['date'] + period
            ]['close'].values[0]  

            # Compute the average % change in price
            tx['pct_change'] = round((end_price - start_price) / start_price, 5)
            
           
        # Track errors
        except Exception as e:

            logger.error(f"Failed to compute % change for {tx['ticker']} on {tx['date']}: {e}")
            tx['pct_change'] = 0.0
            #with open('failed_txs.txt', 'a') as f:
                #if tx['ticker'] and tx['date']:
                   # f.write(f"{tx['ticker']},{tx['date']},{e}\n")

        return tx

    def process_ticker(self, ticker: str, transactions: list[dict], period: int) -> pd.DataFrame:
        """
        Processes all transactions for a given ticker.
        After processing all transactions for a ticker, it removes the processed ticker's data from `self.prices`.
        """
        # Process all transactions for this ticker
        processed_transactions = []
        for tx in transactions:
            #logger.debug(f"Processing transaction {transactions.index(tx) + 1} of {len(transactions)} for ticker {ticker}")
            processed_tx = self.compute_returns(tx, period)
            processed_transactions.append(processed_tx)

        # Convert the processed transactions to a DataFrame
        processed_transactions = pd.DataFrame(processed_transactions)
        
        # Remove the ticker's data (using Dask) to enhance performance
        self.prices = self.prices[self.prices['ticker'] != ticker]

        return processed_transactions
