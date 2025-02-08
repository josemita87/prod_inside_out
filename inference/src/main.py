import os

#import alpaca
from inference_pipeline import InferencePipeline
from loguru import logger
from config import config

# Configure structured logging
logger.add(config.log_path, format="{time} {level} {message}", level="DEBUG", rotation="10 MB")

COLUMNS_TO_DROP = config.columns_to_drop
IDENTIFICATION_FEATURES = config.identification_features
TARGET_FEATURE = config.target_feature

if __name__ == "__main__":

    # Instantiate the inference pipeline
    inference_pipeline = InferencePipeline()

    # Get account information
    #account = alpaca.get_account()

    # Load the saved model for inference
    model = inference_pipeline.load_model(
        model_path=config.model_path
    )

    # Fetch data from source (if hopsworks_connect = True, csv path is ignored)
    inference_data = inference_pipeline.fetch_inference_data(
        inference_data_path=config.csv_path
    )

    # Drop unnecessary columns
    predictive_data = inference_pipeline.preprocess_data(
        inference_data=inference_data,
        columns_to_drop=config.columns_to_drop
    )
    
    # Define the scaling features
    features = [
        col for col in predictive_data.columns.tolist() \
            if col not in config.identification_features
    ]
    # Scale the inference data
    scaled_data = inference_pipeline.scale_features(
        data = predictive_data,
        features_to_scale=features
    )

    # Generate predictions using the loaded model
    predictions_df = inference_pipeline.generate_predictions(
        model=model, 
        scaled_data=scaled_data, 
        original_data=inference_data
    )
   
    breakpoint()
    assert predictions_df.drop(columns=['predictions']).equals(
        predictive_data.reset_index(drop=True)
    ), "Rows are not perfectly aligned"
    breakpoint()
    # Execute short trades based on predictions and config.threshold
    inference_data.execute_trades(predictions_df, config.prediction_threshold)


