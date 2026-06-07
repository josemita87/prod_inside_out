"""Inference pipeline for loading data, scaling features and generating trades."""

import logging

import h2o
import pandas as pd
from config import config
from feature_store import FeatureStoreConnection
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)


class InferencePipeline:
    """End-to-end inference pipeline for scoring trades and executing orders.

    Attributes:
        feature_store: Connection used to fetch inference data.
    """

    def __init__(self):
        """Initialize the feature store connection and the H2O cluster."""
        # self.alpaca_api = AlpacaAPI()
        self.feature_store = FeatureStoreConnection()
        h2o.init()
        logger.info('Initialized H2O API')

    def load_model(self, model_path) -> h2o.model.model_base.ModelBase:
        """Load the H2O model from the specified path.

        Args:
            model_path: Filesystem path to the saved H2O model.

        Returns:
            The loaded H2O model.
        """
        model = h2o.load_model(model_path)
        logger.info(f'Loaded model from: {model_path}')
        return model

    def fetch_inference_data(self, inference_data_path) -> pd.DataFrame:
        """Fetch new inference data from a CSV file or feature store.

        Args:
            inference_data_path: CSV path used when the feature store is disabled.

        Returns:
            A DataFrame of inference data.
        """
        if config.hopsworks_connect:
            inference_data = self.feature_store.fetch_new_trades()
            logger.info('Loaded inference data from feature store')
        else:
            inference_data = pd.read_csv(inference_data_path)
            logger.info(f'Loaded inference data from: {inference_data_path}')

        return inference_data

    def preprocess_data(self, inference_data, columns_to_drop) -> pd.DataFrame:
        """Preprocess the inference data to match the training data structure.

        Args:
            inference_data: The raw inference DataFrame to preprocess.
            columns_to_drop: Column names to drop from the data.

        Returns:
            The inference DataFrame with the specified columns removed.
        """
        # Drop other unnecessary features
        inference_data.drop(columns=columns_to_drop, inplace=True)

        return inference_data

    def scale_features(self, data: pd.DataFrame, features_to_scale: list[str]) -> pd.DataFrame:
        """Scale continuous features and encode categorical features.

        Args:
            data: The inference data containing features and identification columns.
            features_to_scale: Column names to scale or encode.

        Returns:
            A DataFrame with scaled/encoded features and identification columns.
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

    def generate_predictions(self, model, scaled_data, original_data) -> pd.DataFrame:
        """Generate predictions and concatenate them with the original data.

        Args:
            model: The H2O model used to score the data.
            scaled_data: The scaled/encoded feature data to predict on.
            original_data: The original data to concatenate with predictions.

        Returns:
            A DataFrame of the original data joined with model predictions.
        """
        # Convert data to H2OFrame & Generate predictions
        h2o_inference_data = h2o.H2OFrame(scaled_data)
        predictions = model.predict(h2o_inference_data)

        # Convert predictions back to pandas using multi-threading
        predictions_df = predictions.as_data_frame(use_multi_thread=True)

        result_data = pd.concat([original_data, predictions_df], axis=1)

        return result_data

    def execute_trades(self, predictions_df, threshold):
        """Execute short trades for predictions below the given threshold.

        Args:
            predictions_df: DataFrame of predictions with ticker symbols.
            threshold: Prediction value below which a short trade is placed.
        """
        for index, row in predictions_df.iterrows():
            if row['predictions'] < threshold:  # Condition for placing a short trade
                symbol = row['ticker'].astype(str).str.upper().str.strip()
                qty = config.qty
                side = config.side
                order_type = config.order_type
                time_in_force = config.time_in_force

                # Place the order
                order = self.alpaca_api.place_order(symbol, qty, side, order_type, time_in_force)
                if order:
                    logger.info(f'Order details: {order}')
