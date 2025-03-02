# Lottery Stats API

A Python-based system for collecting, analyzing, and serving historical lottery data from lottery.net.

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
  - Maximum 5 retries per request with 1s, 2s, 4s, 8s, 16s backoff
  - Configurable timeout and backoff settings
- Smart data update system:
  - Automatically detects and updates from the latest entry in existing CSV files
  - Performs full historical scrape for new or empty files
  - Optional manual start date override with `--start-date` parameter
  - Maintains data sorted by date (newest first)
  - Prevents duplicate entries

### Analysis
- Comprehensive statistical analysis:
  - Overall number frequencies and percentages
  - Position-specific number analysis
  - Special ball (Powerball/Mega Ball) analysis
  - Combination frequency analysis
  - Coverage statistics and unused numbers
- Separate analysis modules for each lottery type
- Exports detailed analysis results to CSV files
- Supports both individual and comparative analysis

### API
- RESTful endpoints for accessing lottery data and statistics
- Endpoints for:
  - Number frequencies (overall and position-specific)
  - Combination checking
  - Random and optimized number generation
  - Latest winning combinations
- Built with FastAPI for modern, async API development
- Includes Swagger UI and ReDoc documentation
- Rate limiting and CORS support

## Usage

### Data Collection

To scrape lottery data, use the collection script:

```bash
# Scrape Powerball data
python src/collection/lottery_scraper.py powerball [--start-date YYYY-MM-DD]

# Scrape Mega Millions data
python src/collection/lottery_scraper.py mega-millions [--start-date YYYY-MM-DD]
```

Options:
- `--start-date`: Optional. Specify a start date in YYYY-MM-DD format. If not provided, the scraper will:
  - For new/empty files: Scrape all available historical data
  - For existing files: Update from the latest entry

### Running the Application

The project includes a convenient runner script (`run.py`) that provides commands for both analysis and API functionality:

```bash
# Run the comprehensive analysis for both lotteries
PYTHONPATH=. python run.py analyze

# Start the API server
PYTHONPATH=. python run.py api
```

#### Analysis Output
When running the analysis command, the following files will be generated in the `data/analysis` directory:
- `overall_statistics.csv` - General statistics for both lotteries
- `number_frequencies.csv` - Frequency analysis of all numbers
- `position_frequencies.csv` - Position-specific number frequencies
- `combination_frequencies.csv` - Analysis of winning combinations
- `unused_numbers.csv` - Numbers that have never been drawn

#### API Server
The API server will start on `http://localhost:8000` with the following documentation endpoints:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

The server includes hot reloading, which means any changes to the code will automatically trigger a server restart.

## Data Format

### Collection Output
CSV files are generated in the `data` directory with the following format:

```
Draw Date,Winning Numbers,Powerball/Mega Ball,Multiplier
YYYY-MM-DD,"1 2 3 4 5",10,2
```

Fields:
- `Draw Date`: Date of the lottery draw in YYYY-MM-DD format
- `Winning Numbers`: Five main numbers separated by spaces
- `Powerball/Mega Ball`: The special ball number (Powerball or Mega Ball)
- `Multiplier`: Power Play or Megaplier value (defaults to "1" if not available)

## Project Structure

```
lottery-stats-api/
├── src/                  # Source code
│   ├── collection/       # Data collection modules
│   │   └── lottery_scraper.py
│   ├── analysis/        # Analysis modules
│   │   ├── lottery_analysis.py      # Base analysis functionality
│   │   ├── mega_millions_analysis.py
│   │   ├── powerball_analysis.py
│   │   └── analyze_lotteries.py     # Main analysis script
│   └── api/             # API modules
│       └── api_server.py
├── data/                # Data storage
│   ├── raw/            # Raw CSV files
│   │   ├── powerball.csv
│   │   └── mega_millions.csv
│   └── analysis/       # Analysis outputs
│       ├── overall_statistics.csv
│       ├── number_frequencies.csv
│       ├── position_frequencies.csv
│       ├── combination_frequencies.csv
│       └── unused_numbers.csv
├── requirements.txt     # Python dependencies
├── LICENSE             # MIT License
└── README.md          # Project documentation
```

## Requirements

- Python 3.7+
- Required packages:
  - requests
  - beautifulsoup4
  - pandas
  - urllib3
  - fastapi
  - uvicorn
  - numpy

Install dependencies:
```bash
pip install -r requirements.txt
```

## Error Handling

The system includes robust error handling across all components:
- Collection:
  - Network errors: Automatic retries with exponential backoff
  - SSL errors: Fallback to non-SSL if verification fails
  - Malformed HTML: Flexible parsing that adapts to different page structures
  - Rate limiting: Built-in delays between requests
  - Data validation: Ensures complete and valid data before saving
- Analysis:
  - Input validation
  - Data consistency checks
  - Error reporting in analysis outputs
- API:
  - Input validation
  - Rate limiting
  - Error responses with clear messages
  - CORS handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for informational and educational purposes only. Past lottery results do not guarantee future outcomes. Please gamble responsibly.
