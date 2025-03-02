#!/usr/bin/env python3
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py [analyze|api]")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "analyze":
        from src.analysis.analyze_lotteries import analyze_and_export
        analyze_and_export()
    elif command == "api":
        import uvicorn
        uvicorn.run("src.api.api_server:app", host="0.0.0.0", port=8000, reload=True)
    else:
        print("Invalid command. Use 'analyze' or 'api'")
        sys.exit(1) 