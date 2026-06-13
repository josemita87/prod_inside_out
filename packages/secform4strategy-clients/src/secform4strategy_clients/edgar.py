"""SEC EDGAR HTTP client.

Encapsulates how to talk to SEC EDGAR: the required ``User-Agent`` header, a
default timeout, polite rate-limiting, and the EDGAR-specific file formats (e.g.
the quarterly master index). It does NOT hold service business logic — filtering
by form type, deriving keys/timestamps, and publishing are the caller's domain.
"""

import logging
import time

logger = logging.getLogger(__name__)


class EdgarClient:
    """Perform HTTP GETs against SEC EDGAR with the required headers.

    Attributes:
        headers: Request headers sent with every GET (includes the SEC User-Agent).
        timeout: Default per-request timeout in seconds.
    """

    #: EDGAR current-filings page used to discover the newest Form 4 links.
    LIVE_FILINGS_URL = (
        'https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=4&owner=include&count=100&action=getcurrent'
    )

    def __init__(
        self,
        user_agent: str | None = None,
        headers: dict | None = None,
        timeout: int = 10,
    ) -> None:
        """Configure the client's headers and default timeout.

        Args:
            user_agent: Value for the ``User-Agent`` header (SEC requires one).
                Ignored if ``headers`` is given.
            headers: Full headers dict to use verbatim; overrides ``user_agent``.
            timeout: Default request timeout in seconds.
        """
        # Lazy import so the SDK is only required when this client is built.
        import requests

        self._requests = requests
        if headers is not None:
            self.headers = dict(headers)
        else:
            self.headers = {'Accept-Encoding': 'gzip, deflate', 'Host': 'www.sec.gov'}
            if user_agent:
                self.headers['User-Agent'] = user_agent
        self.timeout = timeout

    def get(self, url: str, timeout: int | None = None):
        """GET a URL with the configured headers.

        Args:
            url: The full URL to request.
            timeout: Optional per-request timeout override (seconds).

        Returns:
            The raw ``requests.Response`` (caller reads ``.text``/``.content``/etc.).
        """
        return self._requests.get(url, headers=self.headers, timeout=self.timeout if timeout is None else timeout)

    def fetch_master_index(self, year, quarter, throttle: float = 1.0):
        """Fetch and parse an EDGAR quarterly master index.

        Knows the master.idx URL pattern and the file's pipe-delimited format
        (a preamble followed by a ``...|...`` header, then one filing per line
        with fields ``cik|company|form_type|date|file_path``). Callers get a
        DataFrame of all filings and apply their own form-type filtering.

        Args:
            year: Calendar year of the master index.
            quarter: Quarter identifier (e.g. ``"QTR1"``).
            throttle: Seconds to sleep after a successful fetch, to respect SEC
                rate limits. Set to 0 to disable.

        Returns:
            A DataFrame of filing records, or ``None`` if the request was not 200.
        """
        from io import BytesIO

        import pandas as pd

        url = f'https://www.sec.gov/Archives/edgar/full-index/{year}/{quarter}/master.idx'
        response = self.get(url)
        if response.status_code != 200:
            return None

        lines = response.content.decode('utf-8').splitlines()

        # Crop the preamble: data starts two lines after the header row.
        start_index = 0
        for i, line in enumerate(lines):
            if '|' in line:
                start_index = i + 2
                break

        data = BytesIO('\n'.join(lines[start_index:]).encode('utf-8'))
        df = pd.read_csv(
            data,
            sep='|',
            header=None,
            names=['cik', 'company', 'form_type', 'date', 'file_path'],
            dtype=str,
            encoding='utf-8',
        )

        if throttle:
            time.sleep(throttle)
        return df

    def fetch_live_links(self, num_pages: int, wait_time: int = 10) -> set:
        """Scrape the newest Form 4 filing links from EDGAR's current-filings page.

        Drives a headless browser over the paginated ``getcurrent`` results and
        collects relative ``.txt`` filing paths. This is SEC EDGAR interaction
        (infra); callers receive plain link strings and decide what to do with
        them. Requires the ``edgar-live`` extra (Selenium + BeautifulSoup).

        Args:
            num_pages: Number of paginated result pages to scrape.
            wait_time: Maximum seconds to wait for page elements to load.

        Returns:
            A set of relative ``.txt`` filing link paths.
        """
        import random

        from bs4 import BeautifulSoup
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        driver = self._configure_driver()
        driver.get(self.LIVE_FILINGS_URL)
        logger.debug('Opened SEC EDGAR current-filings page')

        wait = WebDriverWait(driver, wait_time)
        all_links: set = set()

        for _ in range(num_pages):
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href]')))

                # Light human-like scrolling to reduce bot detection.
                for _ in range(random.randint(1, 3)):
                    driver.execute_script(f'window.scrollBy(0, {random.randint(100, 300)})')
                    time.sleep(random.uniform(0.5, 1.5))

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                links = {
                    a['href'].replace('/Archives/', '') if a['href'].startswith('/Archives') else a['href']
                    for a in soup.find_all('a', href=True)
                    if a['href'].endswith('.txt')
                }
                all_links.update(links)

                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next 100']")))
                next_button.click()
                logger.debug("Clicked 'Next 100' button")

            except Exception as e:
                logger.debug(f'Collected {len(all_links)} links. Exception: {e}')
                return all_links

        driver.quit()
        return all_links

    def _configure_driver(self):
        """Create a masked headless Chromium WebDriver for EDGAR scraping."""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        )
        chrome_options.binary_location = '/usr/bin/chromium'

        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Mask Selenium and apply the SEC headers.
        driver.execute_cdp_cmd(
            'Page.addScriptToEvaluateOnNewDocument',
            {'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': self.headers})
        return driver
