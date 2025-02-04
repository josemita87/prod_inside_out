import alpaca_trade_api as tradeapi

print("Alpaca Trade API imported successfully.")

from alpaca_trade_api.rest import REST as tradeapi
from feature_store import FeatureStoreConnection
from loguru import logger
import h2o
import pandas as pd
import os
from config import config

# Configure structured logging
logger.add(config.log_path, format="{time} {level} {message}", level="DEBUG", rotation="10 MB")

class AlpacaAPI:
    def __init__(self):
        self.api = tradeapi.REST(config.API_KEY, config.API_SECRET, config.BASE_URL, api_version='v2')
        logger.info("Initialized Alpaca API")

    def get_account(self):
        """Get account information."""
        account = self.api.get_account()
        logger.info(f"Account status: {account.status}")
        return account

    def place_order(self, symbol, qty, side, order_type, time_in_force):
        """Place an order."""
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force
            )
            logger.info(f"Order submitted: {order}")
            return order
        
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None
