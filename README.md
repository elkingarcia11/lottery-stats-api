# Lottery Stats API

A FastAPI-based REST API for analyzing Mega Millions and Powerball lottery statistics. The API provides historical data analysis, frequency statistics, and combination checking capabilities using a SQLite database.

## Features

- Historical lottery draw data stored in SQLite database
- Number frequency analysis for both main numbers and special balls
- Position-specific frequency analysis
- Combination checking against historical draws
- Optimized combination generation based on frequency analysis
- Random unique combination generation
- Paginated access to latest winning combinations

## Database Structure

The API uses a SQLite database (`data/lottery.db`) with the following tables:

- `draws`: Historical lottery draw data
  - `lottery_type`: Type of lottery (powerball/mega_millions)
  - `draw_date`: Date of the draw
  - `winning_numbers`: Space-separated string of winning numbers
  - `special_ball`: Special ball number (Powerball/Mega Ball)
  - `multiplier`: Prize multiplier value

- `number_frequencies`: Overall number frequency statistics
  - `lottery_type`: Type of lottery
  - `number`: The number
  - `frequency`: Number of occurrences
  - `percentage`: Frequency as a percentage

- `position_frequencies`: Position-specific number frequencies
  - `lottery_type`: Type of lottery
  - `position`: Position (1-5 for main numbers, 6 for special ball)
  - `number`: The number
  - `frequency`: Number of occurrences
  - `percentage`: Frequency as a percentage

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lottery-stats-api.git
   cd lottery-stats-api
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the analysis script to populate the database:
   ```bash
   python run.py analyze
   ```

5. Start the API server:
   ```bash
   python run.py api
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### Root
- `GET /`: Welcome message

### Number Frequencies
- `GET /{lottery_type}/number-frequencies?category={main|special}`: Get frequency statistics for all numbers

### Position Frequencies
- `GET /{lottery_type}/position-frequencies?position={1-5}`: Get position-specific frequency statistics

### Combination Checking
- `POST /{lottery_type}/check-combination`: Check if a combination exists in historical data

### Combination Generation
- `GET /{lottery_type}/generate-optimized`: Generate an optimized combination based on frequencies
- `GET /{lottery_type}/generate-random`: Generate a random unique combination

### Latest Combinations
- `GET /{lottery_type}/latest-combinations`: Get paginated list of latest winning combinations

Replace `{lottery_type}` with either `mega-millions` or `powerball`.

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
