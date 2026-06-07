"""H2O AutoML wrapper for training and prediction."""

import logging

import h2o
import pandas as pd
from h2o.automl import H2OAutoML

logger = logging.getLogger(__name__)


class AutoML:
    """Wrapper around H2O AutoML for regression and classification tasks.

    Attributes:
        max_runtime_secs: Maximum AutoML runtime in seconds.
        seed: Random seed for reproducibility.
        ratio: Train/test split ratio.
        automl: The underlying H2OAutoML instance.
        best_model: The leader model after training, or None before training.
    """

    def __init__(
        self,
        max_runtime_secs: int = 10,
        seed: int = 1,
        ratio: float = 0.95,
    ):
        """Initialize the H2O cluster and AutoML instance.

        Args:
            max_runtime_secs: Maximum AutoML runtime in seconds. Defaults to 10.
            seed: Random seed for reproducibility. Defaults to 1.
            ratio: Train/test split ratio. Defaults to 0.95.
        """
        self.max_runtime_secs = max_runtime_secs
        self.seed = seed
        self.ratio = ratio

        # Initialize H2O cluster
        h2o.init()

        # Initialize H2O AutoML
        self.automl = H2OAutoML(max_runtime_secs=self.max_runtime_secs, seed=self.seed)

        # Initialize best model attribute
        self.best_model = None

    def train_classifier(
        self,
        data: h2o.frame,
        target: str,
        features: list[str],
    ):
        """Train an AutoML classifier using H2O on training data.

        Args:
            data: H2OFrame containing the training data.
            target: Name of the target column to predict.
            features: Names of the columns to use as predictors.
        """
        logger.info('Training AutoML classifier...')

        # Initialize H2O AutoML
        automl = H2OAutoML(max_runtime_secs=self.max_runtime_secs, seed=self.seed)

        # Train the model
        automl.train(x=features, y=target, training_frame=data)

        # Set the classifier
        self.classifier = automl
        logger.info('AutoML classifier trained successfully.')

    def train_regressor(self, data: h2o.frame, target: str, features: list[str]):
        """Train an AutoML regressor using H2O.

        Args:
            data: H2OFrame containing the training data.
            target: Name of the target column to predict.
            features: Names of the columns to use as predictors.
        """
        logger.info('Training AutoML regressor...')

        # Train the model
        self.automl.train(x=features, y=target, training_frame=data)

        # Save the best model
        self.best_model = self.automl.leader

    def classify(self, data: h2o.frame) -> pd.DataFrame:
        """Classify the data using the trained classifier.

        Args:
            data: H2OFrame containing the data to classify.

        Returns:
            A DataFrame of the classifier's predictions.

        Raises:
            ValueError: If the classifier has not been trained.
        """
        if self.classifier is None:
            raise ValueError('Classifier has not been trained.')

        # Make predictions
        predictions = self.classifier.predict(data)
        # Return predictions as a pandas DataFrame
        return predictions.as_data_frame()

    def predict_shorts(self, data: h2o.frame) -> pd.DataFrame:
        """Predict the magnitude of negative returns using the trained regressor.

        Args:
            data: H2OFrame containing the data to predict on.

        Returns:
            A DataFrame of the regressor's predictions.

        Raises:
            ValueError: If the regressor has not been trained.
        """
        if self.best_model is None:
            raise ValueError('Regressor has not been trained.')

        # Make predictions
        predictions = self.best_model.predict(data)

        # Return predictions as a pandas DataFrame
        return predictions.as_data_frame()
