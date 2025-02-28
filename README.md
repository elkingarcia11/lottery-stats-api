# Lottery Stats API

A Python-based scraper and API for collecting and analyzing historical lottery data from lottery.net.

## Features

### Data Collection
- Scrapes historical lottery data for:
  - Mega Millions (from 1996 to present)
  - Powerball (from 1992 to present)
- Handles format changes in lottery data presentation
- Exports data to CSV files with consistent formatting
- Includes error handling and rate limiting to be respectful to the source website

### Analysis Features
- Historical Data Analysis
  - General number frequencies
  - Position-specific frequencies
  - Special ball frequencies (Powerball/Mega Ball)
  - Combination existence checking
  - Unique combination generation
  - Latest winning numbers retrieval

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lottostats-api.git
cd lottostats-api
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Data Collection

The scraper can be run for either Mega Millions or Powerball:

For Mega Millions:
```bash
python lottery_scraper.py mega-millions
```

For Powerball:
```bash
python lottery_scraper.py powerball
```

### API Server

1. Start the server:
```bash
python api_server.py
```

The server will run on `http://localhost:8000`

2. Access the API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Data Format

### CSV Output

The scraper creates CSV files with the following structure:

#### Mega Millions (mega_millions.csv)
- Draw Date: Date of the drawing (MM/DD/YYYY)
- Winning Numbers: Five main numbers separated by spaces
- Mega Ball: The Mega Ball number

#### Powerball (powerball.csv)
- Draw Date: Date of the drawing (MM/DD/YYYY)
- Winning Numbers: Five main numbers separated by spaces
- Powerball Ball: The Powerball number

## API Documentation

### Mega Millions Endpoints

#### 1. Check Combination
**Endpoint:** `POST /mega-millions/check-combination`

**Request:**
```json
{
    "numbers": [1, 2, 3, 4, 5],
    "special_ball": 6
}
```
**Response:**
```json
{
    "success": true,
    "data": {
        "exists": true,
        "frequency": 1,
        "dates": ["2024-03-15"],
        "main_numbers": [1, 2, 3, 4, 5],
        "mega_ball": 6
    }
}
```

#### 2. Get Latest Numbers
**Endpoint:** `GET /mega-millions/latest?limit=100`

**Request Parameters:**
- `limit` (optional, default=100): Number of results to return

**Response:**
```json
{
    "success": true,
    "data": {
        "latest_numbers": [
            {
                "draw_date": "2024-03-15",
                "main_numbers": [1, 2, 3, 4, 5],
                "mega_ball": 6,
                "multiplier": 3
            }
        ]
    }
}
```

### Powerball Endpoints

Similar endpoints are available for Powerball under `/powerball/` routes.

### Error Response Format
All endpoints return errors in this format:
```json
{
    "success": false,
    "message": "Error description",
    "data": {}
}
```

Common HTTP status codes:
- 200: Success
- 400: Bad Request (invalid input)
- 500: Internal Server Error

## Technical Notes

- The scraper includes a 2-second delay between requests to avoid overwhelming the source website
- For Powerball data after August 23, 2021, the script automatically handles the Double Play format and only extracts the main drawing numbers
- All dates are stored in MM/DD/YYYY format for consistency
- API built with FastAPI for high performance and automatic documentation
- Uses Pandas for efficient data processing and analysis

## Input Validation Rules

### Mega Millions
- Main numbers: 5 unique numbers between 1 and 70
- Mega Ball: 1 number between 1 and 25

### Powerball
- Main numbers: 5 unique numbers between 1 and 69
- Powerball: 1 number between 1 and 26

## Dependencies

### Core Dependencies
- requests: For making HTTP requests
- beautifulsoup4: For parsing HTML content
- pandas: For data manipulation and CSV export

### API Dependencies
- fastapi: Web framework for building APIs
- uvicorn: ASGI server implementation
- pydantic: Data validation using Python type annotations

## Project Structure

```
lottostats-api/
├── api_server.py           # FastAPI server implementation
├── lottery_scraper.py      # Data collection script
├── powerball_analysis.py   # Powerball data analysis
├── mega_millions_analysis.py # Mega Millions data analysis
├── requirements.txt        # Project dependencies
├── powerball.csv          # Powerball historical data
├── mega_millions.csv      # Mega Millions historical data
└── README.md              # Project documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for informational and educational purposes only. Past lottery results do not guarantee future outcomes. Please gamble responsibly.
