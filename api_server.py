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
    special_ball: Optional[int] = None  # For Mega Millions separate input

class LotteryResponse(BaseModel):
    success: bool
    data: Dict
    message: str = ""

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
    return LotteryResponse(
        success=True,
        data={"frequencies": frequencies}
    )

@app.get("/mega-millions/position-frequencies")
async def get_mega_millions_position_frequencies():
    frequencies = {
        f"position_{i+1}": mega_millions.get_position_frequencies(i)
        for i in range(5)
    }
    return LotteryResponse(
        success=True,
        data={"position_frequencies": frequencies}
    )

@app.get("/mega-millions/megaball-frequencies")
async def get_mega_millions_megaball_frequencies():
    frequencies = mega_millions.get_megaball_frequencies()
    return LotteryResponse(
        success=True,
        data={"megaball_frequencies": frequencies}
    )

@app.post("/mega-millions/check-combination")
async def check_mega_millions_combination(combo: CombinationCheck):
    if len(combo.numbers) != 5 or combo.special_ball is None:
        raise HTTPException(
            status_code=400,
            detail="Must provide 5 main numbers and 1 Mega Ball number"
        )
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

# Powerball endpoints
@app.get("/powerball/frequencies")
async def get_powerball_frequencies():
    frequencies = powerball.get_general_frequencies()
    return LotteryResponse(
        success=True,
        data={"frequencies": frequencies}
    )

@app.get("/powerball/position-frequencies")
async def get_powerball_position_frequencies():
    frequencies = {
        f"position_{i+1}": powerball.get_position_frequencies(i)
        for i in range(5)
    }
    return LotteryResponse(
        success=True,
        data={"position_frequencies": frequencies}
    )

@app.get("/powerball/powerball-frequencies")
async def get_powerball_specific_frequencies():
    frequencies = powerball.get_powerball_frequencies()
    return LotteryResponse(
        success=True,
        data={"powerball_frequencies": frequencies}
    )

@app.post("/powerball/check-combination")
async def check_powerball_combination(combo: CombinationCheck):
    if len(combo.numbers) != 6:
        raise HTTPException(
            status_code=400,
            detail="Must provide 6 numbers (5 main numbers + Powerball)"
        )
    result = powerball.check_combination(combo.numbers)
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

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True) 