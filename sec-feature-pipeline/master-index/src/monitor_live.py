from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from loguru import logger
import random


class SECLinkMonitor:
    def __init__(self, num_pages: int):
        self.url = "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=4&owner=include&count=100&action=getcurrent"
        self.num_pages = num_pages  
        self.headers = {
            "User-Agent": "CompanyE InvestmentServices admin@companye.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        }

    def _random_human_interaction(self, driver):
        """Simulate random human-like interactions."""
        # Random scrolling
        for _ in range(random.randint(1, 3)):
            driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)})")
            time.sleep(random.uniform(0.5, 1.5))

    def _configure_driver(self):
        """Set up WebDriver with advanced masking."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")  # Required in Docker
        chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent crashes in Docker
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        )

        # Specify the path to Chromium browser and chromedriver
        chrome_bin_path = "/usr/bin/chromium"
        chromedriver_path = "/usr/bin/chromedriver"

        # Set the binary location of Chromium
        chrome_options.binary_location = chrome_bin_path

        # Create a Service object for chromedriver
        service = Service(executable_path=chromedriver_path)

        # Initialize WebDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Mask Selenium by disabling navigator.webdriver
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
                """
            },
        )

        # Add custom headers
        driver.execute_cdp_cmd(
            "Network.setExtraHTTPHeaders", {"headers": self.headers}
        )

        return driver

    def parse_links(self, wait_time: int = 10) -> set:
        driver = self._configure_driver()
        # Open the webpage
        driver.get(self.url)
        logger.debug("Opened SEC Edgar")

        # Set up WebDriverWait
        wait = WebDriverWait(driver, wait_time)
        all_links = set()

        # Scrape and paginate through num_pages pages
        for _ in range(self.num_pages):
            try:
                # Wait for .txt links to be present on the page before scraping
                wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href]"))
                )

                # Simulate random human interaction
                self._random_human_interaction(driver)

                # Parse the page with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, "html.parser")
                links = {
                    a["href"].replace("/Archives/", "") if a["href"].startswith("/Archives") else a["href"]
                    for a in soup.find_all("a", href=True)
                    if a["href"].endswith(".txt")
                }
              
                all_links.update(links)
                
                # Look for the "Next 100" button and click it
                next_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@value='Next 100']"))
                )
                next_button.click()
                logger.debug("Clicked 'Next 100' button")

            except Exception as e:
                # Handle the case where the "Next" button is not found or another error occurs
                logger.debug(f"Collected {len(all_links)} links. Exception: {e}")
                return all_links

        # Clean up
        driver.quit()
        return all_links

    