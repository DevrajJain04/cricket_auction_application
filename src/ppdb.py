import json ,time
import pandas as pd
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI , Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, Player, Match, MatchStats, PlayerTransfer, Shroff_teams, TeamPlayer, get_db, engine
from calculate_points import FantasyPointsCalculator
import os,json,requests
from typing import List, Dict, Optional
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY_DJ4499")
df = pd.read_csv("Match_data.csv")
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
    yesterday = datetime.now().date() - pd.Timedelta(days=9)
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
            fantasy_points['bowling_points'] += calculator.bowlers_bonus(stats)       #adding the bonus of getting players out on stumping/bowled/lbw etc.
            fantasy_points['total_points'] += calculator.bowlers_bonus(stats)         #to make sure total is also updated since total is calculated inside the calculator only 
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
        completed_matches = get_completed_matches()
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


app = FastAPI(title="Shroff IPL auction points calculator")

@app.get("/")
async def root():
    return {"message":"Made with care by ROYAL CHALLENGERS THALASONS"}

# Player endpoints
@app.get("/players", response_model=List[PlayerResponse])
async def get_all_players(db: Session = Depends(get_db)):
    try:
        players = db.query(Player).all()
        
        # Convert SQLAlchemy model objects to dictionaries
        player_list = []
        for player in players:
            player_list.append({
                "id": player.id,
                "player_name": player.player_name,
                "team": player.team,
                "matches_played": player.matches_played,
                "total_runs": player.total_runs,
                "total_wickets": player.total_wickets,
                "total_fantasy_points": player.total_fantasy_points
            })
        
        return player_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}", response_model=dict)
async def get_player(player_id: int, db: Session = Depends(get_db)):
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Convert Player object to dictionary for proper serialization
        player_data = {
            "id": player.id,
            "player_name": player.player_name,
            "team": player.team,
            "matches_played": player.matches_played,
            "total_runs": player.total_runs,
            "total_wickets": player.total_wickets,
            "total_fantasy_points": player.total_fantasy_points
            # Add any other fields you need
        }
        
        return player_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Get player match stats
    match_stats = db.query(MatchStats).filter(MatchStats.player_id == player_id).all()
    
    # Get player team history
    team_history = db.query(TeamPlayer).filter(TeamPlayer.player_id == player_id).all()
    
    return {
        "player": player,
        "match_stats": match_stats,
        "team_history": team_history
    }

@app.get("/players/name/{player_name}", response_model=dict)
async def get_player_by_name(player_name: str, db: Session = Depends(get_db)):
    """Get player details by name"""
    player = db.query(Player).filter(Player.player_name == player_name).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get player match stats
    match_stats = db.query(MatchStats).filter(MatchStats.player_id == player.id).all()
    
    # Get player team history
    team_history = db.query(TeamPlayer).filter(TeamPlayer.player_id == player.id).all()
    
    return {
        "player": player,
        "match_stats": match_stats,
        "team_history": team_history
    }

# Team endpoints
@app.get("/teams", response_model=list)
async def get_all_teams(db: Session = Depends(get_db)):
    """Get all fantasy teams"""
    teams = db.query(Shroff_teams).all()
    return teams

@app.get("/team/{team_id}", response_model=TeamResponse)
async def get_team(team_id: int, db: Session = Depends(get_db)):
    try:
        team = db.query(Shroff_teams).filter(Shroff_teams.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Get current team players
    current_players = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.left_at_match == None
    ).all()
    
    # Get team transfer history
    transfers = db.query(PlayerTransfer).filter(
        (PlayerTransfer.from_team_id == team_id) | (PlayerTransfer.to_team_id == team_id)
    ).order_by(PlayerTransfer.transfer_at_match).all()
    
    return {
        "team": team,
        "current_players": current_players,
        "transfers": transfers
    }

@app.get("/teams/code/{team_code}", response_model=dict)
async def get_team_by_code(team_code: str, db: Session = Depends(get_db)):
    """Get team details by team code"""
    team = db.query(Shroff_teams).filter(Shroff_teams.team_code == team_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get current team players
    current_players = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team.id,
        TeamPlayer.left_at_match == None
    ).all()
    
    # Get team transfer history
    transfers = db.query(PlayerTransfer).filter(
        (PlayerTransfer.from_team_id == team.id) | (PlayerTransfer.to_team_id == team.id)
    ).order_by(PlayerTransfer.transfer_at_match).all()
    
    return {
        "team": team,
        "current_players": current_players,
        "transfers": transfers
    }

# Fantasy points endpoints
@app.get("/fantasy/match/{match_id}", response_model=dict)
async def get_fantasy_points_by_match(match_id: int, db: Session = Depends(get_db)):
    """Get fantasy points for all teams for a specific match"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    teams = db.query(Shroff_teams).all()
    team_points = []
    
    for team in teams:
        # Get team players for this match
        team_players = db.query(TeamPlayer).filter(
            TeamPlayer.team_id == team.id,
            TeamPlayer.joined_at_match <= match_id,
            (TeamPlayer.left_at_match == None) | (TeamPlayer.left_at_match > match_id)
        ).all()
        
        total_points = 0
        player_points = []
        
        for tp in team_players:
            # Get player match stats
            match_stat = db.query(MatchStats).filter(
                MatchStats.player_id == tp.player_id,
                MatchStats.match_id == match_id
            ).first()
            
            if match_stat:
                # Apply captain/vice-captain multiplier
                multiplier = 2.0 if tp.is_captain else (1.5 if tp.is_vice_captain else 1.0)
                points = match_stat.total_points * multiplier
                
                player_points.append({
                    "player_id": tp.player_id,
                    "player_name": tp.player.player_name,
                    "is_captain": tp.is_captain,
                    "is_vice_captain": tp.is_vice_captain,
                    "base_points": match_stat.total_points,
                    "multiplier": multiplier,
                    "total_points": points
                })
                
                total_points += points
        
        team_points.append({
            "team_id": team.id,
            "team_name": team.team_name,
            "team_code": team.team_code,
            "total_points": total_points,
            "players": player_points
        })
    
    return {
        "match": match,
        "team_points": team_points
    }

@app.get("/fantasy/leaderboard", response_model=list)
async def get_fantasy_leaderboard(db: Session = Depends(get_db)):
    """Get overall fantasy points leaderboard for all teams"""
    teams = db.query(Shroff_teams).all()
    leaderboard = []
    
    for team in teams:
        # Calculate total points across all matches
        total_points = 0
        matches_played = 0
        
        # Get all matches
        matches = db.query(Match).order_by(Match.match_date).all()
        match_points = []
        
        for match in matches:
            # Get team players for this match
            team_players = db.query(TeamPlayer).filter(
                TeamPlayer.team_id == team.id,
                TeamPlayer.joined_at_match <= match.id,
                (TeamPlayer.left_at_match == None) | (TeamPlayer.left_at_match > match.id)
            ).all()
            
            match_total = 0
            
            for tp in team_players:
                # Get player match stats
                match_stat = db.query(MatchStats).filter(
                    MatchStats.player_id == tp.player_id,
                    MatchStats.match_id == match.id
                ).first()
                
                if match_stat:
                    # Apply captain/vice-captain multiplier
                    multiplier = 2.0 if tp.is_captain else (1.5 if tp.is_vice_captain else 1.0)
                    match_total += match_stat.total_points * multiplier
            
            if match_total > 0:
                matches_played += 1
                total_points += match_total
                match_points.append({
                    "match_id": match.id,
                    "match_name": match.match_name,
                    "points": match_total
                })
        
        leaderboard.append({
            "team_id": team.id,
            "team_name": team.team_name,
            "team_code": team.team_code,
            "total_points": total_points,
            "matches_played": matches_played,
            "average_points": total_points / matches_played if matches_played > 0 else 0,
            "match_points": match_points
        })
    
    # Sort leaderboard by total points descending
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    return leaderboard

# Team management endpoints
@app.post("/teams/{team_id}/add_player", response_model=dict)
async def add_player_to_team(
    team_id: int,
    player_id: int,
    is_captain: bool = False,
    is_vice_captain: bool = False,
    price: float = 0,
    match_id: int = None,
    db: Session = Depends(get_db)
):
    """Add a player to a team"""
    try:
        # Validate team exists
        team = db.query(Shroff_teams).filter(Shroff_teams.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Validate player exists
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get current match if not specified
        if not match_id:
            latest_match = db.query(Match).order_by(Match.match_date.desc()).first()
            if not latest_match:
                raise HTTPException(status_code=400, detail="No matches found in database")
            match_id = latest_match.id
        
        # Check if player is already in team
        existing_player = db.query(TeamPlayer).filter(
            TeamPlayer.team_id == team_id,
            TeamPlayer.player_id == player_id,
            TeamPlayer.left_at_match == None
        ).first()
        
        if existing_player:
            raise HTTPException(status_code=400, detail="Player already in team")
        
        # Check purse balance
        if price > team.purse_remaining:
            raise HTTPException(status_code=400, detail="Insufficient purse balance")
        
        # Add player to team
        new_team_player = TeamPlayer(
            team_id=team_id,
            player_id=player_id,
            joined_at_match=match_id,
            is_captain=is_captain,
            is_vice_captain=is_vice_captain,
            price=price
        )
        
        # Update team purse
        team.purse_remaining -= price
        
        db.add(new_team_player)
        db.commit()
        
        return {
            "message": "Player added to team successfully",
            "player_id": player_id,
            "team_id": team_id,
            "purse_remaining": team.purse_remaining
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/teams/{team_id}/remove_player", response_model=dict)
async def remove_player_from_team(
    team_id: int,
    player_id: int,
    match_id: int = None,
    db: Session = Depends(get_db)
):
    """Remove a player from a team"""
    try:
        # Validate team exists
        team = db.query(Shroff_teams).filter(Shroff_teams.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get current match if not specified
        if not match_id:
            latest_match = db.query(Match).order_by(Match.match_date.desc()).first()
            if not latest_match:
                raise HTTPException(status_code=400, detail="No matches found in database")
            match_id = latest_match.id
        
        # Find active team player record
        team_player = db.query(TeamPlayer).filter(
            TeamPlayer.team_id == team_id,
            TeamPlayer.player_id == player_id,
            TeamPlayer.left_at_match == None
        ).first()
        
        if not team_player:
            raise HTTPException(status_code=404, detail="Player not found in team")
        
        # Mark player as left
        team_player.left_at_match = match_id
        
        # Refund 50% of purchase price to purse
        refund_amount = team_player.price * 0.5
        team.purse_remaining += refund_amount
        
        db.commit()
        
        return {
            "message": "Player removed from team successfully",
            "player_id": player_id,
            "team_id": team_id,
            "refund_amount": refund_amount,
            "purse_remaining": team.purse_remaining
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/teams/{team_id}/update_captain", response_model=dict)
async def update_captain(
    team_id: int,
    player_id: int,
    is_captain: bool,
    is_vice_captain: bool = False,
    db: Session = Depends(get_db)
):
    """Update captain/vice-captain status for a player"""
    try:
        # Validate team exists
        team = db.query(Shroff_teams).filter(Shroff_teams.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Find active team player record
        team_player = db.query(TeamPlayer).filter(
            TeamPlayer.team_id == team_id,
            TeamPlayer.player_id == player_id,
            TeamPlayer.left_at_match == None
        ).first()
        
        if not team_player:
            raise HTTPException(status_code=404, detail="Player not found in team")
        
        # Update captain status
        team_player.is_captain = is_captain
        team_player.is_vice_captain = is_vice_captain
        
        db.commit()
        
        return {
            "message": "Captain status updated successfully",
            "player_id": player_id,
            "is_captain": is_captain,
            "is_vice_captain": is_vice_captain
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Trade endpoints
@app.post("/trades/create", response_model=dict)
async def create_trade(
    from_team_id: int,
    to_team_id: int,
    player_id: int,
    price: float = 0,
    match_id: int = None,
    db: Session = Depends(get_db)
):
    """Trade a player between teams"""
    try:
        # Validate teams exist
        from_team = db.query(Shroff_teams).filter(Shroff_teams.id == from_team_id).first()
        to_team = db.query(Shroff_teams).filter(Shroff_teams.id == to_team_id).first()
        if not from_team or not to_team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Validate player exists
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get current match if not specified
        if not match_id:
            latest_match = db.query(Match).order_by(Match.match_date.desc()).first()
            if not latest_match:
                raise HTTPException(status_code=400, detail="No matches found in database")
            match_id = latest_match.id
        
        # Check if player is in from_team
        from_team_player = db.query(TeamPlayer).filter(
            TeamPlayer.team_id == from_team_id,
            TeamPlayer.player_id == player_id,
            TeamPlayer.left_at_match == None
        ).first()
        
        if not from_team_player:
            raise HTTPException(status_code=400, detail="Player not in source team")
        
        # Check if to_team has enough purse
        if price > to_team.purse_remaining:
            raise HTTPException(status_code=400, detail="Destination team has insufficient purse")
        
        # Create trade record
        trade = PlayerTransfer(
            from_team_id=from_team_id,
            to_team_id=to_team_id,
            player_id=player_id,
            transfer_at_match=match_id,
            price=price
        )
        
        # Remove player from from_team
        from_team_player.left_at_match = match_id
        
        # Add player to to_team
        new_team_player = TeamPlayer(
            team_id=to_team_id,
            player_id=player_id,
            joined_at_match=match_id,
            is_captain=False,
            is_vice_captain=False,
            price=price
        )
        
        # Update purses
        from_team.purse_remaining += price
        to_team.purse_remaining -= price
        
        db.add(trade)
        db.add(new_team_player)
        db.commit()
        
        return {
            "message": "Trade completed successfully",
            "player_id": player_id,
            "from_team_id": from_team_id,
            "to_team_id": to_team_id,
            "price": price,
            "from_team_purse": from_team.purse_remaining,
            "to_team_purse": to_team.purse_remaining
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Try to populate database but continue even if it fails
    try:
        print("Attempting to populate database with historical matches...")
        full_populate_till_date()
    except Exception as e:
        print(f"Database population failed: {str(e)}")
        print("Continuing with API server startup...")
    
    # Start the API server
    print("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)