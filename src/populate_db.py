import pandas as pd
from datetime import datetime
import time
import json
import requests
from database import Match, MatchStats, Player, SessionLocal
from process_scorecard import process_match_data
from calculate_points import FantasyPointsCalculator

# Configuration
API_KEY = "0c1560fd-4f5d-41cf-a90d-b965813560df"  # Replace with your actual API key
BASE_URL = "https://api.cricapi.com/v1"

# def fetch_match_data(match_id: str) -> dict:
#     """Fetch match data from CricData API"""
#     url = f"{BASE_URL}/match_scorecard"
#     params = {"apikey": API_KEY, "offset": 0,"id": match_id}
#     response = requests.get(url, params=params)
#     return response.json()

def get_completed_matches():
    """Get list of completed matches from Match_data.csv"""
    df = pd.read_csv("Match_data.csv")
    df["date"] = pd.to_datetime(df["date"]).dt.date  # Convert to date-only format
    yesterday = datetime.now().date() - pd.Timedelta(days=1)
    # today = datetime.now().date()
    return df[df["date"] <= yesterday][["id", "date"]].to_dict('records')

def process_and_store_match(db, match_id: str, match_data: dict):
    """Process match data and store in database"""
    player_stats = process_match_data(match_data)
    match_date_str = match_data.get('date', '') # Extract only the date
    
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        match = Match(
            match_id=match_id,
            match_name=match_data.get('name', ''),
            match_date=datetime.strptime(match_date_str, '%Y-%m-%d'),
            venue=match_data.get('venue', ''),
            teams=json.dumps(match_data.get('teams', []))
        )
        db.add(match)
        db.commit()
    
    calculator = FantasyPointsCalculator()
    
    for player_id, stats in player_stats.items():
        player = db.query(Player).filter(Player.player_name == stats['player_name']).first()
        if not player:
            player = Player(player_name=stats['player_name'], team=stats['team'])
            db.add(player)
            db.commit()
        
        points = calculator.calculate_total_points(stats)
        
        match_stats = MatchStats(
            player_id=player.id,
            match_id=match.id,
            runs=stats.get('runs', 0),
            balls_faced=stats.get('balls_faced', 0),
            fours=stats.get('fours', 0),
            sixes=stats.get('sixes', 0),
            strike_rate=stats.get('strike_rate', 0.0),
            dismissals=stats.get('dismissals', 0),
            dismissal_type=stats.get('dismissal_type', ''),
            dismissal_bowler=stats.get('dismissal_bowler', ''),
            overs_bowled=stats.get('overs_bowled', 0.0),
            maidens=stats.get('maidens', 0),
            runs_conceded=stats.get('runs_conceded', 0),
            wickets=stats.get('wickets', 0),
            no_balls=stats.get('no_balls', 0),
            wides=stats.get('wides', 0),
            economy=stats.get('economy', 0.0),
            catches=stats.get('catches', 0),
            stumpings=stats.get('stumpings', 0),
            run_outs=stats.get('run_outs', 0),
            total_points=points['total_points'],
            batting_points=points['batting_points'],
            bowling_points=points['bowling_points'],
            fielding_points=points['fielding_points']
        )
        db.add(match_stats)
        
        player.matches_played += 1
        player.total_runs += stats.get('runs', 0)
        player.total_balls_faced += stats.get('balls_faced', 0)
        player.total_fours += stats.get('fours', 0)
        player.total_sixes += stats.get('sixes', 0)
        player.total_wickets += stats.get('wickets', 0)
        player.total_overs_bowled += stats.get('overs_bowled', 0.0)
        player.total_maidens += stats.get('maidens', 0)
        player.total_runs_conceded += stats.get('runs_conceded', 0)
        player.total_catches += stats.get('catches', 0)
        player.total_stumpings += stats.get('stumpings', 0)
        player.total_run_outs += stats.get('run_outs', 0)
        player.total_fantasy_points += points['total_points']
    
    db.commit()

def populate_database():
    """Populate database with historical match data"""
    db = SessionLocal()
    try:
        completed_matches = get_completed_matches()
        print(f"Found {len(completed_matches)} completed matches to process")
        
        for match in completed_matches:
            match_id = str(match['id'])
            match_date = match['date'].strftime('%Y-%m-%d')
            print(f"\nProcessing match {match_id} from {match_date}")
            with open("response.json", "r") as f:
                input_result = json.loads(f.read())
            match_data = input_result#fetch_match_data(match_id)
            process_and_store_match(db, match_id, match_data)
            print(f"Successfully processed match {match_id}")
            
            time.sleep(1)  # Avoid API rate limits
        
        print("\nDatabase population completed!")
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting database population...")
    populate_database()
