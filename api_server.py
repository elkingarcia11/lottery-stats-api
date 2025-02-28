from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
import uvicorn
from mega_millions_analysis import MegaMillionsAnalyzer
from powerball_analysis import PowerballAnalyzer

app = FastAPI(
    title="Lottery Analysis API",
    description="API for analyzing Mega Millions and Powerball lottery data",
    version="1.0.0"
)

# Initialize analyzers
mega_millions = MegaMillionsAnalyzer('mega_million.csv')
powerball = PowerballAnalyzer('powerball.csv')

# Pydantic models for request/response validation
class CombinationCheck(BaseModel):
    numbers: List[int]
    special_ball: Optional[int] = None  # For Mega Ball or Powerball

    def validate_mega_millions(self):
        if len(self.numbers) != 5:
            raise HTTPException(
                status_code=400,
                detail="Must provide exactly 5 main numbers for Mega Millions"
            )
        if not all(1 <= n <= 70 for n in self.numbers):
            raise HTTPException(
                status_code=400,
                detail="Mega Millions main numbers must be between 1 and 70"
            )
        if len(set(self.numbers)) != 5:
            raise HTTPException(
                status_code=400,
                detail="Mega Millions main numbers must be unique"
            )
        if self.special_ball is None:
            raise HTTPException(
                status_code=400,
                detail="Must provide a Mega Ball number"
            )
        if not (1 <= self.special_ball <= 25):
            raise HTTPException(
                status_code=400,
                detail="Mega Ball number must be between 1 and 25"
            )

    def validate_powerball(self):
        if len(self.numbers) != 5:
            raise HTTPException(
                status_code=400,
                detail="Must provide exactly 5 main numbers for Powerball"
            )
        if not all(1 <= n <= 69 for n in self.numbers):
            raise HTTPException(
                status_code=400,
                detail="Powerball main numbers must be between 1 and 69"
            )
        if len(set(self.numbers)) != 5:
            raise HTTPException(
                status_code=400,
                detail="Powerball main numbers must be unique"
            )
        if self.special_ball is None:
            raise HTTPException(
                status_code=400,
                detail="Must provide a Powerball number"
            )
        if not (1 <= self.special_ball <= 26):
            raise HTTPException(
                status_code=400,
                detail="Powerball number must be between 1 and 26"
            )

class LotteryResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Dict

@app.get("/")
async def root():
    return {
        "message": "Lottery Analysis API",
        "endpoints": {
            "Mega Millions": [
                "/mega-millions/frequencies",
                "/mega-millions/position-frequencies",
                "/mega-millions/megaball-frequencies",
                "/mega-millions/check-combination",
                "/mega-millions/generate-combination"
            ],
            "Powerball": [
                "/powerball/frequencies",
                "/powerball/position-frequencies",
                "/powerball/powerball-frequencies",
                "/powerball/check-combination",
                "/powerball/generate-combination"
            ]
        }
    }

# Mega Millions endpoints
@app.get("/mega-millions/frequencies")
async def get_mega_millions_frequencies():
    frequencies = mega_millions.get_general_frequencies()
    sorted_frequencies = dict(sorted(frequencies.items(), key=lambda x: x[0]))
    return LotteryResponse(
        success=True,
        data={"frequencies": sorted_frequencies}
    )

@app.get("/mega-millions/position-frequencies")
async def get_mega_millions_position_frequencies():
    frequencies = {
        f"position_{i+1}": dict(sorted(mega_millions.get_position_frequencies(i).items(), key=lambda x: x[0]))
        for i in range(5)
    }
    return LotteryResponse(
        success=True,
        data={"position_frequencies": frequencies}
    )

@app.get("/mega-millions/megaball-frequencies")
async def get_mega_millions_megaball_frequencies():
    frequencies = mega_millions.get_megaball_frequencies()
    sorted_frequencies = dict(sorted(frequencies.items(), key=lambda x: x[0]))
    return LotteryResponse(
        success=True,
        data={"megaball_frequencies": sorted_frequencies}
    )

@app.post("/mega-millions/check-combination")
async def check_mega_millions_combination(combo: CombinationCheck):
    combo.validate_mega_millions()
    result = mega_millions.check_combination(combo.numbers, combo.special_ball)
    return LotteryResponse(
        success=True,
        data=result
    )

@app.get("/mega-millions/generate-combination")
async def generate_mega_millions_combination():
    result = mega_millions.generate_unique_combination()
    if "error" in result:
        return LotteryResponse(
            success=False,
            message=result["error"],
            data={}
        )
    return LotteryResponse(
        success=True,
        data=result
    )

@app.get("/mega-millions/latest")
async def get_mega_millions_latest(limit: int = 100):
    """
    Get the latest Mega Millions winning numbers.
    
    Args:
        limit: Number of recent results to return (default 100)
    """
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 1000"
        )
    
    results = mega_millions.get_latest_numbers(limit)
    return LotteryResponse(
        success=True,
        data={"latest_numbers": results}
    )

# Powerball endpoints
@app.get("/powerball/frequencies")
async def get_powerball_frequencies():
    frequencies = powerball.get_general_frequencies()
    sorted_frequencies = dict(sorted(frequencies.items(), key=lambda x: x[0]))
    return LotteryResponse(
        success=True,
        data={"frequencies": sorted_frequencies}
    )

@app.get("/powerball/position-frequencies")
async def get_powerball_position_frequencies():
    frequencies = {
        f"position_{i+1}": dict(sorted(powerball.get_position_frequencies(i).items(), key=lambda x: x[0]))
        for i in range(5)
    }
    return LotteryResponse(
        success=True,
        data={"position_frequencies": frequencies}
    )

@app.get("/powerball/powerball-frequencies")
async def get_powerball_specific_frequencies():
    frequencies = powerball.get_powerball_frequencies()
    sorted_frequencies = dict(sorted(frequencies.items(), key=lambda x: x[0]))
    return LotteryResponse(
        success=True,
        data={"powerball_frequencies": sorted_frequencies}
    )

@app.post("/powerball/check-combination")
async def check_powerball_combination(combo: CombinationCheck):
    combo.validate_powerball()
    # For Powerball, we need to combine the numbers with the special ball
    all_numbers = combo.numbers + [combo.special_ball]
    result = powerball.check_combination(all_numbers)
    return LotteryResponse(
        success=True,
        data=result
    )

@app.get("/powerball/generate-combination")
async def generate_powerball_combination():
    result = powerball.generate_unique_combination()
    if "error" in result:
        return LotteryResponse(
            success=False,
            message=result["error"],
            data={}
        )
    return LotteryResponse(
        success=True,
        data=result
    )

@app.get("/powerball/latest")
async def get_powerball_latest(limit: int = 100):
    """
    Get the latest Powerball winning numbers.
    
    Args:
        limit: Number of recent results to return (default 100)
    """
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 1000"
        )
    
    results = powerball.get_latest_numbers(limit)
    return LotteryResponse(
        success=True,
        data={"latest_numbers": results}
    )

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True) 