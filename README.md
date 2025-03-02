# Lottery Stats API

A Python-based system for collecting historical lottery data from lottery.net.

## Features

### Data Collection
- Scrapes historical lottery data for:
  - Mega Millions (from 1996 to present)
  - Powerball (from 1992 to present)
- Handles format changes in lottery data presentation:
  - Pre-2021: Table-based structure
  - Post-2021: Flexible row-based parsing with Double Play support
- Exports data to CSV files with consistent formatting
- Includes error handling and retry mechanism:
  - Automatic retries with exponential backoff
  - Maximum 3 retries per request
  - Configurable timeout and backoff settings
- Smart data update system:
  - Automatically detects and updates from the latest entry in existing CSV files
  - Performs full historical scrape for new or empty files
  - Optional manual start date override with `--start-date` parameter
  - Maintains data sorted by date (newest first)
  - Prevents duplicate entries

### Analysis Features
- Comprehensive statistical analysis:
  - Overall number frequencies and percentages
  - Position-specific number analysis
  - Special ball (Powerball/Mega Ball) analysis
  - Combination frequency analysis
  - Coverage statistics and unused numbers
- Exports detailed analysis results to CSV files
- Supports both individual and comparative analysis

### API Features
The API provides real-time access to lottery statistics and analysis through RESTful endpoints.

#### Base URL
```
http://localhost:8000
```

#### API Reference

1. **Number Frequencies**
```http
GET /{lottery_type}/number-frequencies?category={category}
```
Parameters:
- Path:
  - `lottery_type`: (string, required) - "mega-millions" or "powerball"
- Query:
  - `category`: (string, required) - "main" or "special"

Response:
```json
[
  {
    "number": 1,
    "count": 150,
    "percentage": 2.5
  },
  {
    "number": 2,
    "count": 142,
    "percentage": 2.3
  }
]
```

2. **Position Frequencies**
```http
GET /{lottery_type}/position-frequencies?position={position}
```
Parameters:
- Path:
  - `lottery_type`: (string, required) - "mega-millions" or "powerball"
- Query:
  - `position`: (integer, optional) - Position number (1-5)

Response:
```json
[
  {
    "position": 1,
    "number": 1,
    "count": 30,
    "percentage": 1.5
  },
  {
    "position": 1,
    "number": 2,
    "count": 28,
    "percentage": 1.4
  }
]
```

3. **Check Combination**
```http
POST /{lottery_type}/check-combination
```
Parameters:
- Path:
  - `lottery_type`: (string, required) - "mega-millions" or "powerball"
- Request Body:
```json
{
    "numbers": [1, 2, 3, 4, 5],
    "special_ball": 10  // Optional
}
```

Response:
```json
{
    "exists": true,
    "frequency": 2,
    "dates": ["01/01/2020", "03/15/2021"],
    "main_numbers": [1, 2, 3, 4, 5],
    "special_ball": 10,
    "matches": [
        {
            "date": "01/01/2020",
            "special_ball": 10,
            "prize": "1,000,000"
        },
        {
            "date": "03/15/2021",
            "special_ball": 12,
            "prize": "500,000"
        }
    ]
}
```

Notes:
- When only main numbers are provided (no special_ball), the endpoint returns all matching combinations with their respective special balls and dates
- The `matches` array provides detailed information about each occurrence including the special ball and prize (if available)
- Main numbers are always returned in sorted order
- If no matches are found, `frequency` will be 0 and `matches` will be null

4. **Generate Optimized Combination**
```http
GET /{lottery_type}/generate-optimized
```
Parameters:
- Path:
  - `lottery_type`: (string, required) - "mega-millions" or "powerball"

Response:
```json
{
    "main_numbers": [12, 23, 34, 45, 56],
    "special_ball": 15,
    "position_percentages": {
        "1": 3.2,
        "2": 2.8,
        "3": 3.1,
        "4": 2.9,
        "5": 3.0
    },
    "is_unique": true
}
```

5. **Generate Random Combination**
```http
GET /{lottery_type}/generate-random
```
Parameters:
- Path:
  - `lottery_type`: (string, required) - "mega-millions" or "powerball"

Response:
```json
{
    "main_numbers": [7, 13, 25, 41, 68],
    "special_ball": 12,
    "is_unique": true
}
```

6. **Latest Winning Combinations**
```http
GET /{lottery_type}/latest-combinations?page={page}&page_size={page_size}
```
Parameters:
- Path:
  - `lottery_type`: (string, required) - "mega-millions" or "powerball"
- Query:
  - `page`: (integer, optional, default: 1) - Page number for pagination
  - `page_size`: (integer, optional, default: 20, max: 50) - Number of combinations per page

Response:
```json
{
    "combinations": [
        {
            "draw_date": "2024-03-21",
            "main_numbers": [1, 2, 3, 4, 5],
            "special_ball": 10,
            "prize": "1,000,000"
        }
    ],
    "total_count": 100,
    "has_more": true
}
```
Notes:
- Results are sorted by draw date (newest first)
- Main numbers are always returned in sorted order
- `has_more` indicates if there are more pages available
- `prize` field is optional and may not be available for all draws

#### Error Responses

All endpoints may return the following error responses:

400 Bad Request:
```json
{
    "detail": "Invalid input message"
}
```

500 Internal Server Error:
```json
{
    "detail": "Error message"
}
```

Common error cases:
- Invalid lottery type
- Invalid number ranges
- Non-unique numbers
- Invalid position number
- Unable to generate unique combination

#### Rate Limiting
- Maximum 100 requests per minute per IP address
- Exceeding the limit returns a 429 Too Many Requests response

#### CORS
- API supports Cross-Origin Resource Sharing (CORS)
- All origins are allowed for development purposes
- Configure allowed origins in production

#### Input Validation
- Mega Millions:
  - Main numbers: 5 unique numbers between 1 and 70
  - Mega Ball: 1 number between 1 and 25
- Powerball:
  - Main numbers: 5 unique numbers between 1 and 69
  - Powerball: 1 number between 1 and 26

#### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage

### Data Collection

To scrape lottery data, use the `lottery_scraper.py` script:

```bash
# Scrape Powerball data
python lottery_scraper.py powerball [--start-date YYYY-MM-DD]

# Scrape Mega Millions data
python lottery_scraper.py mega-millions [--start-date YYYY-MM-DD]
```

Options:
- `--start-date`: Optional. Specify a start date in YYYY-MM-DD format. If not provided, the scraper will:
  - For new/empty files: Scrape all available historical data
  - For existing files: Update from the latest entry

### Output Format

The scraper generates CSV files with the following format:

```
Draw Date,Numbers,Powerball/Mega Ball
YYYY-MM-DD,"1 2 3 4 5",10
```

- `Draw Date`: Date of the lottery draw in YYYY-MM-DD format
- `Numbers`: Five main numbers separated by spaces
- `Powerball/Mega Ball`: The special ball number (Powerball or Mega Ball)

## Requirements

- Python 3.7+
- Required packages:
  - requests
  - beautifulsoup4
  - pandas
  - urllib3

Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
lottery-stats-api/
├── lottery_scraper.py     # Main scraping script
├── requirements.txt       # Python dependencies
└── data/                 # Generated CSV files
    ├── powerball.csv
    └── mega_millions.csv
```

## Error Handling

The scraper includes robust error handling:
- Network errors: Automatic retries with exponential backoff
- Malformed HTML: Flexible parsing that adapts to different page structures
- Rate limiting: Built-in delays between requests
- Data validation: Ensures complete and valid data before saving

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for informational and educational purposes only. Past lottery results do not guarantee future outcomes. Please gamble responsibly.
