# LottoStats API

A comprehensive REST API for analyzing Powerball and Mega Millions lottery data, providing historical statistics, frequency analysis, and unique combination generation.

## Features

- **Historical Data Analysis**
  - General number frequencies
  - Position-specific frequencies
  - Special ball frequencies (Powerball/Mega Ball)
  - Combination existence checking
  - Unique combination generation

- **Supported Lotteries**
  - Powerball
  - Mega Millions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lottostats-api.git
cd lottostats-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
python api_server.py
```

The server will run on `http://localhost:8000`

2. Access the API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Mega Millions

- `GET /mega-millions/frequencies` - Get general number frequencies
- `GET /mega-millions/position-frequencies` - Get frequencies by position
- `GET /mega-millions/megaball-frequencies` - Get Mega Ball frequencies
- `POST /mega-millions/check-combination` - Check if a combination exists
- `GET /mega-millions/generate-combination` - Get a new unique combination

### Powerball

- `GET /powerball/frequencies` - Get general number frequencies
- `GET /powerball/position-frequencies` - Get frequencies by position
- `GET /powerball/powerball-frequencies` - Get Powerball frequencies
- `POST /powerball/check-combination` - Check if a combination exists
- `GET /powerball/generate-combination` - Get a new unique combination

## Example API Calls

### Check Mega Millions Combination
```bash
curl -X POST "http://localhost:8000/mega-millions/check-combination" \
     -H "Content-Type: application/json" \
     -d '{"numbers": [1, 2, 3, 4, 5], "special_ball": 6}'
```

### Check Powerball Combination
```bash
curl -X POST "http://localhost:8000/powerball/check-combination" \
     -H "Content-Type: application/json" \
     -d '{"numbers": [1, 2, 3, 4, 5, 6]}'
```

### Generate New Combinations
```bash
# Mega Millions
curl "http://localhost:8000/mega-millions/generate-combination"

# Powerball
curl "http://localhost:8000/powerball/generate-combination"
```

## Data Sources

The API uses historical data from:
- `powerball.csv` - Historical Powerball drawing results
- `mega_million.csv` - Historical Mega Millions drawing results

## Technical Details

- Built with FastAPI
- Uses Pandas for data processing
- Implements efficient data structures for frequency tracking
- Provides input validation and error handling
- Returns standardized JSON responses

## Requirements

- Python 3.8+
- pandas==2.0.3
- fastapi==0.109.2
- uvicorn==0.27.1
- pydantic==2.6.1

## Project Structure

```
lottostats-api/
├── api_server.py           # FastAPI server implementation
├── powerball_analysis.py   # Powerball data analysis
├── mega_millions_analysis.py # Mega Millions data analysis
├── requirements.txt        # Project dependencies
├── powerball.csv          # Powerball historical data
├── mega_million.csv       # Mega Millions historical data
└── README.md             # Project documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for informational and educational purposes only. Past lottery results do not guarantee future outcomes. Please gamble responsibly.
