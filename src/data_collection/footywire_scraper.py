"""
FootyWire scraper for AFL player statistics and performance data.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FootyWireScraper:
    """
    FootyWire website scraper for AFL player statistics
    """
    
    def __init__(self, headless=True):
        self.base_url = "https://www.footywire.com"
        self.session = requests.Session()
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver setup successful")
            
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            raise
    
    def close_driver(self):
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_player_stats(self, year=2024, round_num=None, team=None):
        """
        Scrape player statistics from FootyWire
        """
        if not self.driver:
            self.setup_driver()
        
        try:
            # Navigate to AFL stats page
            url = f"{self.base_url}/afl/footy/ft_players"
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Find the main stats table
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            
            for table in tables:
                # Check if this is the player stats table
                headers = table.find_elements(By.TAG_NAME, "th")
                if len(headers) > 5:  # Likely a stats table
                    return self._parse_stats_table(table)
            
            logger.warning("No suitable stats table found")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error scraping player stats: {e}")
            return pd.DataFrame()
    
    def _parse_stats_table(self, table):
        """
        Parse a stats table from FootyWire
        """
        try:
            # Extract headers
            header_row = table.find_element(By.TAG_NAME, "tr")
            headers = [th.text.strip() for th in header_row.find_elements(By.TAG_NAME, "th")]
            
            # Extract data rows
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
            
            data = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= len(headers):
                    row_data = [cell.text.strip() for cell in cells[:len(headers)]]
                    data.append(row_data)
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=headers)
            
            # Clean numeric columns
            numeric_cols = ['Disposals', 'Marks', 'Tackles', 'Goals', 'Behinds', 
                          'Kicks', 'Handballs', 'Contested Possessions', 'Uncontested Possessions']
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"Parsed {len(df)} player records")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing stats table: {e}")
            return pd.DataFrame()
    
    def get_team_stats(self, year=2024):
        """
        Scrape team statistics
        """
        if not self.driver:
            self.setup_driver()
        
        try:
            url = f"{self.base_url}/afl/footy/ft_team_stats?year={year}"
            self.driver.get(url)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            
            for table in tables:
                headers = table.find_elements(By.TAG_NAME, "th")
                if len(headers) > 3:  # Team stats table
                    return self._parse_team_table(table)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error scraping team stats: {e}")
            return pd.DataFrame()
    
    def _parse_team_table(self, table):
        """
        Parse team statistics table
        """
        try:
            # Extract headers
            header_row = table.find_element(By.TAG_NAME, "tr")
            headers = [th.text.strip() for th in header_row.find_elements(By.TAG_NAME, "th")]
            
            # Extract data rows
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]
            
            data = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= len(headers):
                    row_data = [cell.text.strip() for cell in cells[:len(headers)]]
                    data.append(row_data)
            
            df = pd.DataFrame(data, columns=headers)
            
            # Clean numeric columns
            for col in df.columns[1:]:  # Skip team name
                if col != 'Team':
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing team table: {e}")
            return pd.DataFrame()
    
    def get_afl_fixture(self, year=2024):
        """
        Scrape AFL fixture/results
        """
        try:
            url = f"{self.base_url}/afl/footy/ft_match_list?year={year}"
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find fixture table
            tables = soup.find_all('table')
            
            for table in tables:
                headers = table.find_all('th')
                if len(headers) > 3:
                    return self._parse_fixture_table(table)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error scraping fixture: {e}")
            return pd.DataFrame()
    
    def _parse_fixture_table(self, table):
        """
        Parse fixture/results table
        """
        try:
            headers = [th.text.strip() for th in table.find_all('th')]
            
            rows = table.find_all('tr')[1:]  # Skip header
            
            data = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= len(headers):
                    row_data = [cell.text.strip() for cell in cells[:len(headers)]]
                    data.append(row_data)
            
            return pd.DataFrame(data, columns=headers)
            
        except Exception as e:
            logger.error(f"Error parsing fixture table: {e}")
            return pd.DataFrame()

def main():
    """
    Main function to demonstrate FootyWire scraping
    """
    scraper = FootyWireScraper(headless=True)
    
    try:
        logger.info("Starting FootyWire data collection...")
        
        # Get player stats
        player_stats = scraper.get_player_stats(year=2024)
        if not player_stats.empty:
            player_stats.to_csv('data/raw/footywire_players.csv', index=False)
            logger.info(f"Saved {len(player_stats)} player records")
        
        # Get team stats
        team_stats = scraper.get_team_stats(year=2024)
        if not team_stats.empty:
            team_stats.to_csv('data/raw/footywire_teams.csv', index=False)
            logger.info(f"Saved {len(team_stats)} team records")
        
        # Get fixture
        fixture = scraper.get_afl_fixture(year=2024)
        if not fixture.empty:
            fixture.to_csv('data/raw/footywire_fixture.csv', index=False)
            logger.info(f"Saved {len(fixture)} fixture records")
        
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    main()