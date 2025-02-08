import h2o
from h2o.automl import H2OAutoML
from loguru import logger
from sklearn.model_selection import train_test_split
import pandas as pd

class AutoML:
    def __init__(
        self, 
        max_runtime_secs:int=10, 
        seed:int=1,
        ratio:float=0.95,
        ):
        self.max_runtime_secs = max_runtime_secs
        self.seed = seed
        self.ratio=ratio
        
        # Initialize H2O cluster
        h2o.init()

        # Initialize H2O AutoML
        self.automl = H2OAutoML(
            max_runtime_secs=self.max_runtime_secs, 
            seed=self.seed
        )

        # Initialize best model attribute
        self.best_model = None

    def train_classifier(
        self, 
        data:h2o.frame, 
        target:str, 
        features:list[str],
        ):
        """Train an AutoML classifier using H2O on training data."""
        logger.info("Training AutoML classifier...")
        
        # Initialize H2O AutoML
        automl = H2OAutoML(max_runtime_secs=self.max_runtime_secs, seed=self.seed)
        
        # Train the model
        automl.train(x=features, y=target, training_frame=data)
        
        # Set the classifier
        self.classifier = automl
        logger.info("AutoML classifier trained successfully.")

    def train_regressor(
        self, 
        data:h2o.frame, 
        target:str, 
        features:list[str]
    ):

        """Train an AutoML regressor using H2O."""
        logger.info("Training AutoML regressor...")
        
        # Train the model
        self.automl.train(
            x=features, 
            y=target, 
            training_frame=data
        )

        # Save the best model
        self.best_model = self.automl.leader


    def classify(self, data:h2o.frame) -> pd.DataFrame:
        """Classify the data using the trained classifier."""
        if self.classifier is None:
            raise ValueError("Classifier has not been trained.")

        # Make predictions
        predictions = self.classifier.predict(data)
        breakpoint()
        # Return predictions as a pandas DataFrame
        return predictions.as_data_frame()

    def predict_shorts(self, data:h2o.frame) -> pd.DataFrame:
        """Predict the magnitude of negative returns using the trained regressor."""
        if self.best_model is None:
            raise ValueError("Regressor has not been trained.")

        # Make predictions
        predictions = self.best_model.predict(data)
        
        # Return predictions as a pandas DataFrame
        return predictions.as_data_frame()