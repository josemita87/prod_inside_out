import pandas as pd
import numpy as np
from loguru import logger

def get_unique_tickers(df: pd.DataFrame) -> list:
    """
    Returns a list of unique tickers from the specified DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing the transactions with a 'ticker' column.

    Returns:
        list: List of unique tickers.
    """
    return df['ticker'].unique().tolist()

def data_cleaning(data: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the data by replacing 'None' and '---' with NaN, dropping duplicates,
    and removing rows with NaN in 'pct_change' and 'avg_target_expanding'.

    Args:
        data (pd.DataFrame): DataFrame to be cleaned.

    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    data.replace(['None', '---'], np.nan, inplace=True)
    data.drop_duplicates(inplace=True)
    data.dropna(subset=['pct_change', 'avg_target_expanding'], inplace=True)
    return data

def normalize_data(
        txs: pd.DataFrame = pd.DataFrame(), 
        prices: pd.DataFrame = pd.DataFrame()
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ensures 'ticker' columns in both DataFrames are uppercase, verifies that
    'acquired_disposed' is 'D', and returns the updated DataFrames.

    Parameters:
    -----------
    txs : pd.DataFrame
        DataFrame for transactions containing 'ticker' and 'acquired_disposed'.
    prices : pd.DataFrame
        DataFrame for prices containing 'ticker'.

    Returns:
    --------
    tuple[pd.DataFrame, pd.DataFrame]
        The updated txs and prices DataFrames with consistent formatting.
    """
    try:
        if not txs.empty: 
            # Convert 'ticker' columns to uppercase and strip whitespace
            txs['ticker'] = txs['ticker'].str.upper().str.strip()
            # Convert 'acquired_disposed' column to uppercase, strip whitespace, and fill missing values
            txs['acquired_disposed'] = txs['acquired_disposed'].str.upper().str.strip()

            # Verify that all values in 'acquired_disposed' are 'D'
            if not (txs['acquired_disposed'] == 'D').all():
                raise ValueError("Not all values in 'acquired_disposed' are 'D'")

        if not prices.empty:
            prices['ticker'] = prices['ticker'].str.upper().str.strip()

        logger.info("Data cleaning and formatting successful.")
        return txs, prices

    except Exception as e:
        logger.error(f"Error in assert_and_format_data: {e}")
        raise