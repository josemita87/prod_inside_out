Inference Feature Pipeline

This project is designed to manage the inference feature pipeline, encompassing data fetching, preprocessing, feature store management, and prediction generation. The pipeline is containerized using Docker Compose to orchestrate multiple microservices, each responsible for distinct stages of the process.

Table of Contents

Project Structure

Prerequisites

Environment Variables

Setup and Installation

Running the Pipeline

Stopping the Pipeline

Services

Configuration

System Modes

Contributing

License

Project Structure

The project is structured as follows:

📂 inference-feature-pipeline
│-- 📂 services
│   │-- 📂 sec-feature-pipeline
│   │   ├── master-index
│   │   ├── scraper
│   │   ├── kafka-to-store
│   │-- 📂 prices-feature-pipeline
│   │   ├── yahoo-connect
│   │   ├── target
│   │-- 📂 training-pipeline
│   │   ├── training
│   │-- 📂 inference-pipeline
│   │   ├── inference
│-- 📂 configs
│-- 📂 env
│-- 📂 scripts
│-- Dockerfile
│-- docker-compose.yml

Prerequisites

To run this pipeline, ensure the following dependencies are installed:

Docker (latest stable version)

Docker Compose (latest stable version)

Python 3.8+

Poetry (for dependency management)

Hopsworks API Key (for secure access to the feature store)

Environment Variables

The project relies on environment variable files (.env) to configure various settings. These include API keys, database credentials, and feature store configurations. Each pipeline mode (detailed below) has a corresponding .env file to define its behavior.

Services

SEC Feature Pipeline

master-index

Fetches links from the SEC to supply to the scraper.

Ensures up-to-date and complete indexing of available data sources.

scraper

Extracts and processes data from SEC Form 4 filings.

Cleans and structures the extracted data for downstream processing.

kafka-to-store

Reads messages from Kafka and ingests them into the Hopsworks Feature Store.

Handles error management and ensures data consistency.

Prices Feature Pipeline

yahoo-connect

Retrieves unique stock tickers from the feature store.

Fetches real-time and historical price data from Yahoo Finance.

target

Aggregates price and transaction data according to a schema defined in config.py.

Computes pct_change in stock price over a specified period post-transaction.

Derives an additional feature, average_pct_change, by analyzing historical data for the same ticker.

Stores the aggregated and computed features back into the feature store.

Training Pipeline

training

Fetches labeled training data from the feature store.

Trains an ML model to predict pct_change based on selling transactions.

Optimizes model performance through hyperparameter tuning and validation.

Saves the trained model for inference.

Inference Pipeline

Retrieves the most recent data from the feature store.

Loads the trained ML model to generate predictions.

Outputs predictions to a specified destination for further use.

System Modes

The system operates in three modes, each corresponding to a different execution workflow:

1. System Load

Responsible for initial data ingestion and processing.

Executes all required microservices to ensure the feature store is populated with essential data.

2. System Update

Periodically updates the existing datasets with new information.

Ensures the model remains current with the latest market and transaction data.

3. System Inference

Runs the inference pipeline using the most recent data.

Produces predictions based on the trained ML model.

Each mode is configured via a dedicated .env file, defining service-specific parameters and execution rules.

Contributing

Contributions are welcome! To contribute:

Fork the repository.

Create a feature branch (git checkout -b feature-branch).

Commit your changes (git commit -m 'Add new feature').

Push to the branch (git push origin feature-branch).

Open a Pull Request for review.

License

This project is licensed under the MIT License. See the LICENSE file for details.

