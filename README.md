# Lottery Stats API

A Python-based system for collecting, analyzing, and serving historical lottery data from lottery.net.

## Features

### Data Collection
- Scrapes historical lottery data for:
  - Mega Millions (from 1996 to present)
  - Powerball (from 1992 to present)
- Handles format changes in lottery data presentation
- Exports data to CSV files with consistent formatting
- Includes error handling and rate limiting

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
    "special_ball": 10
}
```

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

```bash
# For Mega Millions
python lottery_scraper.py mega-millions

# For Powerball
python lottery_scraper.py powerball
```

### Data Analysis

Run the comprehensive analysis for both lotteries:

```bash
python analyze_lotteries.py
```

This will create a timestamped directory (format: `lottery_analysis_YYYYMMDD_HHMMSS`) containing five CSV files:

1. `1_overall_statistics.csv`
   - Total draws for each lottery
   - Number ranges
   - Coverage statistics

2. `2_number_frequencies.csv`
   - Frequency of each number
   - Both count and percentage
   - Separate sections for main numbers and special balls

3. `3_position_frequencies.csv`
   - Position-specific number frequencies
   - Analysis of numbers in each position (1-5)
   - Both count and percentage

4. `4_combination_frequencies.csv`
   - Analysis of winning combinations
   - Both main numbers only and full combinations
   - Frequency and percentage of occurrences

5. `5_unused_numbers.csv`
   - Numbers that have never been drawn
   - Separated by lottery type and number category

### API Server (Coming Soon)

1. Start the server:
```bash
python api_server.py
```

The server will run on `http://localhost:8000`

2. Access the API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Data Format

### CSV Output Files

#### Lottery Data Files
- `mega_millions.csv` and `powerball.csv`:
  - Draw Date: Date of the drawing (MM/DD/YYYY)
  - Winning Numbers: Five main numbers separated by spaces
  - Special Ball: Mega Ball or Powerball number

#### Analysis Output
All analysis files include:
- Clear headers and categories
- Both raw counts and percentages
- Lottery-specific breakdowns
- Timestamp in directory name for version tracking

## Technical Notes

- Scraper includes a 2-second delay between requests
- Handles Powerball format change after August 23, 2021
- All dates stored in MM/DD/YYYY format
- Analysis results include confidence metrics
- Comprehensive error handling and validation

## Input Validation Rules

### Mega Millions
- Main numbers: 5 unique numbers between 1 and 70
- Mega Ball: 1 number between 1 and 25

### Powerball
- Main numbers: 5 unique numbers between 1 and 69
- Powerball: 1 number between 1 and 26

## Project Structure

```
lottostats-api/
├── lottery_scraper.py      # Data collection script
├── lottery_analysis.py     # Base analysis functionality
├── mega_millions_analysis.py # Mega Millions specific analysis
├── powerball_analysis.py   # Powerball specific analysis
├── analyze_lotteries.py    # Comprehensive analysis script
├── api_server.py          # FastAPI server (coming soon)
├── requirements.txt       # Project dependencies
├── powerball.csv         # Powerball historical data
├── mega_millions.csv     # Mega Millions historical data
└── README.md            # Project documentation
```

## Dependencies

### Core Dependencies
- requests: For making HTTP requests
- beautifulsoup4: For parsing HTML content
- pandas: For data manipulation and CSV handling

### Analysis Dependencies
- numpy: For numerical computations
- dataclasses: For structured data handling

### API Dependencies (Coming Soon)
- fastapi: Web framework for building APIs
- uvicorn: ASGI server implementation
- pydantic: Data validation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for informational and educational purposes only. Past lottery results do not guarantee future outcomes. Please gamble responsibly.
