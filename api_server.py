from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Optional
from pydantic import BaseModel, conlist
from mega_millions_analysis import MegaMillionsAnalysis
from powerball_analysis import PowerballAnalysis
from enum import Enum
import uvicorn
import random

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
    numbers: conlist(int, min_items=5, max_items=5)  # Exactly 5 numbers
    special_ball: Optional[int] = None

class CombinationResponse(BaseModel):
    exists: bool
    frequency: int
    dates: List[str]
    main_numbers: List[int]
    special_ball: Optional[int]

class GeneratedCombinationResponse(BaseModel):
    main_numbers: List[int]
    special_ball: int
    position_percentages: Optional[Dict[int, float]] = None
    is_unique: bool

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
        
        return [
            NumberFrequencyResponse(
                number=number,
                count=freq.count,
                percentage=freq.percentage
            )
            for number, freq in frequencies.items()
        ]
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
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/{lottery_type}/check-combination", response_model=CombinationResponse)
async def check_combination(
    lottery_type: LotteryType,
    combination: CombinationRequest
):
    """Check if a combination exists in historical data."""
    try:
        analysis = mega_millions if lottery_type == LotteryType.mega_millions else powerball
        stats = analysis.get_analysis()
        
        # Validate number ranges based on lottery type
        if lottery_type == LotteryType.mega_millions:
            if any(n < 1 or n > 70 for n in combination.numbers):
                raise HTTPException(status_code=400, detail="Mega Millions main numbers must be between 1 and 70")
            if combination.special_ball and (combination.special_ball < 1 or combination.special_ball > 25):
                raise HTTPException(status_code=400, detail="Mega Ball must be between 1 and 25")
        else:
            if any(n < 1 or n > 69 for n in combination.numbers):
                raise HTTPException(status_code=400, detail="Powerball main numbers must be between 1 and 69")
            if combination.special_ball and (combination.special_ball < 1 or combination.special_ball > 26):
                raise HTTPException(status_code=400, detail="Powerball must be between 1 and 26")
        
        # Check if numbers are unique
        if len(set(combination.numbers)) != 5:
            raise HTTPException(status_code=400, detail="Main numbers must be unique")
        
        # Sort numbers for consistency
        sorted_numbers = tuple(sorted(combination.numbers))
        
        # Check main numbers only or full combination
        if combination.special_ball is None:
            frequencies = stats['number_combination_frequencies']
            combo_key = sorted_numbers
        else:
            frequencies = stats['full_combination_frequencies']
            combo_key = tuple(list(sorted_numbers) + [combination.special_ball])
        
        # Find the combination and its dates
        freq_stats = frequencies.get(combo_key)
        if freq_stats:
            # Find dates when this combination occurred
            dates = []
            for _, row in analysis.df.iterrows():
                row_numbers = sorted([int(n) for n in row['Winning Numbers'].split()])
                row_special = int(row[analysis.special_ball_column]) if combination.special_ball else None
                
                if row_numbers == list(sorted_numbers):
                    if combination.special_ball is None or row_special == combination.special_ball:
                        dates.append(row['Draw Date'])
            
            return CombinationResponse(
                exists=True,
                frequency=freq_stats.count,
                dates=dates,
                main_numbers=list(sorted_numbers),
                special_ball=combination.special_ball
            )
        else:
            return CombinationResponse(
                exists=False,
                frequency=0,
                dates=[],
                main_numbers=list(sorted_numbers),
                special_ball=combination.special_ball
            )
            
    except HTTPException:
        raise
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

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True) 