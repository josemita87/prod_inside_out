#import dask.dataframe as dd
import pandas as pd
from loguru import logger
import numpy as np
from numba import jit

def data_aggregation(transactions: pd.DataFrame, agg_dict: dict) -> pd.DataFrame:
    """
    Aggregate transaction data based on the provided aggregation dictionary.

    Parameters:
    -----------
    transactions : pd.DataFrame
        DataFrame containing transaction data.
    agg_dict : dict
        Dictionary specifying the aggregation operations.

    Returns:
    --------
    pd.DataFrame
        Aggregated transaction data.
    """
    # Filter out columns that are not present in the transactions DataFrame
    valid_agg_dict = {k: v for k, v in agg_dict.items() if k in transactions.columns}
    return transactions.groupby(['ticker', 'date'], as_index=False).agg(valid_agg_dict)

def compute_target(transactions: pd.DataFrame, prices: pd.DataFrame, period: int) -> pd.DataFrame:
    """
    Compute the target prices and percentage changes for transactions.

    Parameters:
    -----------
    transactions : pd.DataFrame
        DataFrame containing transaction data.
    prices : pd.DataFrame
        DataFrame containing price data.
    period : int
        Period for computing the target prices.

    Returns:
    --------
    pd.DataFrame
        DataFrame with computed target prices and percentage changes.
    """
    # Homogenize the date format
    transactions['date'] = pd.to_datetime(transactions['date']).dt.tz_convert('UTC')
    prices['date'] = pd.to_datetime(prices['date']).dt.tz_convert('UTC')

    # Remove timezone information to ensure both DataFrames have the same datetime type
    transactions['date'] = transactions['date'].dt.tz_localize(None)
    prices['date'] = prices['date'].dt.tz_localize(None)
    
    # Ensure both DataFrames have the same datetime type
    transactions['date'] = transactions['date'].astype('datetime64[ns]')
    prices['date'] = prices['date'].astype('datetime64[ns]')

    # Sort both dataframes by date
    transactions.sort_values(['date'], inplace=True)
    prices.sort_values(['date'], inplace=True)

    assert transactions['date'].is_monotonic_increasing, "Transaction dates not sorted"
    assert prices['date'].is_monotonic_increasing, "Price dates not sorted"
    
    # Backward merge_asof to get the start price
    start_state = pd.merge_asof(
        left=transactions,
        right=prices,
        on='date',
        by='ticker',
        direction='backward'
    ).rename(columns={'close': 'start_price'})

    # Create future_date column and filter out dates in the future
    latest_date = prices['date'].max()
    start_state['future_date'] = start_state['date'] + pd.to_timedelta(period, unit='D')
    start_state = start_state[start_state['future_date'] <= latest_date]

    # Perform forward merge_asof to get the end price
    end_state = pd.merge_asof(
        left=start_state,
        right=prices,
        left_on='future_date',
        right_on='date',
        by='ticker',
        direction='forward'
    ).rename(columns={'close': 'end_price', 'date_x': 'date'})

    # Drop the future_date column
    end_state = end_state.drop(columns=['future_date'])

    # Calculate % change
    end_state['pct_change'] = (
        ((end_state['end_price'] - end_state['start_price']) / end_state['start_price']).round(5)
    )

    # Collapse price columns into one: this way we increase likelihood of having a price to work with
    end_state['price'] = np.where(
        end_state['price'] == 0, 
        end_state['start_price'], 
        end_state['price']
    )

    # Convert the shares-related counts to USD value 
    end_state[['tx_value', 'remaining_value', 'direct_holding', 'indirect_holding']] = \
        end_state[['shares', 'remaining_shares', 'direct_holding', 'indirect_holding']].mul(end_state['price'], axis=0)

    # Drop unnecessary columns 
    end_state = end_state.drop(columns=['start_price', 'end_price', 'remaining_shares', 'shares', 'date_y'])

    logger.debug(f"Target computation completed. Shape: {end_state.shape}")
    return end_state

def compute_RT4(df: pd.DataFrame, timedelta: int) -> pd.DataFrame:
    """
    Compute the average target price over a specified time period.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing transaction data.
    timedelta : int
        Time period for computing the average target price.

    Returns:
    --------
    pd.DataFrame
        DataFrame with computed average target prices.
    """
    # Sort the dataframe by ticker and date
    df.sort_values(['ticker', 'date'], inplace=True)

    # Constant period (days) covered (in milliseconds)
    delta_ms = timedelta * 24 * 60 * 60 * 1000 

    # Prepare an empty column to store the average pct_change
    df['avg_target_expanding'] = np.nan

    # Extract timestamps and pct_changes for easier access
    timestamps = df['timestamp'].astype(np.int64).values  
    pct_changes = df['pct_change'].astype(np.float64).values  
    tickers = df['ticker'].astype(str).values 
    
    # Numba JIT-compiled function for computing expanding averages
    #@jit(nopython=True, parallel=True)
    def expanding_average(tickers, timestamps, pct_changes, delta_ms):
        """
        Compute the expanding average of percentage changes over a specified time period.
        This algorithm works the follwing way:
            1. For each ticker, get the timestamp of the current row.
            2. Find the offset, which is the row that is delta_ms milliseconds before the row timestamp.
            3. Compute the average of all percentage changes belonging to the same ticker 
            (in other words, after the recorded offset and before the timestamp found in step 2).

            *Step 3 ensures the average_target resulting from this function is not biased by the
            percentage changes of the same ticker that happened after the current row*

        Parameters:
        -----------
        tickers : np.ndarray
            Sorted array of ticker symbols.
        timestamps : np.ndarray
            Sorted array of timestamps in milliseconds.
        pct_changes : np.ndarray
            Sorted array of percentage changes.
        delta_ms : int
            Time period for computing the expanding average in milliseconds.

        Returns:
        --------
        np.ndarray
            Array of computed expanding averages.
        """
        avg_pct_changes = np.empty_like(pct_changes)  
        
        # Initialize offset tracker
        offset = 0
        last_ticker = tickers[0]  
        
        for i in range(len(tickers)):
            current_ticker = tickers[i]
            current_timestamp = timestamps[i]
            cutoff_time = current_timestamp - delta_ms
            
            # Reset offset if we move to a new ticker
            if current_ticker != last_ticker:
                offset = i 
            
            # Perform binary search to find the cutoff index for this ticker
            idx = np.searchsorted(timestamps[offset:], cutoff_time, side='right') + offset
            
            if idx > offset:
                # Get all pct_changes before the cutoff time for this ticker
                valid_pct_changes = pct_changes[offset:idx]
                avg_pct_changes[i] = np.nanmean(valid_pct_changes)  
            else:
                avg_pct_changes[i] = np.nan  
            
            # Update the last_ticker for the next iteration
            last_ticker = current_ticker

        return avg_pct_changes

    # Call the Numba-accelerated function
    df['avg_target_expanding'] = expanding_average(tickers, timestamps, pct_changes, delta_ms)

    return df

def map_RT4_to_BIR4(target_dataframe: pd.DataFrame, inference_data: pd.DataFrame) -> pd.DataFrame:
    """
    Maps the latest "avg_target_expanding" values from the target DataFrame 
    into an "avg_target_expanding" column in the inference DataFrame.

    Parameters:
    -----------
    target_dataframe : pd.DataFrame
        DataFrame containing at least "ticker", "date", and "avg_target_expanding".
    inference_data : pd.DataFrame
        DataFrame where the "avg_target_expanding" column will be added 
        based on the matching ticker.

    Returns:
    --------
    pd.DataFrame
        The inference DataFrame with an additional "avg_target_expanding" column containing the mapped values.
    """
    # Group the dataframe by ticker and select the last row (in terms of date) for each ticker
    df = target_dataframe.sort_values(
        by='date', 
        ascending=True
    ).groupby('ticker').tail(1)

    # Map the values
    inference_data['avg_target_expanding'] = inference_data['ticker'].map(
        df.set_index('ticker')['avg_target_expanding']
    )

    return inference_data









