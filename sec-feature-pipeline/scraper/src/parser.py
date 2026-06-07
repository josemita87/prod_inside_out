"""Parser that fetches SEC Form 4 filings and extracts transaction data from XML."""

import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Text

import requests
from transaction import EssentialTrade

logger = logging.getLogger(__name__)
# Get the absolute path to the 'scraper' directory


from const import derivative_paths, derivative_root, headers, insider_paths, paths, root


class Form4Parser:
    """Fetch a SEC Form 4 filing and parse its transactions from the embedded XML.

    Attributes:
        url: Full URL of the filing to fetch.
        xml: Parsed XML element tree of the filing, or None if fetching failed.
    """

    BASE_URL = 'https://www.sec.gov/Archives/'
    XML_DELIM = r'<XML>\s*(<\?xml[^>]+?>.*?)</XML>'
    ROOT = root
    DERIVATIVE_ROOT = derivative_root
    INSIDER_PATHS = insider_paths
    PATHS = paths
    DERIVATIVE_PATHS = derivative_paths
    HEADERS = headers

    def __init__(self, url: str, sleep_time: int = 0.1):
        """Initialize the parser, throttle, and fetch the filing XML.

        Args:
            url: Filing path appended to the archives base URL.
            sleep_time: Seconds to sleep before fetching, to throttle requests.
        """
        self.url = self.BASE_URL + url
        time.sleep(sleep_time)
        self.xml = self.get_filing()

    def get_filing(self) -> Text:
        """Fetch the filing and extract its embedded XML document.

        Returns:
            The parsed XML element on success, or None if fetching or parsing fails.
        """
        try:
            filing = requests.get(self.url, headers=headers).text
            return ET.fromstring(re.search(self.XML_DELIM, filing, re.DOTALL).group(1))

        except Exception:
            # logger.error(f"\n\nFailed to get filing: {e}, {self.url}\n\n")
            return None

    def create_txs(self) -> list[dict]:
        """Create a list of transactions for the filing.

        Initialize a list to store transactions as dicts, and query the XML for
        non-derivative and derivative transactions. For each individual
        transaction, create an EssentialTrade filled with _process_transaction().

        Returns:
            A list of transaction dicts, or None if the filing XML is missing.
        """
        filing_data = []

        if self.xml is None:
            return None

        params = [(self.ROOT, self.PATHS), (self.DERIVATIVE_ROOT, self.DERIVATIVE_PATHS)]

        # Get both non-derivative and derivative transactions
        for root, paths in params:
            # Find all transactions in the filing for the given root (derivative or non-derivative)
            for etree in self.xml.findall(root):
                # Populate the EssentialTrade object with the transaction data
                self.transaction = EssentialTrade(link=self.url, xml=self.xml)
                filing_data.append(
                    self._process_transaction(
                        etree,
                        paths,
                    )
                )

        return filing_data

    def _process_transaction(self, etree: ET.ElementTree, paths: dict) -> dict:
        """Populate the current transaction from insider and transaction paths.

        Args:
            etree: Element tree of a single transaction node.
            paths: Mapping of output keys to XML paths for the transaction.

        Returns:
            The populated transaction as a dictionary.
        """
        self._query_xml(self.xml, self.INSIDER_PATHS)
        self._query_xml(etree, paths)

        return self.transaction.to_dict()

    def _query_xml(self, etree: ET.ElementTree, paths: dict):
        """Query the given paths and set the corresponding transaction attributes.

        Args:
            etree: The ElementTree object to query.
            paths: A mapping where keys are the desired output keys and values
                are the paths to the values in the ElementTree.
        """
        for key, path in paths.items():
            try:
                element = etree.find(path)

                if element is not None:
                    if 'footnote_id' in key.lower():
                        setattr(self.transaction, key, element.get('id'))

                    else:
                        setattr(self.transaction, key, element.text)

            except AttributeError:
                pass
