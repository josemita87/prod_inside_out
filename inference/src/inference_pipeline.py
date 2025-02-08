from alpaca import AlpacaAPI
from feature_store import FeatureStoreConnection
from loguru import logger
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import h2o
import pandas as pd
import numpy as np
from config import config

# Configure structured logging
logger.add(config.log_path, format="{time} {level} {message}", level="DEBUG", rotation="10 MB")

class InferencePipeline:
    def __init__(self):
        #self.alpaca_api = AlpacaAPI()
        self.feature_store = FeatureStoreConnection() 
        h2o.init()
        logger.info("Initialized H2O API")

    def load_model(self, model_path) -> h2o.model.model_base.ModelBase:
        """Load the H2O model from the specified path."""
        model = h2o.load_model(model_path)
        logger.info(f"Loaded model from: {model_path}")
        return model

    def fetch_inference_data(self, inference_data_path) -> pd.DataFrame:
        """Fetch new inference data from a CSV file or feature store."""
        if config.hopsworks_connect:
            inference_data = self.feature_store.fetch_new_trades()
            logger.info(f"Loaded inference data from feature store")
        else:
            inference_data = pd.read_csv(inference_data_path)
            logger.info(f"Loaded inference data from: {inference_data_path}")

        return inference_data

    def preprocess_data(self, inference_data, columns_to_drop) -> pd.DataFrame: 
        """Preprocess the inference data to match the training data structure."""
        
        # Drop other unnecessary features
        inference_data.drop(columns=columns_to_drop, inplace=True)
   
        return inference_data
    
    def scale_features(
            self, 
            data: pd.DataFrame, 
            features_to_scale: list[str]
        ) -> pd.DataFrame:
        """Scale continuous features and encode categorical features."""

        # Scale only "features_to_scale". The remaining are for identification
        X = data.copy()[features_to_scale]

        # Identify continuous and categorical columns
        continuous_cols = X.select_dtypes(include=['float64', 'int64']).columns
        categorical_cols = X.select_dtypes(include=['bool', 'category', 'object']).columns
        
        # Define transformers for continuous and categorical features
        transformers = [
            ('num', StandardScaler(), continuous_cols),
            ('cat', OneHotEncoder(drop="if_binary"), categorical_cols)
        ]
        
        # Create a ColumnTransformer
        preprocessor = ColumnTransformer(transformers)
    
        X_processed = preprocessor.fit_transform(X)
        breakpoint()
        scaled_data = pd.DataFrame(X_processed, columns=features_to_scale)               
        
        # Add the identification features back to the processed data
        X_identification = data.drop(columns=features_to_scale)
        return pd.concat([scaled_data, X_identification], axis=1)


    def generate_predictions(self, model, scaled_data, original_data) -> pd.DataFrame:
        """Generate predictions using the loaded model and concatenate them with the original data."""
        # Convert data to H2OFrame & Generate predictions
        h2o_inference_data = h2o.H2OFrame(scaled_data)
        predictions = model.predict(h2o_inference_data)

        # Convert predictions back to pandas using multi-threading
        predictions_df = predictions.as_data_frame(use_multi_thread=True)
        
        result_data = pd.concat([original_data, predictions_df], axis=1)
        
        return result_data

    def execute_trades(self, predictions_df, threshold):
        """Execute short trades based on predictions and threshold."""
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
                    logger.info(f"Order details: {order}")