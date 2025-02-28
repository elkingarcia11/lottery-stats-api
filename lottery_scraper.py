import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
from typing import Literal
import argparse

def scrape_lottery(year: int, lottery_type: Literal['mega-millions', 'powerball']):
    """
    Scrape lottery data for a specific year and lottery type
    """
    url = f"https://www.lottery.net/{lottery_type}/numbers/{year}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"\nFetching URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table
        table = soup.find('table', class_='prizes')
        if not table:
            print(f"No table found for {year}. HTML content:")
            print(response.text[:500])  # Print first 500 chars of response
            return []
            
        # Find tbody
        tbody = table.find('tbody')
        if not tbody:
            print(f"No tbody found in table for {year}")
            return []
            
        # Find all rows
        rows = tbody.find_all('tr')
        if not rows:
            print(f"No rows found in tbody for {year}")
            return []
            
        print(f"Found {len(rows)} rows for {year}")
        
        data = []
        powerball_format_change_date = datetime(2021, 8, 23)  # Format change date for Powerball
        
        for row_index, row in enumerate(rows, 1):
            try:
                # Extract date
                date_cell = row.find('td')
                if not date_cell:
                    print(f"No date cell found in row {row_index}")
                    continue
                    
                # Get raw text and normalize spaces
                date_text = ' '.join(date_cell.get_text().split())
                try:
                    date_obj = datetime.strptime(date_text, '%A %B %d, %Y')
                except ValueError:
                    # Try alternative format if first attempt fails
                    date_text = date_text.replace('\n', ' ').strip()
                    date_parts = date_text.split(' ')
                    if len(date_parts) >= 4:
                        # Reconstruct date string ensuring proper spacing
                        date_text = f"{date_parts[0]} {' '.join(date_parts[1:])}"
                        try:
                            date_obj = datetime.strptime(date_text, '%A %B %d, %Y')
                        except ValueError as e:
                            print(f"Failed to parse date '{date_text}' in row {row_index}: {e}")
                            continue
                
                formatted_date = date_obj.strftime('%m/%d/%Y')
                
                # Extract numbers based on lottery type and date
                if lottery_type == 'powerball' and date_obj >= powerball_format_change_date:
                    # Get the first set of numbers (before Double Play)
                    number_lists = row.find_all('ul', class_='multi results powerball')
                    if number_lists:
                        first_list = number_lists[0]  # Get only the first list (ignore Double Play)
                        numbers = first_list.find_all('li', class_='ball')
                        special_ball = first_list.find('li', class_='powerball')
                else:
                    # Original format for both mega-millions and older powerball
                    numbers = row.find_all('li', class_='ball')
                    # Use correct class name for each lottery type
                    special_ball_class = 'mega-ball' if lottery_type == 'mega-millions' else 'powerball'
                    special_ball = row.find('li', class_=special_ball_class)
                
                if not numbers:
                    print(f"No numbers found for {formatted_date}")
                    continue
                    
                if len(numbers) != 5:
                    print(f"Expected 5 numbers but found {len(numbers)} for {formatted_date}")
                    continue
                    
                if not special_ball:
                    print(f"No special ball found for {formatted_date}")
                    continue
                
                winning_numbers = [num.get_text(strip=True) for num in numbers]
                special_ball_number = special_ball.get_text(strip=True)
                
                data.append({
                    'Draw Date': formatted_date,
                    'Winning Numbers': ' '.join(winning_numbers),
                    f'{lottery_type.split("-")[0].title()} Ball': special_ball_number
                })
                
            except Exception as e:
                print(f"Error processing row {row_index} for {year}: {str(e)}")
                continue
        
        print(f"Successfully collected {len(data)} records for {year}")
        return data
        
    except requests.RequestException as e:
        print(f"Network error for {year}: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error for {year}: {str(e)}")
        return []

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scrape lottery data from lottery.net')
    parser.add_argument('lottery_type', choices=['mega-millions', 'powerball'],
                      help='Type of lottery to scrape (mega-millions or powerball)')
    args = parser.parse_args()

    # Configuration for different lottery types
    lottery_configs = {
        'mega-millions': {'start_year': 1996, 'filename': 'mega_millions.csv'},
        'powerball': {'start_year': 1992, 'filename': 'powerball.csv'}
    }
    
    current_year = 2025
    config = lottery_configs[args.lottery_type]
    all_data = []
    
    print(f"\nStarting {args.lottery_type} scraping...")
    
    # Scrape data from start year to current year
    for year in range(config['start_year'], current_year + 1):
        print(f"\nScraping {args.lottery_type} for year {year}...")
        year_data = scrape_lottery(year, args.lottery_type)
        all_data.extend(year_data)
        time.sleep(2)  # Increased delay to be more conservative
    
    # Create DataFrame and save to CSV
    if all_data:
        df = pd.DataFrame(all_data)
        df = df.sort_values('Draw Date', ascending=False)
        df.to_csv(config['filename'], index=False)
        print(f"\nData successfully saved to {config['filename']}")
        print(f"Total records collected: {len(df)}")
    else:
        print(f"\nNo data was collected for {args.lottery_type}")

if __name__ == "__main__":
    main() 