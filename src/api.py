# src/api.py
import os
import sys
from typing import List, Optional
from decimal import Decimal # Import Decimal

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case # Import func and case
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Add src directory to Python path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    # Ensure Match is imported for joining
    from database import SessionLocal, Player, Shroff_teams, TeamPlayer, MatchStats, Match, get_db
except ImportError as e:
    print(f"Error importing database modules: {e}")
    print("Ensure database.py is in the src directory and contains all models.")
    sys.exit(1)

# --- Pydantic Models ---

class PlayerBase(BaseModel):
    id: int
    player_name: str
    team: Optional[str] = None # IPL team

    class Config:
        from_attributes = True # ORM mode

class TeamPlayerInfo(BaseModel):
    player: PlayerBase
    bought_for: float
    is_captain: bool
    is_vice_captain: bool

    class Config:
        from_attributes = True

class ShroffTeamDetails(BaseModel):
    id: int
    team_name: str
    team_code: str
    purse_remaining: float
    players: List[TeamPlayerInfo]

    class Config:
        from_attributes = True

class UnsoldPlayer(PlayerBase):
    pass # Inherits fields from PlayerBase

# New Models for Team Player Stats
class TeamPlayerAggregatedStats(BaseModel):
    player: PlayerBase
    matches_for_team: int
    total_runs: int
    total_wickets: int
    total_catches: int
    total_stumpings: int
    total_run_outs: int
    total_points: float
    total_batting_points: float
    total_bowling_points: float
    total_fielding_points: float

class TeamStatsResponse(BaseModel):
    team_id: int
    team_name: str
    team_code: str
    player_aggregated_stats: List[TeamPlayerAggregatedStats]

# --- FastAPI App ---

app = FastAPI(title="Shroff Premier League API", version="1.0.0")

# --- CORS Middleware ---
origins = ["*"] # Allow all origins for dev

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---

def calculate_player_stats_for_team(db: Session, team_player: TeamPlayer) -> Optional[TeamPlayerAggregatedStats]:
    """
    Calculates aggregated stats for a player during their tenure with a specific team.
    """
    if not team_player.player:
        print(f"Warning: TeamPlayer {team_player.id} has no associated Player.")
        return None

    # Base query for MatchStats joined with Match
    stats_query = db.query(
        func.count(MatchStats.id).label("matches_for_team"),
        func.sum(MatchStats.runs).label("total_runs"),
        func.sum(MatchStats.wickets).label("total_wickets"),
        func.sum(MatchStats.catches).label("total_catches"),
        func.sum(MatchStats.stumpings).label("total_stumpings"),
        func.sum(MatchStats.run_outs).label("total_run_outs"),
        func.sum(MatchStats.total_points).label("total_points"),
        func.sum(MatchStats.batting_points).label("total_batting_points"),
        func.sum(MatchStats.bowling_points).label("total_bowling_points"),
        func.sum(MatchStats.fielding_points).label("total_fielding_points")
    ).join(Match).filter(MatchStats.player_id == team_player.player_id)

    # Filter stats based on player's tenure in the team
    stats_query = stats_query.filter(Match.id >= team_player.joined_at_match)
    if team_player.left_at_match is not None:
        # If player left, only include matches strictly BEFORE leaving match id
        # Assuming left_at_match means they didn't play *that* match for the team
        stats_query = stats_query.filter(Match.id < team_player.left_at_match)

    aggregated_stats = stats_query.first()

    # Handle case where player played 0 matches for the team in the recorded stats
    if aggregated_stats.matches_for_team == 0:
         return TeamPlayerAggregatedStats(
            player=PlayerBase.model_validate(team_player.player),
            matches_for_team=0,
            total_runs=0,
            total_wickets=0,
            total_catches=0,
            total_stumpings=0,
            total_run_outs=0,
            total_points=0.0,
            total_batting_points=0.0,
            total_bowling_points=0.0,
            total_fielding_points=0.0
        )


    # Convert sums which might be None (if no stats) or Decimal to float/int
    # SQLAlchemy func.sum might return Decimal, handle potential None as 0
    def safe_convert(value, target_type):
        if value is None:
            return target_type(0)
        # Convert Decimal to float, otherwise direct conversion
        return float(value) if isinstance(value, Decimal) and target_type is float else target_type(value)

    return TeamPlayerAggregatedStats(
        player=PlayerBase.model_validate(team_player.player),
        matches_for_team=safe_convert(aggregated_stats.matches_for_team, int),
        total_runs=safe_convert(aggregated_stats.total_runs, int),
        total_wickets=safe_convert(aggregated_stats.total_wickets, int),
        total_catches=safe_convert(aggregated_stats.total_catches, int),
        total_stumpings=safe_convert(aggregated_stats.total_stumpings, int),
        total_run_outs=safe_convert(aggregated_stats.total_run_outs, int),
        total_points=safe_convert(aggregated_stats.total_points, float),
        total_batting_points=safe_convert(aggregated_stats.total_batting_points, float),
        total_bowling_points=safe_convert(aggregated_stats.total_bowling_points, float),
        total_fielding_points=safe_convert(aggregated_stats.total_fielding_points, float)
    )


# --- API Endpoints ---

@app.get("/")
async def root():
    return {"message": "Welcome to the Shroff Premier League API"}

@app.get("/teams/", response_model=List[ShroffTeamDetails])
async def get_all_shroff_teams(db: Session = Depends(get_db)):
    """
    Retrieves details for all Shroff teams, including their current roster.
    """
    try:
        # Eager load players and their associated player details
        teams = db.query(Shroff_teams).options(
            joinedload(Shroff_teams.players).joinedload(TeamPlayer.player)
        ).all()
        result = []

        for team in teams:
            player_details = []
            for tp in team.players:
                # Only include current players
                if tp.left_at_match is None and tp.player:
                    player_info = PlayerBase.model_validate(tp.player)
                    team_player_info = TeamPlayerInfo(
                        player=player_info,
                        bought_for=tp.bought_for,
                        is_captain=tp.is_captain,
                        is_vice_captain=tp.is_vice_captain
                    )
                    player_details.append(team_player_info)
                elif tp.left_at_match is None and not tp.player:
                     print(f"Warning: TeamPlayer record {tp.id} is missing related Player {tp.player_id}")


            team_details = ShroffTeamDetails(
                id=team.id,
                team_name=team.team_name,
                team_code=team.team_code,
                purse_remaining=team.purse,
                players=player_details
            )
            result.append(team_details)

        return result
    except Exception as e:
        print(f"Error fetching teams: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error retrieving team data")


@app.get("/players/unsold/", response_model=List[UnsoldPlayer])
async def get_unsold_players(db: Session = Depends(get_db)):
    """
    Retrieves a list of players who are not currently assigned to any Shroff team.
    """
    try:
        # Get IDs of all players currently assigned to a team
        assigned_player_ids_query = db.query(TeamPlayer.player_id).filter(
            TeamPlayer.left_at_match == None
        ).distinct()
        assigned_player_ids = {pid for (pid,) in assigned_player_ids_query.all()}

        # Query players whose IDs are NOT in the assigned set
        unsold_players_query = db.query(Player).filter(
            Player.id.notin_(assigned_player_ids)
        )
        unsold_players = unsold_players_query.all()

        return [UnsoldPlayer.model_validate(player) for player in unsold_players]

    except Exception as e:
        print(f"Error fetching unsold players: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error retrieving unsold player data")


@app.get("/teams/{team_id}/player_stats/", response_model=TeamStatsResponse)
async def get_team_player_stats(team_id: int, db: Session = Depends(get_db)):
    """
    Retrieves aggregated match statistics for players currently on a specific Shroff team,
    considering only the matches played during their tenure with that team.
    """
    try:
        # Fetch the team, eagerly loading current players and their player details
        team = db.query(Shroff_teams).options(
            joinedload(Shroff_teams.players).joinedload(TeamPlayer.player)
        ).filter(Shroff_teams.id == team_id).first()

        if not team:
            raise HTTPException(status_code=404, detail=f"Shroff Team with ID {team_id} not found")

        aggregated_stats_list = []
        for tp in team.players:
            # Process only current players
            if tp.left_at_match is None:
                player_stats = calculate_player_stats_for_team(db, tp)
                if player_stats:
                    aggregated_stats_list.append(player_stats)

        return TeamStatsResponse(
            team_id=team.id,
            team_name=team.team_name,
            team_code=team.team_code,
            player_aggregated_stats=aggregated_stats_list
        )

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions to let FastAPI handle them
        raise http_exc
    except Exception as e:
        print(f"Error fetching player stats for team {team_id}: {e}")
        # Log the full error traceback for debugging if possible
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error retrieving team player stats")


if __name__ == "__main__":
    import uvicorn
    print("Starting Shroff Premier League API server...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
