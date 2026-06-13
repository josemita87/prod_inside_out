"""Parse SEC Form 4 filings: fetch a filing and extract transaction dicts from its XML."""

import logging
import re
import time
import xml.etree.ElementTree as ET

from const import derivative_paths, derivative_root, headers, insider_paths, paths, root
from secform4strategy_clients.edgar import EdgarClient
from transaction import EssentialTrade

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.sec.gov/Archives/'
XML_DELIM = r'<XML>\s*(<\?xml[^>]+?>.*?)</XML>'

# SEC EDGAR HTTP client, carrying the service's required headers.
edgar = EdgarClient(headers=headers)


def parse_filing(url: str, sleep_time: float = 0.1) -> list[dict] | None:
    """Fetch a Form 4 filing and parse its transactions from the embedded XML.

    Args:
        url: Filing path appended to the archives base URL.
        sleep_time: Seconds to sleep before fetching, to throttle requests.

    Returns:
        A list of transaction dicts, or None if the filing XML is missing.
    """
    full_url = BASE_URL + url
    time.sleep(sleep_time)
    filing_xml = _fetch_filing(full_url)

    if filing_xml is None:
        return None

    filing_data = []
    # Query both the non-derivative and derivative transaction blocks.
    for tx_root, tx_paths in [(root, paths), (derivative_root, derivative_paths)]:
        for etree in filing_xml.findall(tx_root):
            # One accumulator per transaction; insider fields live at the filing
            # root, transaction fields on the individual node.
            trade = EssentialTrade(link=full_url, xml=filing_xml)
            _query_xml(filing_xml, insider_paths, trade)
            _query_xml(etree, tx_paths, trade)
            filing_data.append(trade.to_dict())

    return filing_data


def _fetch_filing(full_url: str) -> ET.Element | None:
    """Fetch the filing and extract its embedded XML document.

    Returns:
        The parsed XML element on success, or None if fetching or parsing fails.
    """
    try:
        filing = edgar.get(full_url).text
        return ET.fromstring(re.search(XML_DELIM, filing, re.DOTALL).group(1))
    except Exception:
        return None


def _query_xml(etree: ET.Element, query_paths: dict, trade: EssentialTrade) -> None:
    """Set ``trade`` attributes from ``query_paths`` resolved against ``etree``.

    Args:
        etree: The element to query.
        query_paths: Mapping where keys are output attribute names and values are
            the XML paths to the corresponding values.
        trade: The transaction accumulator to populate in place.
    """
    for key, path in query_paths.items():
        element = etree.find(path)
        if element is None:
            continue

        if 'footnote_id' in key.lower():
            setattr(trade, key, element.get('id'))
        else:
            setattr(trade, key, element.text)
