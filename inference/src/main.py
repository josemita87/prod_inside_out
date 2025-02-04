import os

#import alpaca
import inference_pipeline
from loguru import logger
from config import config

# Configure structured logging
logger.add(config.log_path, format="{time} {level} {message}", level="DEBUG", rotation="10 MB")

if __name__ == "__main__":

    # Instantiate the inference pipeline
    inference_pipeline = inference_pipeline.InferencePipeline()

    # Get account information
    #account = alpaca.get_account()

    # Load the saved model for inference
    model = inference_pipeline.load_model(config.model_path)

    # Fetch data from source (if hopsworks_connect = True, csv path is ignored)
    inference_data = inference_pipeline.fetch_inference_data(config.csv_path)

    # Preprocess the inference data
    inference_data = inference_pipeline.preprocess_data(inference_data)

    # Scale the inference data
    inference_data = inference_pipeline.scale_data(inference_data)

    # Generate predictions using the loaded model
    predictions_df = inference_pipeline.generate_predictions(model, inference_data)
    breakpoint()
    # Execute short trades based on predictions and config.threshold
    inference_data.execute_trades(predictions_df, config.prediction_threshold)


