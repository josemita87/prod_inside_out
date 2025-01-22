from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from loguru import logger
import time

class SECLinkMonitor:
    def __init__(self, check_interval:int=60):
        self.url = "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=4&owner=include&count=100&action=getcurrent"
        self.check_interval = check_interval
        self.seen_links = set()

    def parse_unseen_links(self, wait_time:int=10) -> set:
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")  # Required in Docker
        chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent crashes in Docker

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Open the webpage
        driver.get(self.url)
        logger.debug("Opened SEC Edgar")

        # Set up WebDriverWait to wait for elements
        wait = WebDriverWait(driver, wait_time)
        all_links = set()

        # Scrape and paginate through the results
        while True:
            try:
                # Wait for .txt links to be present on the page before scraping
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href]")))
                
                # Parse the page with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                links = {a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.txt')}
                all_links.update(links)

                # Check if any of the links have already been seen
                for link in all_links: 
                    if link in self.seen_links:
                        all_links.remove(link)
                        logger.info(f"Link {link} has already been seen. Stopping scraping.")
                        break

                # Look for the "Next 100" button and click it
                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next 100']")))
                next_button.click()

            except Exception as e:
                # Handle the case where the "Next" button is not found or another error occurs
                logger.debug(f"Collected {len(all_links)} links.") 
                break

            # Clean up
            driver.quit()
            return all_links
        
    def monitor(self):
        while True:
            print("Checking for updates...")
            new_links = self.parse_unseen_links()

            if new_links:
                self.seen_links.update(new_links)
                yield from new_links

            else:
                print("No new links.")
            time.sleep(self.check_interval)

