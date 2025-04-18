import json ,time
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import FastAPI , Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, Player, Match, MatchStats, PlayerTransfer, Shroff_teams, TeamPlayer, get_db, engine
from calculate_points import FantasyPointsCalculator
import os,json,requests
from typing import List, Dict, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY_PRADNYAPTI")

# Get the path to Match_data.csv in the root directory
project_root = Path(__file__).parent.parent
match_data_path = project_root / "Match_data.csv"
df = pd.read_csv(match_data_path)
df["date"] = pd.to_datetime(df["date"]).dt.date  # Convert to date-only format

class PlayerResponse(BaseModel):
    id: int
    player_name: str
    team: str
    matches_played: int
    total_runs: int
    total_wickets: int
    total_fantasy_points: float
    
    class Config:
        from_attributes = True  # This enables ORM mode for Pydantic v2

class TeamResponse(BaseModel):
    id: int
    team_name: str
    team_code: str
    purse_remaining: float


#fetch based on match_id from get_completed_matches
def fetch_match_data(match_id: str) -> dict:
    """Fetch match data from CricData API"""
    try:
        url = f"{BASE_URL}/match_scorecard"
        params = {"apikey": API_KEY, "offset": 0,"id": match_id}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching match data for {match_id}: {str(e)}")
        return {"status": "error", "message": str(e)}
#yesterday tak
def get_completed_matches():
    yesterday = datetime.now().date() - timedelta(days=1)
    # today = datetime.now().date()
    return df[df["date"] <= yesterday][["id", "date"]].to_dict('records')

def get_yesterdays_match():
    """Get match data for yesterday's date from Match_data.csv"""
    yesterday = datetime.now().date() - timedelta(days=1)
    matches = df[df["date"] == yesterday][["id", "date"]].to_dict('records')
    print(f"Found {len(matches)} matches for {yesterday}")
    return matches

#10 10 match ke set yaha se load karlo per api key
def get_10_matches():
    # Updated to return a single match at index 10
    return df[30:33][["id", "date"]].to_dict('records')
#aaj ka match
def todays_match(match_id):
    today = datetime.now().date()
    return df[df["date"] == today][["id","date"]].to_dict('records')
#called in pop_db for player_stats
def process_match_data(match_data):
    player_stats = defaultdict(lambda: {
        'player_name': '',
        'team': '',
        'matches': 1,
        'batting_innings': 0,
        'runs': 0,
        'balls_faced': 0,
        'fours': 0,
        'sixes': 0,
        'strike_rate': 0,
        'dismissals': 0,
        'dismissal_type': '',
        'dismissal_bowler': '',
        'bowling_innings': 0,
        'overs_bowled': 0,
        'maidens': 0,
        'runs_conceded': 0,
        'wickets': 0,
        'no_balls': 0,
        'wides': 0,
        'economy': 0,
        'catches': 0,
        'stumpings': 0,
        'run_outs': 0,
        'match_id': match_data['id'],
        'match_name': match_data['name'],
        'match_date': match_data['date'],
        'venue': match_data['venue']
    })
    
    teams = match_data['teams']
    
    for innings in match_data['scorecard']:
        batting_team = innings['inning'].split(' Inning')[0]
        bowling_team = teams[1] if batting_team == teams[0] else teams[0]
        
        # Process batting stats
        for batsman in innings['batting']:
            player_id = batsman['batsman']['id']
            player_name = batsman['batsman']['name']
            
            player_stats[player_id]['player_name'] = player_name
            player_stats[player_id]['team'] = batting_team
            player_stats[player_id]['batting_innings'] += 1
            player_stats[player_id]['runs'] += batsman['r']
            player_stats[player_id]['balls_faced'] += batsman['b']
            player_stats[player_id]['fours'] += batsman['4s']
            player_stats[player_id]['sixes'] += batsman['6s']
            player_stats[player_id]['strike_rate'] = batsman['sr']
            
            if 'dismissal' in batsman:
                player_stats[player_id]['dismissals'] += 1
                player_stats[player_id]['dismissal_type'] = batsman['dismissal']
                # Check if bowler exists before accessing it (for run-outs, etc.)
                if 'bowler' in batsman and batsman['bowler'] is not None:
                    player_stats[player_id]['dismissal_bowler'] = batsman['bowler']['name']
                else:
                    player_stats[player_id]['dismissal_bowler'] = ''
        
        # Process bowling stats
        for bowler in innings['bowling']:
            player_id = bowler['bowler']['id']
            player_name = bowler['bowler']['name']
            
            player_stats[player_id]['player_name'] = player_name
            player_stats[player_id]['team'] = bowling_team
            player_stats[player_id]['bowling_innings'] += 1
            player_stats[player_id]['overs_bowled'] += bowler['o']
            player_stats[player_id]['maidens'] += bowler['m']
            player_stats[player_id]['runs_conceded'] += bowler['r']
            player_stats[player_id]['wickets'] += bowler['w']
            player_stats[player_id]['no_balls'] += bowler['nb']
            player_stats[player_id]['wides'] += bowler['wd']
            player_stats[player_id]['economy'] = bowler['eco']
        
        # Process fielding stats
        for fielder in innings['catching']:
            if 'catcher' in fielder:
                player_id = fielder['catcher']['id']
                player_name = fielder['catcher']['name']
                
                player_stats[player_id]['player_name'] = player_name
                player_stats[player_id]['team'] = bowling_team
                player_stats[player_id]['catches'] += fielder['catch']
                player_stats[player_id]['stumpings'] += fielder['stumped']
                player_stats[player_id]['run_outs'] += fielder['runout']
    
    return player_stats
#pops_db based on player_stats
def populate_database(input_result):
    db = Session(engine)

    try:
        if input_result['status'] != 'success':
            print("Error: The input data indicates an unsuccessful request")
            return False

        match_data = input_result['data']
        player_stats = process_match_data(match_data)
        
        # Print sample data for verification
        print("\nSample processed player stats (first 3 players):")
        for i, (player_id, stats) in enumerate(list(player_stats.items())[:3]):
            print(f"\nPlayer {i+1}:")
            print(f"Name: {stats['player_name']}")
            print(f"Team: {stats['team']}")
            print(f"Runs: {stats['runs']}, Wickets: {stats['wickets']}")
            print(f"Catches: {stats['catches']}, Run Outs: {stats['run_outs']}")
            print("---")

        # Check if match already exists
        existing_match = db.query(Match).filter(Match.match_id == match_data['id']).first()
        if existing_match:
            print(f"\nMatch {match_data['id']} already exists in database")
            return True  # Return True since this isn't an error

        # Create Match record
        match_date = datetime.strptime(match_data['date'], "%Y-%m-%d")
        new_match = Match(
            match_id=match_data['id'],
            match_name=match_data['name'],
            match_date=match_date,
            venue=match_data['venue'],
            teams=json.dumps(match_data['teams'])
        )
        db.add(new_match)
        db.commit()
        db.refresh(new_match)
        print(f"\nCreated new match record: {new_match.match_name}")

        # Initialize Shroff teams if they don't exist
        if db.query(Shroff_teams).count() == 0:
            team_names = [
                "Royal Challengers Thalasons",
                "Shroff Superwizards Supergiants Snakes",
                "Shroff Conquerers", 
                "Rising Shroff Supergiants",
                "Bumrah Brigadiers",
                "Lalu ki Fauj"
            ]
            for i, name in enumerate(team_names):
                team_code = name.split()[-1][:3].upper()
                # Check if team code already exists
                if db.query(Shroff_teams).filter(Shroff_teams.team_code == team_code).first():
                    print(f"Team code {team_code} already exists!")
                    return False
                
                team = Shroff_teams(
                    team_name=name,
                    team_code=team_code,
                    purse=100.0
                )
                db.add(team)
            db.commit()
            print("Initialized Shroff teams")

        # Process each player's stats
        for player_id, stats in player_stats.items():
            # Find or create Player
            player = db.query(Player).filter(Player.player_name == stats['player_name']).first()
            if not player:
                player = Player(
                    player_name=stats['player_name'],
                    team=stats['team'],
                    matches_played=0,
                    total_runs=0,
                    total_balls_faced=0,
                    total_fours=0,
                    total_sixes=0,
                    total_wickets=0,
                    total_overs_bowled=0,
                    total_maidens=0,
                    total_runs_conceded=0,
                    total_catches=0,
                    total_stumpings=0,
                    total_run_outs=0,
                    total_fantasy_points=0
                )
                db.add(player)
                db.commit()
                print(f"Created new player: {player.player_name}")

            # Create MatchStats record
            calculator = FantasyPointsCalculator()
            fantasy_points = calculator.calculate_total_points(stats)
            if stats['player_name'] in calculator.bowlers_bonus:
                fantasy_points['bowling_points'] += calculator.bowlers_bonus[stats['player_name']]     #adding the bonus of getting players out on stumping/bowled/lbw etc.
                fantasy_points['total_points'] += calculator.bowlers_bonus[stats['player_name']]       #to make sure total is also updated since total is calculated inside the calculator only 
            match_stats = MatchStats(
                player_id=player.id,
                match_id=new_match.id,
                player_name = stats['player_name'],
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
                total_points=fantasy_points['total_points'],
                batting_points=fantasy_points['batting_points'],
                bowling_points=fantasy_points['bowling_points'],
                fielding_points=fantasy_points['fielding_points']
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
            player.total_fantasy_points += fantasy_points['total_points']

        db.commit()
        print("\nSuccessfully updated database with match data")

        # Verification: Print example records
        print("\nVerification - Example records:")
        
        # Example Player record
        sample_player = db.query(Player).order_by(Player.id.desc()).first()
        print(f"\nPlayer Record: {sample_player.player_name}")
        print(f"Matches: {sample_player.matches_played}")
        print(f"Total Runs: {sample_player.total_runs}")
        print(f"Total Wickets: {sample_player.total_wickets}")
        
        # Example MatchStats record
        sample_stats = db.query(MatchStats).order_by(MatchStats.id.desc()).first()
        print(f"\nMatch Stats Record:")
        print(f"Player: {sample_stats.player.player_name}")
        print(f"Match: {sample_stats.match.match_name}")
        print(f"Runs: {sample_stats.runs}, Wickets: {sample_stats.wickets}")
        print(f"Points: Total={sample_stats.total_points}, Batting={sample_stats.batting_points}")

    except Exception as e:
        db.rollback()
        print(f"Error processing data: {str(e)}")
        return False  # Stop on any exception
    finally:
        db.close()
        return True
#full pipeline to populate db till date (yet to test)
def full_populate_till_date():
    try:
        completed_matches = get_10_matches()
        print(f"Found {len(completed_matches)} completed matches to process")
        
        for match in completed_matches:
            try:
                match_id = str(match['id'])
                match_date = match['date'].strftime('%Y-%m-%d')
                print(f"\nProcessing match {match_id} from {match_date}")
                
                # Fetch match data from API
                match_data = fetch_match_data(match_id)
                
                if match_data.get("status") == "error":
                    print(f"Error fetching match {match_id}: {match_data.get('message')}")
                    return False  # Stop on API error
                
                success = populate_database(match_data)
                
                if not success:
                    print("Stopping due to processing error")
                    return False  # Stop on processing error
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing match {match_id}: {str(e)}")
                return False  # Stop on any exception
                
        return True
        
    except Exception as e:
        print(f"Database population failed: {str(e)}")
        return False


if __name__ == "__main__":
    import uvicorn
    try:
        print("Attempting to populate database with historical matches...")
        full_populate_till_date()
    except Exception as e:
        print(f"Database population failed: {str(e)}")
        print("Continuing with API server startup...")