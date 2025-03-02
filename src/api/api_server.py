from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Optional, Annotated, Any
from pydantic import BaseModel, conlist
import sys
import os

# Add the parent directory to Python path to find the analysis modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from analysis.mega_millions_analysis import MegaMillionsAnalysis
from analysis.powerball_analysis import PowerballAnalysis
from enum import Enum
import uvicorn
import random
import pandas as pd

class LotteryType(str, Enum):
    mega_millions = "mega-millions"
    powerball = "powerball"

class NumberFrequencyResponse(BaseModel):
    number: int
    count: int
    percentage: float

class PositionFrequencyResponse(BaseModel):
    position: int
    number: int
    count: int
    percentage: float

class CombinationRequest(BaseModel):
    numbers: Annotated[List[int], conlist(item_type=int, min_length=5, max_length=5)]  # Exactly 5 numbers
    special_ball: Optional[int] = None

class CombinationResponse(BaseModel):
    exists: bool
    frequency: int
    dates: List[str]
    main_numbers: List[int]
    special_ball: Optional[int] = None
    matches: Optional[List[Dict[str, Any]]] = None  # List of detailed match information

class GeneratedCombinationResponse(BaseModel):
    main_numbers: List[int]
    special_ball: int
    position_percentages: Optional[Dict[int, float]] = None
    is_unique: bool

class WinningCombination(BaseModel):
    draw_date: str
    main_numbers: List[int]
    special_ball: int
    prize: Optional[str] = None

class WinningCombinationsResponse(BaseModel):
    combinations: List[WinningCombination]
    total_count: int
    has_more: bool

app = FastAPI(
    title="Lottery Stats API",
    description="API for analyzing Mega Millions and Powerball lottery statistics",
    version="1.0.0"
)

# Initialize analyzers
mega_millions = MegaMillionsAnalysis()
powerball = PowerballAnalysis()

@app.get("/")
async def root():
    return {"message": "Welcome to the Lottery Stats API"}

@app.get("/{lottery_type}/number-frequencies", response_model=List[NumberFrequencyResponse])
async def get_number_frequencies(
    lottery_type: LotteryType,
    category: str = Query(..., description="Either 'main' for main numbers or 'special' for Mega Ball/Powerball")
):
    """Get frequency statistics for all numbers in a lottery."""
    try:
        analysis = mega_millions if lottery_type == LotteryType.mega_millions else powerball
        stats = analysis.get_analysis()
        
        if category == 'main':
            frequencies = stats['overall_frequencies']
        elif category == 'special':
            frequencies = stats['special_ball_frequencies']
        else:
            raise HTTPException(status_code=400, detail="Invalid category. Use 'main' or 'special'")
        
        return sorted([
            NumberFrequencyResponse(
                number=number,
                count=freq.count,
                percentage=freq.percentage
            )
            for number, freq in frequencies.items()
        ], key=lambda x: x.number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{lottery_type}/position-frequencies", response_model=List[PositionFrequencyResponse])
async def get_position_frequencies(
    lottery_type: LotteryType,
    position: Optional[int] = Query(None, ge=1, le=5, description="Filter by specific position (1-5)")
):
    """Get frequency statistics for numbers in each position."""
    try:
        analysis = mega_millions if lottery_type == LotteryType.mega_millions else powerball
        stats = analysis.get_analysis()
        
        results = []
        position_freqs = stats['position_frequencies']
        
        for pos in range(1, 6):
            if position and pos != position:
                continue
                
            for number, freq in position_freqs[pos].items():
                results.append(
                    PositionFrequencyResponse(
                        position=pos,
                        number=number,
                        count=freq.count,
                        percentage=freq.percentage
                    )
                )
        
        # Sort first by position, then by number
        return sorted(results, key=lambda x: (x.position, x.number))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/{lottery_type}/check-combination", response_model=CombinationResponse)
async def check_combination(lottery_type: LotteryType, request: CombinationRequest):
    """Check if a combination exists in historical data."""
    try:
        analysis = mega_millions if lottery_type == LotteryType.mega_millions else powerball
        df = analysis.df
        
        # Convert main numbers to string format for comparison
        main_numbers_str = ' '.join(map(str, sorted(request.numbers)))
        
        # Find matches based on main numbers
        matches = df[df['Winning Numbers'] == main_numbers_str].copy()
        
        if matches.empty:
            return CombinationResponse(
                exists=False,
                frequency=0,
                dates=[],
                main_numbers=sorted(request.numbers),
                special_ball=request.special_ball
            )
        
        # Convert matches to response format
        matches_list = []
        exact_match_found = False
        
        for _, row in matches.iterrows():
            row_special_ball = int(row[analysis.special_ball_column])
            
            # If special ball is provided, mark if we found an exact match
            if request.special_ball is not None and row_special_ball == request.special_ball:
                exact_match_found = True
                
            matches_list.append({
                'date': row['Draw Date'],
                'special_ball': row_special_ball,
                'prize': row.get('Prize', None)  # Include prize if available
            })
            
        # If special ball was provided but no exact match was found, return no matches
        if request.special_ball is not None and not exact_match_found:
            return CombinationResponse(
                exists=False,
                frequency=0,
                dates=[],
                main_numbers=sorted(request.numbers),
                special_ball=request.special_ball
            )
            
        return CombinationResponse(
            exists=True,
            frequency=len(matches_list),
            dates=[match['date'] for match in matches_list],
            main_numbers=sorted(request.numbers),
            special_ball=request.special_ball,
            matches=matches_list  # Include detailed match information
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{lottery_type}/generate-optimized", response_model=GeneratedCombinationResponse)
async def generate_optimized_combination(lottery_type: LotteryType):
    """Generate a combination that maximizes position-specific frequencies while ensuring it's unique."""
    try:
        analysis = mega_millions if lottery_type == LotteryType.mega_millions else powerball
        stats = analysis.get_analysis()
        position_freqs = stats['position_frequencies']
        
        # Get the maximum range for numbers based on lottery type
        max_main = 70 if lottery_type == LotteryType.mega_millions else 69
        max_special = 25 if lottery_type == LotteryType.mega_millions else 26
        
        # Find the highest frequency numbers for each position
        optimized_numbers = []
        position_percentages = {}
        
        for pos in range(1, 6):
            # Sort numbers by frequency for this position
            sorted_nums = sorted(
                position_freqs[pos].items(),
                key=lambda x: x[1].percentage,
                reverse=True
            )
            
            # Find the highest frequency number that isn't already selected
            for num, freq in sorted_nums:
                if num not in optimized_numbers and 1 <= num <= max_main:
                    optimized_numbers.append(num)
                    position_percentages[pos] = freq.percentage
                    break
        
        # Find the highest frequency special ball
        special_freqs = stats['special_ball_frequencies']
        special_ball = max(
            special_freqs.items(),
            key=lambda x: x[1].percentage
        )[0]
        
        # Check if this combination already exists
        combo = tuple(sorted(optimized_numbers) + [special_ball])
        is_unique = combo not in stats['full_combination_frequencies']
        
        # If not unique, modify the combination slightly
        if not is_unique:
            # Try replacing the last number with the next best option
            original_last = optimized_numbers[-1]
            for num in range(1, max_main + 1):
                if num not in optimized_numbers:
                    optimized_numbers[-1] = num
                    new_combo = tuple(sorted(optimized_numbers) + [special_ball])
                    if new_combo not in stats['full_combination_frequencies']:
                        is_unique = True
                        break
            
            # If still not unique, restore original and try a different special ball
            if not is_unique:
                optimized_numbers[-1] = original_last
                for num in range(1, max_special + 1):
                    if num != special_ball:
                        new_combo = tuple(sorted(optimized_numbers) + [num])
                        if new_combo not in stats['full_combination_frequencies']:
                            special_ball = num
                            is_unique = True
                            break
        
        return GeneratedCombinationResponse(
            main_numbers=sorted(optimized_numbers),
            special_ball=special_ball,
            position_percentages=position_percentages,
            is_unique=is_unique
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{lottery_type}/generate-random", response_model=GeneratedCombinationResponse)
async def generate_random_combination(lottery_type: LotteryType):
    """Generate a random combination that hasn't appeared before."""
    try:
        analysis = mega_millions if lottery_type == LotteryType.mega_millions else powerball
        stats = analysis.get_analysis()
        
        # Get the maximum range for numbers based on lottery type
        max_main = 70 if lottery_type == LotteryType.mega_millions else 69
        max_special = 25 if lottery_type == LotteryType.mega_millions else 26
        
        # Generate combinations until we find a unique one
        max_attempts = 100  # Prevent infinite loop
        for _ in range(max_attempts):
            # Generate 5 unique random numbers for main numbers
            main_numbers = random.sample(range(1, max_main + 1), 5)
            special_ball = random.randint(1, max_special)
            
            # Check if this combination exists
            combo = tuple(sorted(main_numbers) + [special_ball])
            if combo not in stats['full_combination_frequencies']:
                return GeneratedCombinationResponse(
                    main_numbers=sorted(main_numbers),
                    special_ball=special_ball,
                    is_unique=True
                )
        
        raise HTTPException(
            status_code=500,
            detail="Could not generate a unique combination after maximum attempts"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{lottery_type}/latest-combinations", response_model=WinningCombinationsResponse)
async def get_latest_combinations(
    lottery_type: LotteryType,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Number of combinations per page")
):
    """Get the latest winning combinations with pagination support, sorted by most recent draw date first."""
    try:
        analysis = mega_millions if lottery_type == LotteryType.mega_millions else powerball
        df = analysis.df
        
        # Convert Draw Date to datetime for proper sorting
        df['Draw Date'] = pd.to_datetime(df['Draw Date'])
        
        # Sort by draw date in descending order (most recent first)
        df = df.sort_values('Draw Date', ascending=False)
        
        # Convert back to string format
        df['Draw Date'] = df['Draw Date'].dt.strftime('%Y-%m-%d')
        
        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        total_count = len(df)
        
        # Get the slice of data for current page
        page_df = df.iloc[start_idx:end_idx]
        
        combinations = []
        for _, row in page_df.iterrows():
            main_numbers = sorted([int(n) for n in row['Winning Numbers'].split()])
            special_ball = int(row[analysis.special_ball_column])
            
            combinations.append(
                WinningCombination(
                    draw_date=row['Draw Date'],
                    main_numbers=main_numbers,
                    special_ball=special_ball,
                    prize=row.get('Prize', None)  # Include prize if available
                )
            )
        
        return WinningCombinationsResponse(
            combinations=combinations,
            total_count=total_count,
            has_more=(end_idx < total_count)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True) 