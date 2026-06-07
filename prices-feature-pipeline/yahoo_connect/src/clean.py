"""Memory-reduction utilities for price DataFrames."""

import pandas as pd


def reduce_mem_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce the memory usage of the given DataFrame.

    Drops an ``index`` column if present, converts ``date`` to datetime,
    ``close`` to float32, and ``ticker`` to a categorical dtype.

    Args:
        df: DataFrame with ``date``, ``close`` and ``ticker`` columns.

    Returns:
        The DataFrame with downcast column dtypes.
    """
    # Drop index column if it exists
    if df.columns.str.contains('index').any():
        df.drop(columns=['index'], inplace=True)
    # Convert the date column to datetime 64ns
    df['date'] = pd.to_datetime(df['date'])
    # Convert the close column to float32
    df['close'] = df['close'].astype('float32')
    # Convert the ticker column to category
    df['ticker'] = df['ticker'].astype('category')

    return df
