"""Entry point that runs the inference pipeline end to end."""

import logging
from logging.handlers import RotatingFileHandler

from config import config

# import alpaca
from inference_pipeline import InferencePipeline

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(config.log_path, maxBytes=10 * 1024 * 1024, backupCount=5),
    ],
)
logger = logging.getLogger(__name__)

COLUMNS_TO_DROP = config.columns_to_drop
IDENTIFICATION_FEATURES = config.identification_features
TARGET_FEATURE = config.target_feature

if __name__ == '__main__':
    # Instantiate the inference pipeline
    inference_pipeline = InferencePipeline()

    # Get account information
    # account = alpaca.get_account()

    # Load the saved model for inference
    model = inference_pipeline.load_model(model_path=config.model_path)

    # Fetch data from source (if hopsworks_connect = True, csv path is ignored)
    inference_data = inference_pipeline.fetch_inference_data(inference_data_path=config.csv_path)

    # Drop unnecessary columns
    predictive_data = inference_pipeline.preprocess_data(
        inference_data=inference_data, columns_to_drop=config.columns_to_drop
    )

    # Define the scaling features
    features = [col for col in predictive_data.columns.tolist() if col not in config.identification_features]
    # Scale the inference data
    scaled_data = inference_pipeline.scale_features(data=predictive_data, features_to_scale=features)

    # Generate predictions using the loaded model
    predictions_df = inference_pipeline.generate_predictions(
        model=model, scaled_data=scaled_data, original_data=inference_data
    )

    assert predictions_df.drop(columns=['predictions']).equals(predictive_data.reset_index(drop=True)), (
        'Rows are not perfectly aligned'
    )
    # Execute short trades based on predictions and config.threshold
    inference_data.execute_trades(predictions_df, config.prediction_threshold)
