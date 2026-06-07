"""Data loading and feature preprocessing helpers for training."""

import logging

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)


def scale_features(data: pd.DataFrame, features_to_scale: list[str]) -> pd.DataFrame:
    """Scale continuous features and encode categorical features.

    Args:
        data: Input DataFrame containing both features to transform and
            identification columns.
        features_to_scale: Names of columns to scale or encode; remaining
            columns are treated as identification features.

    Returns:
        A DataFrame with the scaled and encoded features concatenated with
        the untouched identification columns.
    """
    # Scale only "features_to_scale". The remaining are for identification
    X = data.copy()[features_to_scale]

    # Identify continuous and categorical columns
    continuous_cols = X.select_dtypes(include=['float64', 'int64']).columns
    categorical_cols = X.select_dtypes(include=['bool', 'category', 'object']).columns

    # Define transformers for continuous and categorical features
    transformers = [
        ('num', StandardScaler(), continuous_cols),
        ('cat', OneHotEncoder(drop='if_binary'), categorical_cols),
    ]

    # Create a ColumnTransformer
    preprocessor = ColumnTransformer(transformers)

    X_processed = preprocessor.fit_transform(X)

    scaled_data = pd.DataFrame(X_processed, columns=features_to_scale)

    # Add the identification features back to the processed data
    X_identification = data.drop(columns=features_to_scale)
    return pd.concat([scaled_data, X_identification], axis=1)


def load_and_preprocess_data(feature_store: str, columns_to_drop: list) -> pd.DataFrame:
    """Load data and prepare it for training with H2O.

    Args:
        feature_store: Feature store connection exposing ``fetch_RT4``.
        columns_to_drop: Column names to remove from the loaded data when
            present.

    Returns:
        A DataFrame with the unnecessary columns dropped.
    """
    # Load the data
    data = feature_store.fetch_RT4()

    # Drop unnecessary columns if they exist
    columns_to_drop = [col for col in columns_to_drop if col in data.columns]
    data.drop(columns=columns_to_drop, inplace=True)

    return data
