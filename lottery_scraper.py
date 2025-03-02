import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
from typing import Literal
import argparse
import urllib3
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

def extract_numbers_from_row(row, min_date=None):
    try:
        # Extract date from the first td
        date_td = row.find('td')
        if not date_td:
            return None
        date_link = date_td.find('a')
        if not date_link:
            return None
            
        # Extract date from href instead of text content
        href = date_link.get('href', '')
        if not href:
            return None
            
        # URL format is /powerball/numbers/MM-DD-YYYY
        date_str = href.split('/')[-1]  # Get MM-DD-YYYY
        draw_date = datetime.strptime(date_str, '%m-%d-%Y')
        
        if min_date and draw_date < min_date:
            return None
            
        # Extract numbers from the second td
        numbers_td = date_td.find_next_sibling('td')
        if not numbers_td:
            return None
            
        # Get all ul elements with class 'multi results powerball'
        results_lists = numbers_td.find_all('ul', class_='multi results powerball')
        if not results_lists:
            return None
            
        # Always use the first results list - this contains the main draw
        results_list = results_lists[0]
        
        # Extract all ball elements
        balls = []
        powerball = None
        multiplier = None
        
        # Get all direct li children of the first results list
        for li in results_list.find_all('li', recursive=False):
            if not li.get('class'):
                continue
                
            text = li.get_text(strip=True)
            if not text:
                continue
                
            if 'ball' in li.get('class') and 'powerball' not in li.get('class'):
                if len(balls) < 5:  # Only take first 5 balls
                    balls.append(text)
            elif 'powerball' in li.get('class'):
                powerball = text
            elif 'power-play' in li.get('class'):
                multiplier = text
        
        # Validate we have the correct number of balls
        if len(balls) != 5 or not powerball:
            print(f"Invalid number of balls for {date_str}: {len(balls)} regular balls, powerball: {powerball}")
            return None
            
        return {
            'date': draw_date,
            'winning_numbers': balls,
            'special_ball': powerball,
            'multiplier': multiplier if multiplier else "1"
        }
    except Exception as e:
        print(f"Error processing row: {e}")
        return None

def scrape_lottery(year: int, lottery_type: Literal['mega-millions', 'powerball'], min_date: datetime = None):
    """
    Scrape lottery data for a specific year and lottery type
    
    Args:
        year: The year to scrape
        lottery_type: Type of lottery ('mega-millions' or 'powerball')
        min_date: Optional minimum date to include (datetime object)
    """
    url = f"https://www.lottery.net/{lottery_type}/numbers/{year}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Disable SSL verification warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        print(f"\nFetching URL: {url}")
        session = create_session_with_retries()
        
        # Try with SSL verification first
        try:
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except (requests.exceptions.SSLError, urllib3.exceptions.SSLError):
            print(f"SSL verification failed for {year}, retrying without SSL verification...")
            # If SSL fails, try without verification
            response = session.get(url, headers=headers, verify=False, timeout=30)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Save HTML content to file
        with open(f'debug_{year}.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
            
        data = []
        
        # For years before 2021, use the original table-based approach
        if year < 2021:
            table = soup.find('table')
            if not table:
                print(f"No table found for {year}")
                return []
                
            draw_rows = table.find_all('tr')
            print(f"Found {len(draw_rows)} potential draws for {year}")
            
            for row in draw_rows:
                try:
                    row_data = extract_numbers_from_row(row, min_date)
                    if row_data:
                        data.append(row_data)
                except Exception as e:
                    print(f"Error processing draw: {str(e)}")
                    continue
        else:
            # For 2021 and later, find all tr elements that contain lottery results
            # Look for tr elements that have both td elements and lottery numbers
            all_rows = soup.find_all('tr')
            valid_rows = []
            
            for row in all_rows:
                # Check if row has the correct structure (two td cells, one with a date link)
                tds = row.find_all('td')
                if len(tds) == 2 and tds[0].find('a') and tds[1].find('ul', class_='multi results powerball'):
                    valid_rows.append(row)
            
            print(f"Found {len(valid_rows)} potential draws for {year}")
            
            for row in valid_rows:
                try:
                    row_data = extract_numbers_from_row(row, min_date)
                    if row_data:
                        data.append(row_data)
                except Exception as e:
                    print(f"Error processing draw: {str(e)}")
                    continue
        
        print(f"Successfully collected {len(data)} records for {year}")
        return data
        
    except requests.RequestException as e:
        print(f"Network error for {year}: {str(e)}")
        time.sleep(5)
        return []
    except Exception as e:
        print(f"Unexpected error for {year}: {str(e)}")
        return []

def update_lottery_data(lottery_type: str, start_date: str = None):
    """
    Update lottery data from a specific date, appending to existing CSV.
    If no CSV exists or is empty, performs a full historical scrape.
    If no start_date is provided, uses the latest date from existing CSV.
    
    Args:
        lottery_type: Type of lottery ('mega-millions' or 'powerball')
        start_date: Optional date string in YYYY-mm-dd format
    """
    filename = f"{lottery_type}.csv"
    current_year = datetime.now().year
    
    # Read existing data if file exists
    if os.path.exists(filename):
        existing_df = pd.read_csv(filename)
        if len(existing_df) > 0:
            print(f"Found existing file with {len(existing_df)} records")
            
            if not start_date:
                # Convert Draw Date to datetime for proper comparison
                existing_df['Draw Date'] = pd.to_datetime(existing_df['Draw Date'])
                latest_date = existing_df['Draw Date'].max()
                start_date = latest_date.strftime('%Y-%m-%d')
                print(f"Using latest date from CSV: {start_date}")
        else:
            print("Existing file is empty, performing full historical scrape")
            existing_df = pd.DataFrame()
            start_date = None
    else:
        print("No existing file found, performing full historical scrape")
        existing_df = pd.DataFrame()
        start_date = None
    
    # If no start_date (empty or non-existent file), do full historical scrape
    if start_date is None:
        start_year = 1992 if lottery_type == 'powerball' else 1996
        print(f"Starting full historical scrape from {start_year}")
    else:
        start_year = datetime.strptime(start_date, '%Y-%m-%d').year
    
    # Collect new data
    new_data = []
    for year in range(start_year, current_year + 1):
        year_data = scrape_lottery(year, lottery_type, 
                                 datetime.strptime(start_date, '%Y-%m-%d') if start_date else None)
        if year_data:
            new_data.extend(year_data)
            time.sleep(1)  # Small delay between years
    
    if new_data:
        # Convert new data to DataFrame and format it
        new_records = []
        for record in new_data:
            new_records.append({
                'Draw Date': record['date'].strftime('%Y-%m-%d'),
                'Winning Numbers': ' '.join(record['winning_numbers']),
                f'{lottery_type.split("-")[0].title()} Ball': record['special_ball'],
                'Multiplier': record['multiplier']
            })
        new_df = pd.DataFrame(new_records)
        
        if not existing_df.empty:
            # Make sure Draw Date is datetime for existing_df
            if not pd.api.types.is_datetime64_any_dtype(existing_df['Draw Date']):
                existing_df['Draw Date'] = pd.to_datetime(existing_df['Draw Date'])
            
            # Combine new and existing data
            combined_df = pd.concat([new_df, existing_df], ignore_index=True)
            
            # Remove duplicates based on Draw Date
            combined_df = combined_df.drop_duplicates(subset='Draw Date', keep='first')
            
            # Sort by date in descending order
            combined_df['Draw Date'] = pd.to_datetime(combined_df['Draw Date'])
            combined_df = combined_df.sort_values('Draw Date', ascending=False)
            combined_df['Draw Date'] = combined_df['Draw Date'].dt.strftime('%Y-%m-%d')
        else:
            # For new/empty files, just sort the new data
            combined_df = new_df.copy()
            combined_df['Draw Date'] = pd.to_datetime(combined_df['Draw Date'])
            combined_df = combined_df.sort_values('Draw Date', ascending=False)
            combined_df['Draw Date'] = combined_df['Draw Date'].dt.strftime('%Y-%m-%d')
        
        # Save to CSV
        combined_df.to_csv(filename, index=False)
        print(f"\nUpdated {filename}")
        print(f"Total records: {len(combined_df)}")
        print(f"New records added: {len(new_df)}")
    else:
        print("No new data collected")

def main():
    parser = argparse.ArgumentParser(description='Scrape lottery data')
    parser.add_argument('lottery_type', choices=['mega-millions', 'powerball'], 
                      help='Type of lottery to scrape')
    parser.add_argument('--start-date', type=str, required=False,
                      help='Optional: Start date in YYYY-MM-DD format. If not provided, uses latest date from existing CSV')
    args = parser.parse_args()
    
    update_lottery_data(args.lottery_type, args.start_date)

if __name__ == "__main__":
    main() 