#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import argparse
from pathlib import Path
import time
import random
from typing import List, Dict, Optional, Tuple, Literal
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'lottery.db'
BASE_URL = "https://www.lottery.net"

def create_session_with_retries() -> requests.Session:
    """Create a session with retry strategy."""
    session = requests.Session()
    
    # Create a retry strategy
    retries = Retry(
        total=5,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4, 8, 16 seconds between retries
        status_forcelist=[500, 502, 503, 504],  # HTTP status codes to retry on
        allowed_methods=["GET"]  # Only retry on GET requests
    )
    
    # Mount the adapter with retry strategy for both HTTP and HTTPS
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

class LotteryScraper:
    def __init__(self, lottery_type: str):
        """Initialize the scraper for a specific lottery type."""
        self.lottery_type = lottery_type
        self.logger = logging.getLogger(__name__)
        self.session = create_session_with_retries()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def _get_latest_date_from_db(self, conn: sqlite3.Connection) -> Optional[str]:
        """Get the most recent draw date from the database."""
        cursor = conn.cursor()
        cursor.execute(
            'SELECT MAX(draw_date) FROM draws WHERE lottery_type = ?',
            (self.lottery_type,)
        )
        result = cursor.fetchone()[0]
        return result

    def process_row(self, row):
        try:
            # Find the date cell
            date_cell = row.find('td')
            if not date_cell:
                return None

            # Get date from link or text
            date_link = date_cell.find('a')
            if date_link:
                date_text = date_link.text.strip()
            else:
                date_text = date_cell.text.strip()

            # Remove line breaks and extra whitespace
            date_text = ' '.join(date_text.split())

            # Handle date formats
            try:
                # First try the standard format
                draw_date = datetime.strptime(date_text, '%B %d, %Y').strftime('%Y-%m-%d')
            except ValueError:
                try:
                    # Try the format with day of week
                    # Remove day of week from start of string
                    date_parts = date_text.split(' ')
                    if len(date_parts) >= 4:  # DayOfWeek Month DD, YYYY
                        date_text = ' '.join(date_parts[1:])
                    draw_date = datetime.strptime(date_text, '%B %d, %Y').strftime('%Y-%m-%d')
                except ValueError as e:
                    self.logger.warning(f"Could not parse date: {date_text} - {str(e)}")
                    return None

            # Find the numbers list
            numbers_list = row.find('ul', class_='multi results mega-millions')
            if not numbers_list:
                return None

            # Get all ball elements
            regular_balls = []
            special_ball = None
            multiplier = 1.0

            # Process each ball
            for ball in numbers_list.find_all('li'):
                try:
                    number = int(ball.text.strip())
                    if 'mega-ball' in ball.get('class', []):
                        special_ball = number
                    elif 'megaplier' in ball.get('class', []):
                        multiplier = float(number)
                    elif 'ball' in ball.get('class', []):
                        regular_balls.append(str(number))
                except ValueError as e:
                    self.logger.warning(f"Could not parse ball number: {ball.text} - {str(e)}")
                    continue

            # Validate we have the correct number of balls
            if len(regular_balls) != 5 or special_ball is None:
                self.logger.warning(f"Invalid number of balls: {len(regular_balls)} regular, special: {special_ball}")
                return None

            draw = {
                'draw_date': draw_date,
                'winning_numbers': ' '.join(regular_balls),
                'special_ball': special_ball,
                'multiplier': multiplier
            }

            self.logger.debug(f"Successfully extracted draw: {draw}")
            return draw

        except Exception as e:
            self.logger.error(f"Error processing row: {str(e)}")
            return None

    def scrape_year(self, year: int, min_date: Optional[datetime] = None) -> List[Dict]:
        """Scrape lottery data for a specific year."""
        url = f"https://www.lottery.net/{self.lottery_type}/numbers/{year}"
        logger.info(f"Fetching URL: {url}")
        
        try:
            # Try with SSL verification first
            try:
                response = self.session.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
            except (requests.exceptions.SSLError, urllib3.exceptions.SSLError):
                logger.warning(f"SSL verification failed for {year}, retrying without SSL verification...")
                # If SSL fails, try without verification
                response = self.session.get(url, headers=self.headers, verify=False, timeout=30)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            data = []
            
            # Try new format first (post-2021)
            draw_rows = soup.find_all('tr', class_='draw')
            if draw_rows:
                logger.info(f"Found {len(draw_rows)} potential draws for {year}")
                for row in draw_rows:
                    row_data = self.process_row(row)
                    if row_data:
                        if min_date and datetime.strptime(row_data['draw_date'], '%Y-%m-%d') < min_date:
                            logger.debug(f"Date {row_data['draw_date']} is before min_date {min_date}")
                            continue
                        data.append(row_data)
            else:
                # Try old format (pre-2021)
                table = soup.find('table')
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header row
                    logger.info(f"Found {len(rows)} potential draws in old format for {year}")
                    for row in rows:
                        row_data = self.process_row(row)
                        if row_data:
                            if min_date and datetime.strptime(row_data['draw_date'], '%Y-%m-%d') < min_date:
                                logger.debug(f"Date {row_data['draw_date']} is before min_date {min_date}")
                                continue
                            data.append(row_data)
            
            logger.info(f"Successfully collected {len(data)} records for {year}")
            return data
            
        except requests.RequestException as e:
            logger.error(f"Network error for {year}: {str(e)}")
            time.sleep(5)
            return []
        except Exception as e:
            logger.error(f"Unexpected error for {year}: {str(e)}")
            return []

    def _insert_draw(self, conn: sqlite3.Connection, draw_data: Dict) -> bool:
        """Insert a single draw into the database."""
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO draws 
                (lottery_type, draw_date, winning_numbers, special_ball, multiplier)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.lottery_type,
                draw_data['draw_date'],
                draw_data['winning_numbers'],
                draw_data['special_ball'],
                draw_data['multiplier']
            ))
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return False

    def scrape_and_update(self, start_date: Optional[str] = None) -> int:
        """
        Scrape lottery data and update the database.
        Returns the number of new records added.
        """
        conn = sqlite3.connect(DB_PATH)
        try:
            if not start_date:
                start_date = self._get_latest_date_from_db(conn)
                if start_date:
                    logger.info(f"Using latest date from database: {start_date}")

            min_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
            current_year = datetime.now().year
            start_year = min_date.year if min_date else (1992 if self.lottery_type == 'powerball' else 1996)
            
            new_records = 0
            
            # Scrape each year from start_year to current_year
            for year in range(current_year, start_year - 1, -1):
                year_data = self.scrape_year(year, min_date)
                
                for draw_data in year_data:
                    if self._insert_draw(conn, draw_data):
                        new_records += 1
                
                # Random delay between years
                if year > start_year:
                    time.sleep(random.uniform(1, 3))

            conn.commit()
            logger.info(f"Added {new_records} new records to the database")
            return new_records

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            conn.rollback()
            return 0

        finally:
            conn.close()

def main():
    parser = argparse.ArgumentParser(description='Scrape lottery data and update the database')
    parser.add_argument('lottery_type', choices=['powerball', 'mega-millions'],
                      help='Type of lottery to scrape')
    parser.add_argument('--start-date', type=str,
                      help='Optional: Start date in YYYY-MM-DD format. If not provided, uses latest date from database')
    
    args = parser.parse_args()
    
    # Ensure database and tables exist
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS draws (
                lottery_type TEXT,
                draw_date TEXT,
                winning_numbers TEXT,
                special_ball INTEGER,
                multiplier REAL,
                PRIMARY KEY (lottery_type, draw_date)
            )
        ''')
        conn.commit()
    finally:
        conn.close()
    
    # Start scraping
    scraper = LotteryScraper(args.lottery_type)
    new_records = scraper.scrape_and_update(args.start_date)
    
    if new_records > 0:
        logger.info("Database update completed successfully")
    else:
        logger.info("No new records added")

if __name__ == "__main__":
    main() 