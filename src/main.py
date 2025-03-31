from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
import requests
import os
import json
from typing import List, Optional

from database import get_db, Player, Match, MatchStats
from process_scorecard import process_match_data
from calculate_points import FantasyPointsCalculator

app = FastAPI(title="Cricket Fantasy Points API")

# Configuration
CRICDATA_API_KEY = os.getenv("API_KEY_MAIN", "your_api_key_here")
CRICDATA_BASE_URL = "https://api.cricapi.com/v1"

def get_todays_match_id() -> str:
    """Get today's match ID from Match_data.csv"""
    df = pd.read_csv("Match_data.csv")
    df["date"] = pd.to_datetime(df["date"])
    todays_date = datetime.now().date()
    todays_match = df[df["date"].dt.date == todays_date]
    if todays_match.empty:
        raise HTTPException(status_code=404, detail="No match scheduled for today")
    return str(todays_match["match_id"].values[0])

def fetch_match_scorecard(match_id: str) -> dict:
    """Fetch match scorecard from CricData API"""
    url = f"{CRICDATA_BASE_URL}/match_scorecard"
    headers = {"Authorization": f"Bearer {CRICDATA_API_KEY}"}
    params = {
        "apikey": CRICDATA_API_KEY,
        "id": match_id,
        "offset": 0
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Match not found")
    return response.json()

def update_player_points(db: Session, match_id: str):
    """Update player points for a specific match"""
    # Fetch match data
    match_data = fetch_match_scorecard(match_id)
    
    # Process match data
    player_stats = process_match_data(match_data)
    
    # Get or create match record
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        match = Match(
            match_id=match_id,
            match_name=match_data.get('name', ''),
            match_date=datetime.strptime(match_data.get('date', ''), '%Y-%m-%d'),
            venue=match_data.get('venue', ''),
            teams=json.dumps(match_data.get('teams', []))
        )
        db.add(match)
        db.commit()
    
    # Calculate points
    calculator = FantasyPointsCalculator()
    
    # Update player stats and match stats
    for player_id, stats in player_stats.items():
        # Get or create player
        player = db.query(Player).filter(Player.player_name == stats['player_name']).first()
        if not player:
            player = Player(
                player_name=stats['player_name'],
                team=stats['team']
            )
            db.add(player)
            db.commit()
        
        # Calculate fantasy points
        points = calculator.calculate_total_points(stats)
        
        # Create match stats
        match_stats = MatchStats(
            player_id=player.id,
            match_id=match.id,
            runs=stats['runs'],
            balls_faced=stats['balls_faced'],
            fours=stats['fours'],
            sixes=stats['sixes'],
            strike_rate=stats['strike_rate'],
            dismissals=stats['dismissals'],
            dismissal_type=stats['dismissal_type'],
            dismissal_bowler=stats['dismissal_bowler'],
            overs_bowled=stats['overs_bowled'],
            maidens=stats['maidens'],
            runs_conceded=stats['runs_conceded'],
            wickets=stats['wickets'],
            no_balls=stats['no_balls'],
            wides=stats['wides'],
            economy=stats['economy'],
            catches=stats['catches'],
            stumpings=stats['stumpings'],
            run_outs=stats['run_outs'],
            total_points=points['total_points'],
            batting_points=points['batting_points'],
            bowling_points=points['bowling_points'],
            fielding_points=points['fielding_points']
        )
        db.add(match_stats)
        
        # Update player career stats
        player.matches_played += 1
        player.total_runs += stats['runs']
        player.total_balls_faced += stats['balls_faced']
        player.total_fours += stats['fours']
        player.total_sixes += stats['sixes']
        player.total_wickets += stats['wickets']
        player.total_overs_bowled += stats['overs_bowled']
        player.total_maidens += stats['maidens']
        player.total_runs_conceded += stats['runs_conceded']
        player.total_catches += stats['catches']
        player.total_stumpings += stats['stumpings']
        player.total_run_outs += stats['run_outs']
        player.total_fantasy_points += points['total_points']
    
    db.commit()

@app.get("/")
async def root():
    return {"message": "Welcome to Cricket Fantasy Points API"}

@app.get("/players/{match_id}")
async def get_match_players(match_id: str, db: Session = Depends(get_db)):
    """Get all players' points for a specific match"""
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    match_stats = db.query(MatchStats).filter(MatchStats.match_id == match.id).all()
    if not match_stats:
        raise HTTPException(status_code=404, detail="No players found for this match")
    
    return match_stats

@app.get("/player/{player_name}")
async def get_player_points(
    player_name: str,
    match_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get points for a specific player, optionally filtered by match"""
    player = db.query(Player).filter(Player.player_name == player_name).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    query = db.query(MatchStats).filter(MatchStats.player_id == player.id)
    if match_id:
        match = db.query(Match).filter(Match.match_id == match_id).first()
        if match:
            query = query.filter(MatchStats.match_id == match.id)
    
    match_stats = query.all()
    if not match_stats:
        raise HTTPException(status_code=404, detail="No match statistics found for this player")
    
    return match_stats

@app.post("/update-match/{match_id}")
async def update_match(match_id: str, db: Session = Depends(get_db)):
    """Update player points for a specific match"""
    try:
        update_player_points(db, match_id)
        return {"message": f"Successfully updated points for match {match_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-todays-match")
async def update_todays_match(db: Session = Depends(get_db)):
    """Update player points for today's match"""
    try:
        match_id = get_todays_match_id()
        update_player_points(db, match_id)
        return {"message": f"Successfully updated points for today's match {match_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 