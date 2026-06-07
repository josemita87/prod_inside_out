"""Data cleaning and memory-reduction helpers for consumed transactions."""

import pandas as pd


def data_cleaning(data: list[dict]) -> pd.DataFrame:
    """Clean the consumed data by dropping duplicates and rows with NaN values.

    Args:
        data: List of transaction dictionaries to clean.

    Returns:
        A DataFrame with duplicate rows and rows containing NaN removed.
    """
    # Convert the list of dicts to a DataFrame
    data = pd.DataFrame(data)

    # Drop duplicate rows
    data = data.drop_duplicates()

    # Drop rows with NaN values in any column
    data = data.dropna()

    return data


# Auxiliary function
def validate_and_reduce_mem_storage(data: pd.DataFrame) -> pd.DataFrame:
    """Reduce DataFrame memory usage by downcasting columns to efficient dtypes.

    Categorical, boolean, numeric and datetime conversions are applied where the
    relevant columns exist. Rows that fail a numeric or date conversion are dropped.

    Args:
        data: DataFrame of transactions to optimize.

    Returns:
        A DataFrame with columns cast to memory-efficient dtypes and invalid rows removed.
    """
    data['link'] = data['link'].astype('str')

    # Convert columns to categorical where appropriate
    for col in [
        'company_cik',
        'ticker',
        'insider_cik',
        'insider_name',
        'owner_code',
        'exchange',
        'acquired_disposed',
        'coding',
        'sic',
    ]:
        if col in data.columns:
            data[col] = data[col].astype('category')

    # Convert booleans to actual boolean dtype
    for col in ['rule105b1', 'derivative', 'equity_swap', 'ownership']:
        if col in data.columns:
            data[col] = data[col].astype('bool')

    # Convert numeric columns to more memory-efficient types
    numeric_columns = {
        'shares': 'int32',
        'price': 'float64',
        'remaining_shares': 'int32',
        'direct_holding': 'int64',
        'indirect_holding': 'int64',
        'market_cap': 'int64',
        'timestamp': 'int64',
    }
    for col, dtype in numeric_columns.items():
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce').astype(dtype)
            data = data.dropna(subset=[col])  # Drop rows where conversion failed

    # Convert 'date' to datetime
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    data = data.dropna(subset=['date'])  # Drop rows where 'date' conversion failed

    return data
