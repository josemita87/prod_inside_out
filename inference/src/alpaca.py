"""Alpaca brokerage API wrapper for account access and order placement."""

import logging

import alpaca_trade_api as tradeapi
from config import config

logger = logging.getLogger(__name__)


class AlpacaAPI:
    """Client wrapper around the Alpaca REST trading API.

    Attributes:
        api: The authenticated Alpaca REST client.
    """

    def __init__(self):
        """Initialize the Alpaca REST client from configuration credentials."""
        self.api = tradeapi.REST(config.API_KEY, config.API_SECRET, config.BASE_URL, api_version='v2')
        logger.info('Initialized Alpaca API')

    def get_account(self):
        """Retrieve account information from Alpaca.

        Returns:
            The Alpaca account object.
        """
        account = self.api.get_account()
        logger.info(f'Account status: {account.status}')
        return account

    def place_order(self, symbol, qty, side, order_type, time_in_force):
        """Submit an order to Alpaca.

        Args:
            symbol: Ticker symbol to trade.
            qty: Number of shares to trade.
            side: Order side, e.g. ``"buy"`` or ``"sell"``.
            order_type: Order type, e.g. ``"market"``.
            time_in_force: Time-in-force policy, e.g. ``"gtc"``.

        Returns:
            The submitted order object, or ``None`` if submission failed.
        """
        try:
            order = self.api.submit_order(
                symbol=symbol, qty=qty, side=side, type=order_type, time_in_force=time_in_force
            )
            logger.info(f'Order submitted: {order}')
            return order

        except Exception as e:
            logger.error(f'Failed to place order: {e}')
            return None
