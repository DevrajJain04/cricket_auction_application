import json ,time
import pandas as pd
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI , Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, Player, Match, MatchStats, get_db, engine
from calculate_points import FantasyPointsCalculator
import os,json,requests
from dotenv import load_dotenv
load_dotenv()
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY_DJ4499")
df = pd.read_csv("Match_data.csv")
df["date"] = pd.to_datetime(df["date"]).dt.date  # Convert to date-only format
#fetch based on match_id from get_completed_matches
def fetch_match_data(match_id: str) -> dict:
    """Fetch match data from CricData API"""
    url = f"{BASE_URL}/match_scorecard"
    params = {"apikey": API_KEY, "offset": 0,"id": match_id}
    response = requests.get(url, params=params)
    return response.json()
#yesterday tak
def get_completed_matches():
    yesterday = datetime.now().date() - pd.Timedelta(days=1)
    # today = datetime.now().date()
    return df[df["date"] <= yesterday][["id", "date"]].to_dict('records')
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
                player_stats[player_id]['dismissal_bowler'] = batsman['bowler']['name']
        
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
            return

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
            return

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

        # Process each player's stats
        for player_id, stats in player_stats.items():
            # Find or create Player
            player = db.query(Player).filter(Player.player_name == stats['player_name']).first()
            if not player:
                player = Player(
                    player_name=stats['player_name'],
                    team=stats['team']
                )
                db.add(player)
                db.commit()
                print(f"Created new player: {player.player_name}")

            # Create MatchStats record
            calculator = FantasyPointsCalculator()

            fantasy_points = calculator.calculate_total_points(stats)
            
            match_stats = MatchStats(
                player_id=player.id,
                match_id=new_match.id,
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
    finally:
        db.close()
#full pipeline to populate db till date (yet to test)
def full_populate_till_date():
    completed_matches = get_completed_matches()
    print(f"Found {len(completed_matches)} completed matches to process")
    
    for match in completed_matches:
        match_id = str(match['id'])
        match_date = match['date'].strftime('%Y-%m-%d')
        print(f"\nProcessing match {match_id} from {match_date}")
        match_data = fetch_match_data(match_id)
        input_result = process_match_data(match_data)
        populate_database(input_result)
        print(f"Successfully processed match {match_id}")
        
        time.sleep(1)  # Avoid API rate limits


app = FastAPI(title="Shroff IPL auction points calculator")

@app.get("/")
async def root():
    return {"message":"Made with care by ROYAL CHALLENGERS THALASONS"}

@app.post("/player_name")
async def fetch_player_stats(player_name):
    db = Session(engine)
    player = db.query(Player).filter(Player.player_name == player_name).first()


full_populate_till_date()