"""Enrich SEC transactions with market cap, exchange and SIC code data."""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Generator, List

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class ApiHandler:
    """Enrich transactions with market cap, exchange and SIC data from local and external sources.

    Attributes:
        transactions: The transactions to enrich, paired with their offsets.
        mcaps: DataFrame of market caps loaded from the mcaps parquet file.
        mcaps_path: Path to the market caps parquet file.
        mapper: Mapping dictionary loaded from the mapper JSON file.
        failed_mcaps_path: Path where transactions with missing market caps are recorded.
        failed_date_path: Path where transactions with missing dates are recorded.
        failed_sic_path: Path where transactions with missing SIC codes are recorded.
        failed_exchange_path: Path where transactions with missing exchanges are recorded.
        buffer_size: Number of enriched transactions to accumulate before returning.
    """

    def __init__(
        self,
        transactions: List[Dict],
        mcaps_path: str,
        mapper_path: str,
        failed_mcaps_path: str,
        failed_date_path: str,
        failed_sic_path: str,
        failed_exchange_path: str,
        buffer_size: int,
    ) -> None:
        """Initialize the handler and load the market caps and mapper data.

        Args:
            transactions: Transactions to enrich, paired with their offsets.
            mcaps_path: Path to the market caps parquet file.
            mapper_path: Path to the mapper JSON file.
            failed_mcaps_path: Path for recording transactions with missing market caps.
            failed_date_path: Path for recording transactions with missing dates.
            failed_sic_path: Path for recording transactions with missing SIC codes.
            failed_exchange_path: Path for recording transactions with missing exchanges.
            buffer_size: Number of enriched transactions to accumulate before returning.
        """
        self.transactions = transactions
        self.mcaps = pd.read_parquet(mcaps_path)
        self.mcaps_path = mcaps_path
        self.mapper = json.load(open(mapper_path))
        self.failed_mcaps_path = failed_mcaps_path
        self.failed_date_path = failed_date_path
        self.failed_sic_path = failed_sic_path
        self.failed_exchange_path = failed_exchange_path
        self.buffer_size = buffer_size

    def get_enriched_data(self) -> Generator[Dict, None, None]:
        """Enrich buffered transactions with market cap, exchange and SIC data.

        Returns:
            A list of enriched transaction and offset tuples, returned once the
            buffer reaches the configured size or after the input is exhausted.
        """
        buffer = []
        for tx, offset in self.transactions:
            tx['market_cap'] = self._get_market_cap(tx)
            tx['exchange'] = self._get_exchange(tx)
            tx['sic'] = self._get_sic(tx)

            buffer.append((tx, offset))

            if len(buffer) >= self.buffer_size:
                return buffer

        # Yield the remaining transactions
        if buffer:
            return buffer

    def _get_market_cap(self, tx: dict) -> int:
        """Return the market capitalization for the transaction's ticker and filing date.

        Filing dates on or after 2024-09-01 are looked up via Yahoo Finance and
        appended to the local market caps file; earlier dates are looked up directly
        in the local file. Failures are recorded in the relevant failed dataset.

        Args:
            tx: Transaction dictionary containing at least ``date`` and ``ticker``.

        Returns:
            The market capitalization as an integer, or None if it cannot be resolved.
        """
        # Get the first business day of the month of the transaction date
        try:
            _date = datetime.strptime(tx.get('date'), '%Y-%m-%d').date()
            fbd = pd.date_range(start=_date.replace(day=1), periods=1, freq='BMS')[0].date()

        except (ValueError, TypeError):
            fbd = None
            self._log_error(tx, self.failed_date_path, 'missing_date')

        # If the filing date is recent, query Yahoo Finance & append to the local dataset
        if fbd:
            if fbd >= datetime(2024, 9, 1).date():
                ticker = tx.get('ticker')
                try:
                    mcap = yf.Ticker(ticker.info.get('marketCap'))

                    pd.DataFrame([[ticker, mcap, fbd]], columns=['ticker', 'mcap', 'date']).to_parquet(
                        self.mcaps_path, engine='pyarrow', append=True
                    )

                    return mcap
                except:
                    return None
        # Otherwise, look up the value directly in the local dataset
        try:
            row = self.mcaps[(self.mcaps['ticker'] == tx.get('ticker').upper()) & (self.mcaps['fbd'] == fbd)]
            return int(row['marketcap'].iloc[0])

        # In case it fails, record it in the failed dataset
        except:
            self._log_error(tx, self.failed_mcaps_path, 'missing_mcap')

    def _get_exchange(self, tx: dict) -> str:
        """Return the exchange for the transaction, falling back to Yahoo Finance.

        The exchange is first looked up in the mapper by company CIK, and on failure
        a Yahoo Finance lookup by ticker is attempted. Failures are recorded.

        Args:
            tx: Transaction dictionary containing at least ``company_cik`` and ``ticker``.

        Returns:
            The exchange identifier, or None if it cannot be resolved.
        """
        try:
            return self.mapper['exchange'].get(tx.get('company_cik'), None)
        except:
            try:
                ticker = yf.Ticker(tx.get('ticker'))
                return ticker.info.get('exchange')

            except:
                self._log_error(tx, self.failed_exchange_path, 'missing_exchange')

    def _get_sic(self, tx: dict) -> str:
        """Return the SIC code for the transaction by looking it up in the mapper.

        Failures are recorded in the failed SIC dataset.

        Args:
            tx: Transaction dictionary containing at least ``company_cik``.

        Returns:
            The SIC code, or None if it cannot be resolved.
        """
        try:
            return self.mapper['sic'].get(tx.get('company_cik'), None)
        except:
            self._log_error(tx, self.failed_sic_path, 'missing_sic')

    def _log_error(self, tx: dict, path: str, error: str) -> None:
        """Append the transaction to the failed dataset matching the error type.

        Args:
            tx: The transaction that failed enrichment.
            path: Path to the parquet file where the failure should be recorded.
            error: The error category, one of ``missing_mcap``, ``missing_date``,
                ``missing_sic`` or ``missing_exchange``.
        """

        # logger.error(f"Error: {error} for transaction")
        def append_to_parquet(path: str, data: pd.DataFrame) -> None:
            """Append rows to a parquet file, creating it if it does not yet exist.

            Args:
                path: Path to the parquet file to write to.
                data: Rows to append to the file.
            """
            if os.path.exists(path) and os.path.getsize(path) > 0:
                existing_data = pd.read_parquet(path)
                updated_data = pd.concat([existing_data, data], ignore_index=True)
            else:
                updated_data = data
            updated_data.to_parquet(path, index=False)

        if error == 'missing_mcap':
            try:
                _date = datetime.strptime(tx.get('date'), '%Y-%m-%d').date()
                fbd = pd.date_range(start=_date.replace(day=1), periods=1, freq='BMS')[0].date()
                failed_data = pd.DataFrame([[tx.get('ticker').upper(), fbd]], columns=['ticker', 'date'])
                append_to_parquet(path, failed_data)

            except:
                self._log_error(tx, self.failed_date_path, 'missing_date')
        elif error == 'missing_date':
            failed_data = pd.DataFrame([tx.get('ticker').upper()], columns=['ticker'])
            append_to_parquet(path, failed_data)

        elif error in {'missing_sic', 'missing_exchange'}:
            failed_data = pd.DataFrame([tx.get('company_cik')], columns=['cik'])
            append_to_parquet(path, failed_data)
