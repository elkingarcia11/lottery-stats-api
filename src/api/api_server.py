from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Optional, Annotated, Any
from pydantic import BaseModel, conlist
import sqlite3
from pathlib import Path
import random
from enum import Enum
import uvicorn

# Constants
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'lottery.db'

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

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable row factory for dict-like access
    return conn

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
        conn = get_db()
        cursor = conn.cursor()
        
        if category == 'main':
            # Get main number frequencies
            cursor.execute('''
                SELECT number, frequency, percentage
                FROM number_frequencies
                WHERE lottery_type = ?
                ORDER BY number
            ''', (lottery_type.value,))
        elif category == 'special':
            # Get special ball frequencies (position 6)
            cursor.execute('''
                SELECT number, frequency, percentage
                FROM position_frequencies
                WHERE lottery_type = ? AND position = 6
                ORDER BY number
            ''', (lottery_type.value,))
        else:
            raise HTTPException(status_code=400, detail="Invalid category. Use 'main' or 'special'")
        
        results = []
        for row in cursor.fetchall():
            results.append(NumberFrequencyResponse(
                number=row['number'],
                count=row['frequency'],
                percentage=row['percentage']
            ))
        
        conn.close()
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{lottery_type}/position-frequencies", response_model=List[PositionFrequencyResponse])
async def get_position_frequencies(
    lottery_type: LotteryType,
    position: Optional[int] = Query(None, ge=1, le=5, description="Filter by specific position (1-5)")
):
    """Get frequency statistics for numbers in each position."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT position, number, frequency, percentage
            FROM position_frequencies
            WHERE lottery_type = ? AND position < 6
        '''
        params = [lottery_type.value]
        
        if position:
            query += ' AND position = ?'
            params.append(position)
            
        query += ' ORDER BY position, number'
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append(PositionFrequencyResponse(
                position=row['position'],
                number=row['number'],
                count=row['frequency'],
                percentage=row['percentage']
            ))
        
        conn.close()
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/{lottery_type}/check-combination", response_model=CombinationResponse)
async def check_combination(lottery_type: LotteryType, request: CombinationRequest):
    """Check if a combination exists in historical data."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Convert numbers to string format for comparison
        main_numbers_str = ' '.join(map(str, sorted(request.numbers)))
        
        # Find matches based on main numbers
        cursor.execute('''
            SELECT draw_date, winning_numbers, special_ball
            FROM draws
            WHERE lottery_type = ? AND winning_numbers = ?
            ORDER BY draw_date DESC
        ''', (lottery_type.value, main_numbers_str))
        
        matches = cursor.fetchall()
        
        if not matches:
            conn.close()
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
        
        for row in matches:
            row_special_ball = row['special_ball']
            
            # If special ball is provided, mark if we found an exact match
            if request.special_ball is not None and row_special_ball == request.special_ball:
                exact_match_found = True
                
            matches_list.append({
                'date': row['draw_date'],
                'special_ball': row_special_ball,
                'prize': None  # Prize info not currently stored
            })
        
        conn.close()
        
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
            matches=matches_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{lottery_type}/generate-optimized", response_model=GeneratedCombinationResponse)
async def generate_optimized_combination(lottery_type: LotteryType):
    """Generate a combination that maximizes position-specific frequencies while ensuring it's unique."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get the maximum range for numbers based on lottery type
        max_main = 70 if lottery_type == LotteryType.mega_millions else 69
        max_special = 25 if lottery_type == LotteryType.mega_millions else 26
        
        # Get highest frequency numbers for each position
        optimized_numbers = []
        position_percentages = {}
        
        for position in range(1, 6):
            cursor.execute('''
                SELECT number, percentage
                FROM position_frequencies
                WHERE lottery_type = ? AND position = ?
                ORDER BY frequency DESC
            ''', (lottery_type.value, position))
            
            # Find the highest frequency number that isn't already selected
            for row in cursor.fetchall():
                if row['number'] not in optimized_numbers and 1 <= row['number'] <= max_main:
                    optimized_numbers.append(row['number'])
                    position_percentages[position] = row['percentage']
                    break
        
        # Get highest frequency special ball
        cursor.execute('''
            SELECT number
            FROM position_frequencies
            WHERE lottery_type = ? AND position = 6
            ORDER BY frequency DESC
            LIMIT 1
        ''', (lottery_type.value,))
        special_ball = cursor.fetchone()['number']
        
        # Check if combination exists
        main_numbers_str = ' '.join(map(str, sorted(optimized_numbers)))
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM draws
            WHERE lottery_type = ? AND winning_numbers = ? AND special_ball = ?
        ''', (lottery_type.value, main_numbers_str, special_ball))
        
        is_unique = cursor.fetchone()['count'] == 0
        
        # If not unique, try modifying the combination
        if not is_unique:
            # Try replacing the last number
            original_last = optimized_numbers[-1]
            for num in range(1, max_main + 1):
                if num not in optimized_numbers:
                    optimized_numbers[-1] = num
                    main_numbers_str = ' '.join(map(str, sorted(optimized_numbers)))
                    cursor.execute('''
                        SELECT COUNT(*) as count
                        FROM draws
                        WHERE lottery_type = ? AND winning_numbers = ? AND special_ball = ?
                    ''', (lottery_type.value, main_numbers_str, special_ball))
                    if cursor.fetchone()['count'] == 0:
                        is_unique = True
                        break
            
            # If still not unique, restore original and try different special ball
            if not is_unique:
                optimized_numbers[-1] = original_last
                for num in range(1, max_special + 1):
                    if num != special_ball:
                        cursor.execute('''
                            SELECT COUNT(*) as count
                            FROM draws
                            WHERE lottery_type = ? AND winning_numbers = ? AND special_ball = ?
                        ''', (lottery_type.value, main_numbers_str, num))
                        if cursor.fetchone()['count'] == 0:
                            special_ball = num
                            is_unique = True
                            break
        
        conn.close()
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
        conn = get_db()
        cursor = conn.cursor()
        
        # Get the maximum range for numbers based on lottery type
        max_main = 70 if lottery_type == LotteryType.mega_millions else 69
        max_special = 25 if lottery_type == LotteryType.mega_millions else 26
        
        # Generate combinations until we find a unique one
        max_attempts = 100  # Prevent infinite loop
        for _ in range(max_attempts):
            # Generate 5 unique random numbers for main numbers
            main_numbers = sorted(random.sample(range(1, max_main + 1), 5))
            special_ball = random.randint(1, max_special)
            
            # Check if this combination exists
            main_numbers_str = ' '.join(map(str, main_numbers))
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM draws
                WHERE lottery_type = ? AND winning_numbers = ? AND special_ball = ?
            ''', (lottery_type.value, main_numbers_str, special_ball))
            
            if cursor.fetchone()['count'] == 0:
                conn.close()
                return GeneratedCombinationResponse(
                    main_numbers=main_numbers,
                    special_ball=special_ball,
                    is_unique=True
                )
        
        conn.close()
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
    """Get the latest winning combinations with pagination support."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute(
            'SELECT COUNT(*) as count FROM draws WHERE lottery_type = ?',
            (lottery_type.value,)
        )
        total_count = cursor.fetchone()['count']
        
        # Calculate pagination
        offset = (page - 1) * page_size
        
        # Get paginated results
        cursor.execute('''
            SELECT draw_date, winning_numbers, special_ball
            FROM draws
            WHERE lottery_type = ?
            ORDER BY draw_date DESC
            LIMIT ? OFFSET ?
        ''', (lottery_type.value, page_size, offset))
        
        combinations = []
        for row in cursor.fetchall():
            main_numbers = [int(n) for n in row['winning_numbers'].split()]
            combinations.append(WinningCombination(
                draw_date=row['draw_date'],
                main_numbers=sorted(main_numbers),
                special_ball=row['special_ball']
            ))
        
        conn.close()
        return WinningCombinationsResponse(
            combinations=combinations,
            total_count=total_count,
            has_more=(offset + page_size < total_count)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True) 