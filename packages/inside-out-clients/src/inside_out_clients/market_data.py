"""Market-data client backed by yfinance.

Encapsulates the yfinance-specific knowledge callers would otherwise reach into
directly: which ``Ticker.info`` keys hold a market cap or an exchange. Callers ask
for a domain value (``market_cap``/``exchange``) rather than driving the SDK. It
does not catch errors — how to handle a missing value is the caller's domain.
"""


class MarketDataClient:
    """Look up market-data fields for a ticker via yfinance."""

    def __init__(self) -> None:
        """Bind the yfinance module."""
        # Lazy import so the SDK is only required when this client is built.
        import yfinance as yf

        self._yf = yf

    def market_cap(self, symbol: str):
        """Return the market capitalization for ``symbol`` (or None if absent)."""
        return self._yf.Ticker(symbol).info.get('marketCap')

    def exchange(self, symbol: str):
        """Return the listing exchange for ``symbol`` (or None if absent)."""
        return self._yf.Ticker(symbol).info.get('exchange')
