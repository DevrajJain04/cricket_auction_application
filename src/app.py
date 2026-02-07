"""
Shroff Premier League Cricket Auction Application
Main FastAPI application entry point.
"""
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Import routers
from routers.auth import router as auth_router
from routers.auctions import router as auctions_router
from routers.teams import router as teams_router
from routers.players import router as players_router
from routers.admin import router as admin_router
from auction.websocket import router as websocket_router

# Import models to ensure tables are created
from models.base import init_db

# Create FastAPI app
app = FastAPI(
    title="Cricket Auction Platform API",
    description="Real-time auction platform for IPL fantasy leagues and community cricket",
    version="2.0.0"
)

# CORS middleware
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    init_db()


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Cricket Auction Platform API",
        "version": "2.0.0",
        "docs": "/docs"
    }


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Register routers
app.include_router(auth_router)
app.include_router(auctions_router)
app.include_router(teams_router)
app.include_router(players_router)
app.include_router(admin_router)
app.include_router(websocket_router)


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"Starting Cricket Auction Platform API on {host}:{port}...")
    uvicorn.run("app:app", host=host, port=port, reload=True)
