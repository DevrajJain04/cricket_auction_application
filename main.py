#!/usr/bin/env python3
"""
Main entry point for the Cricket Data API application.
This file serves as the production entry point for web servers.
"""
import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import the FastAPI application from api.py
from src.api import app

# This code is used when running with Gunicorn
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"Starting Shroff Premier League API server on {host}:{port}...")
    uvicorn.run("main:app", host=host, port=port, reload=False)