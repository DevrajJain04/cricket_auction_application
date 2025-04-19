# src/api.py
import os
import sys
from typing import List, Optional
from decimal import Decimal # Import Decimal

from fastapi import Depends, FastAPI, HTTPException, Body
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, case, and_ # Import func, case, and_
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
# Add src directory to Python path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    # Ensure all relevant models are imported
    from database import (
        SessionLocal, Player, Shroff_teams, TeamPlayer,
        MatchStats, Match, PlayerTransfer, get_db, engine # Added PlayerTransfer
    )
except ImportError as e:
    print(f"Error importing database modules: {e}")
    print("Ensure database.py is in the src directory and contains all models.")
    sys.exit(1)

# --- Pydantic Models ---

# --- Existing Models ---
class PlayerBase(BaseModel):
    id: int
    player_name: str
    team: Optional[str] = None # IPL team

    class Config:
        from_attributes = True

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
    pass

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

# --- New Models for Management API ---

class TradeRequest(BaseModel):
    from_team_id: int
    to_team_id: int
    player_id: int
    match_id: int # Match ID *after* which the trade becomes effective
    transfer_fee: float = Field(0.0, ge=0.0, description="Amount paid by to_team to from_team")

class ReleaseRequest(BaseModel):
    team_id: int
    player_id: int
    match_id: int # Match ID *after* which the release becomes effective

class BuyRequest(BaseModel):
    team_id: int
    player_id: int
    match_id: int # Match ID *after* which the buy becomes effective
    purchase_price: float = Field(..., ge=0.0, description="Price paid by the team to acquire the player")

class ActionResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None


# --- FastAPI App ---
app = FastAPI(title="Shroff Premier League API", version="1.1.0") # Updated version

# --- CORS Middleware ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions (Existing + New) ---

def get_current_player_ids(db: Session) -> set:
    """Returns a set of player IDs currently active on any Shroff team."""
    assigned_player_ids_query = db.query(TeamPlayer.player_id).filter(
        TeamPlayer.left_at_match == None
    ).distinct()
    return {pid for (pid,) in assigned_player_ids_query.all()}

# --- calculate_player_stats_for_team (Keep existing) ---
def calculate_player_stats_for_team(db: Session, team_player: TeamPlayer) -> Optional[TeamPlayerAggregatedStats]:
    """
    Calculates aggregated stats for a player during their tenure with a specific team.
    Takes into account captain/vice-captain multipliers for points.
    """
    if not team_player.player:
        print(f"Warning: TeamPlayer {team_player.id} has no associated Player.")
        return None

    # Get the multiplier based on captain status
    multiplier = 2.0 if team_player.is_captain else (1.5 if team_player.is_vice_captain else 1.0)
    
    # Base query for MatchStats joined with Match
    stats_query = db.query(
        func.count(MatchStats.id).label("matches_for_team"),
        func.sum(MatchStats.runs).label("total_runs"),
        func.sum(MatchStats.wickets).label("total_wickets"),
        func.sum(MatchStats.catches).label("total_catches"),
        func.sum(MatchStats.stumpings).label("total_stumpings"),
        func.sum(MatchStats.run_outs).label("total_run_outs"),
        # Multiply points by the appropriate factor for captain/vice-captain
        func.sum(MatchStats.total_points * multiplier).label("total_points"),
        func.sum(MatchStats.batting_points * multiplier).label("total_batting_points"),
        func.sum(MatchStats.bowling_points * multiplier).label("total_bowling_points"),
        func.sum(MatchStats.fielding_points * multiplier).label("total_fielding_points")
    ).join(Match).filter(MatchStats.player_id == team_player.player_id)

    # Filter stats based on player's tenure in the team
    stats_query = stats_query.filter(Match.id >= team_player.joined_at_match)
    if team_player.left_at_match is not None:
        # If player left, only include matches strictly BEFORE leaving match id
        stats_query = stats_query.filter(Match.id < team_player.left_at_match)

    aggregated_stats = stats_query.first()

    # Handle case where player played 0 matches for the team in the recorded stats
    if not aggregated_stats or aggregated_stats.matches_for_team == 0:
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

    # Helper function to safely convert values
    def safe_convert(value, target_type):
        if value is None:
            return target_type(0)
        try:
            # Convert Decimal to float if needed
            if isinstance(value, Decimal) and target_type is float:
                return float(value)
            return target_type(value)
        except (TypeError, ValueError):
            print(f"Warning: Could not convert {value} to {target_type}. Using 0.")
            return target_type(0)

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


# --- API Endpoints (Existing + New) ---

@app.get("/")
async def root():
    return {"message": "Welcome to the Shroff Premier League API"}

# --- /teams/ (GET) - Keep Existing ---
@app.get("/teams/", response_model=List[ShroffTeamDetails])
async def get_all_shroff_teams(db: Session = Depends(get_db)):
    # ... (previous implementation remains unchanged) ...
    try:
        teams = db.query(Shroff_teams).options(
            selectinload(Shroff_teams.players).selectinload(TeamPlayer.player) # Use selectinload
        ).all()
        result = []
        for team in teams:
            player_details = []
            for tp in team.players:
                if tp.left_at_match is None and tp.player:
                    player_info = PlayerBase.model_validate(tp.player)
                    team_player_info = TeamPlayerInfo(
                        player=player_info, bought_for=tp.bought_for,
                        is_captain=tp.is_captain, is_vice_captain=tp.is_vice_captain
                    )
                    player_details.append(team_player_info)
                elif tp.left_at_match is None and not tp.player:
                     print(f"Warning: TeamPlayer record {tp.id} is missing related Player {tp.player_id}")
            team_details = ShroffTeamDetails(
                id=team.id, team_name=team.team_name, team_code=team.team_code,
                purse_remaining=team.purse, players=player_details
            )
            result.append(team_details)
        return result
    except Exception as e:
        print(f"Error fetching teams: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error retrieving team data")


# --- /players/unsold/ (GET) - Keep Existing ---
@app.get("/players/unsold/", response_model=List[UnsoldPlayer])
async def get_unsold_players(db: Session = Depends(get_db)):
    # ... (previous implementation remains unchanged) ...
     try:
        assigned_player_ids = get_current_player_ids(db)
        unsold_players_query = db.query(Player).filter(Player.id.notin_(assigned_player_ids))
        unsold_players = unsold_players_query.all()
        return [UnsoldPlayer.model_validate(player) for player in unsold_players]
     except Exception as e:
        print(f"Error fetching unsold players: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error retrieving unsold player data")

# --- /teams/{team_id}/player_stats/ (GET) - Keep Existing ---
@app.get("/teams/{team_id}/player_stats/", response_model=TeamStatsResponse)
async def get_team_player_stats(team_id: int, db: Session = Depends(get_db)):
    # ... (previous implementation remains unchanged) ...
    try:
        team = db.query(Shroff_teams).options(
             selectinload(Shroff_teams.players).selectinload(TeamPlayer.player) # Use selectinload
        ).filter(Shroff_teams.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail=f"Shroff Team with ID {team_id} not found")

        aggregated_stats_list = []
        for tp in team.players:
            if tp.left_at_match is None: # Only current players
                player_stats = calculate_player_stats_for_team(db, tp)
                if player_stats:
                    aggregated_stats_list.append(player_stats)

        return TeamStatsResponse(
            team_id=team.id, team_name=team.team_name, team_code=team.team_code,
            player_aggregated_stats=aggregated_stats_list
        )
    except HTTPException as http_exc: raise http_exc
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error retrieving team player stats")


# --- New Management Endpoints ---

@app.post("/trades/", response_model=ActionResponse)
async def execute_trade(trade_data: TradeRequest, db: Session = Depends(get_db)):
    """
    Executes a player trade between two Shroff teams.
    """
    if trade_data.from_team_id == trade_data.to_team_id:
         raise HTTPException(status_code=400, detail="Cannot trade a player to the same team.")

    try:
        # Use a transaction
        with db.begin_nested(): # Use nested transaction or manage manually
            # --- Validation ---
            from_team = db.query(Shroff_teams).filter(Shroff_teams.id == trade_data.from_team_id).with_for_update().first()
            to_team = db.query(Shroff_teams).filter(Shroff_teams.id == trade_data.to_team_id).with_for_update().first()
            player = db.query(Player).filter(Player.id == trade_data.player_id).first()

            if not from_team or not to_team:
                raise HTTPException(status_code=404, detail="One or both teams not found.")
            if not player:
                raise HTTPException(status_code=404, detail="Player not found.")

            # Find the player's current active record in the from_team
            current_team_player = db.query(TeamPlayer).filter(
                TeamPlayer.team_id == trade_data.from_team_id,
                TeamPlayer.player_id == trade_data.player_id,
                TeamPlayer.left_at_match == None
            ).with_for_update().first()

            if not current_team_player:
                raise HTTPException(status_code=400, detail=f"Player {player.player_name} is not currently active in team {from_team.team_name}.")

            # Check purse if fee > 0
            if trade_data.transfer_fee > 0 and Decimal(str(to_team.purse)) < Decimal(str(trade_data.transfer_fee)):
                 raise HTTPException(status_code=400, detail=f"{to_team.team_name} has insufficient purse ({to_team.purse}) for transfer fee ({trade_data.transfer_fee}).")

            # --- Execution ---
            # Mark player as left from the original team
            current_team_player.left_at_match = trade_data.match_id

            # Add player to the new team
            new_team_player = TeamPlayer(
                team_id=trade_data.to_team_id,
                player_id=trade_data.player_id,
                joined_at_match=trade_data.match_id, # Joins after this match
                bought_for=trade_data.transfer_fee, # Cost for the new team is the fee
                is_captain=False, # Reset captain status on trade
                is_vice_captain=False
            )
            db.add(new_team_player)

            # Update purses (using Decimal for precision)
            from_team.purse = float(Decimal(str(from_team.purse)) + Decimal(str(trade_data.transfer_fee)))
            to_team.purse = float(Decimal(str(to_team.purse)) - Decimal(str(trade_data.transfer_fee)))

            # Create PlayerTransfer record
            transfer_record = PlayerTransfer(
                player_id=trade_data.player_id,
                from_team_id=trade_data.from_team_id,
                to_team_id=trade_data.to_team_id,
                transfer_amount=trade_data.transfer_fee,
                transfer_type="trade",
                transfer_at_match=trade_data.match_id
            )
            db.add(transfer_record)

            db.flush() # Ensure IDs are generated if needed

        db.commit() # Commit the transaction

        return ActionResponse(
            success=True,
            message=f"Player {player.player_name} traded from {from_team.team_name} to {to_team.team_name}.",
            details={
                "player_id": player.id,
                "from_team_id": from_team.id,
                "to_team_id": to_team.id,
                "transfer_fee": trade_data.transfer_fee,
                "from_team_new_purse": from_team.purse,
                "to_team_new_purse": to_team.purse,
                "match_id": trade_data.match_id
            }
        )

    except HTTPException as http_exc:
        db.rollback() # Rollback on validation errors too
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"Error during trade: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error during trade.")


@app.post("/teams/{team_id}/release_player/", response_model=ActionResponse)
async def release_player(team_id: int, release_data: ReleaseRequest, db: Session = Depends(get_db)):
    """
    Releases a player from a Shroff team, making them available and refunding 50% cost.
    """
    if team_id != release_data.team_id:
        raise HTTPException(status_code=400, detail="Team ID in URL path does not match Team ID in request body.")

    try:
        with db.begin_nested():
            # --- Validation ---
            team = db.query(Shroff_teams).filter(Shroff_teams.id == team_id).with_for_update().first()
            player = db.query(Player).filter(Player.id == release_data.player_id).first()

            if not team:
                raise HTTPException(status_code=404, detail="Team not found.")
            if not player:
                raise HTTPException(status_code=404, detail="Player not found.")

            # Find the player's current active record in the team
            current_team_player = db.query(TeamPlayer).filter(
                TeamPlayer.team_id == team_id,
                TeamPlayer.player_id == release_data.player_id,
                TeamPlayer.left_at_match == None
            ).with_for_update().first()

            if not current_team_player:
                 raise HTTPException(status_code=400, detail=f"Player {player.player_name} is not currently active in team {team.team_name}.")

            # --- Execution ---
            # Mark player as left
            current_team_player.left_at_match = release_data.match_id

            # Calculate and add refund (50% of bought_for price)
            refund_amount = Decimal(str(current_team_player.bought_for)) * Decimal('0.5')
            team.purse = float(Decimal(str(team.purse)) + refund_amount)

            # No PlayerTransfer record for release refund

            db.flush()

        db.commit()

        return ActionResponse(
            success=True,
            message=f"Player {player.player_name} released from {team.team_name}.",
             details={
                "player_id": player.id,
                "team_id": team.id,
                "refund_amount": float(refund_amount),
                "team_new_purse": team.purse,
                "match_id": release_data.match_id
            }
        )

    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"Error during release: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error during release.")


@app.post("/teams/{team_id}/buy_player/", response_model=ActionResponse)
async def buy_player(team_id: int, buy_data: BuyRequest, db: Session = Depends(get_db)):
    """
    Buys an available (unsold or released) player for a Shroff team.
    """
    if team_id != buy_data.team_id:
        raise HTTPException(status_code=400, detail="Team ID in URL path does not match Team ID in request body.")

    try:
        with db.begin_nested():
            # --- Validation ---
            team = db.query(Shroff_teams).filter(Shroff_teams.id == team_id).with_for_update().first()
            player = db.query(Player).filter(Player.id == buy_data.player_id).first()

            if not team:
                raise HTTPException(status_code=404, detail="Team not found.")
            if not player:
                 raise HTTPException(status_code=404, detail="Player not found.")

            # Check if player is currently active on ANY team
            current_assignments = db.query(TeamPlayer).filter(
                TeamPlayer.player_id == buy_data.player_id,
                TeamPlayer.left_at_match == None
            ).first()

            if current_assignments:
                 other_team = db.query(Shroff_teams).filter(Shroff_teams.id == current_assignments.team_id).first()
                 raise HTTPException(status_code=400, detail=f"Player {player.player_name} is currently active in another team ({other_team.team_name if other_team else 'Unknown Team'}). Cannot buy.")

            # Check purse
            if Decimal(str(team.purse)) < Decimal(str(buy_data.purchase_price)):
                 raise HTTPException(status_code=400, detail=f"{team.team_name} has insufficient purse ({team.purse}) to buy player for ({buy_data.purchase_price}).")

            # --- Execution ---
            # Add player to the team
            new_team_player = TeamPlayer(
                team_id=team_id,
                player_id=buy_data.player_id,
                joined_at_match=buy_data.match_id, # Joins after this match
                bought_for=buy_data.purchase_price, # Cost for the team
                is_captain=False,
                is_vice_captain=False
            )
            db.add(new_team_player)

            # Update purse
            team.purse = float(Decimal(str(team.purse)) - Decimal(str(buy_data.purchase_price)))

            # Create PlayerTransfer record
            transfer_record = PlayerTransfer(
                player_id=buy_data.player_id,
                from_team_id=None, # Coming from the 'market' / unsold pool
                to_team_id=team_id,
                transfer_amount=buy_data.purchase_price,
                transfer_type="buy", # Or "mini-auction" if you prefer
                transfer_at_match=buy_data.match_id
            )
            db.add(transfer_record)

            db.flush()

        db.commit()

        return ActionResponse(
            success=True,
            message=f"Player {player.player_name} bought by {team.team_name}.",
            details={
                "player_id": player.id,
                "team_id": team.id,
                "purchase_price": buy_data.purchase_price,
                "team_new_purse": team.purse,
                "match_id": buy_data.match_id
            }
        )

    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"Error during buy: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error during buy.")


@app.post("/teams/{team_id}/update_captain/", response_model=ActionResponse)
async def update_team_captain(
    team_id: int, 
    captain_data: dict = Body(..., example={
        "player_id": 123,
        "is_captain": True,
        "is_vice_captain": False,
        "effective_match_id": 5  # Match ID after which this change becomes effective
    }),
    db: Session = Depends(get_db)
):
    """
    Updates the captain or vice-captain status for a player on a team.
    
    Only one player can be captain and only one can be vice-captain.
    When a player is made captain, any existing captain is demoted.
    When a player is made vice-captain, any existing vice-captain is demoted.
    """
    player_id = captain_data.get("player_id")
    is_captain = captain_data.get("is_captain", False)
    is_vice_captain = captain_data.get("is_vice_captain", False)
    effective_match_id = captain_data.get("effective_match_id")
    
    if not player_id:
        raise HTTPException(status_code=400, detail="player_id is required")
    
    if not effective_match_id:
        raise HTTPException(status_code=400, detail="effective_match_id is required")
        
    if is_captain and is_vice_captain:
        raise HTTPException(status_code=400, detail="A player cannot be both captain and vice-captain")
        
    try:
        with db.begin_nested():
            # Validate team exists
            team = db.query(Shroff_teams).filter(Shroff_teams.id == team_id).first()
            if not team:
                raise HTTPException(status_code=404, detail=f"Team with ID {team_id} not found")
                
            # Validate player exists and is on the team
            player_on_team = db.query(TeamPlayer).filter(
                TeamPlayer.team_id == team_id,
                TeamPlayer.player_id == player_id,
                TeamPlayer.left_at_match == None
            ).with_for_update().first()
            
            if not player_on_team:
                player = db.query(Player).filter(Player.id == player_id).first()
                if player:
                    raise HTTPException(status_code=400, detail=f"Player {player.player_name} is not active on this team")
                else:
                    raise HTTPException(status_code=404, detail=f"Player with ID {player_id} not found")
            
            # Get player name for messages
            player_name = db.query(Player.player_name).filter(Player.id == player_id).scalar()
            
            # Handle captain status changes
            if is_captain:
                # Remove captain status from any existing captain
                current_captain = db.query(TeamPlayer).filter(
                    TeamPlayer.team_id == team_id,
                    TeamPlayer.is_captain == True,
                    TeamPlayer.left_at_match == None,
                    TeamPlayer.player_id != player_id  # Don't update the target player yet
                ).with_for_update().first()
                
                if current_captain:
                    current_captain.is_captain = False
                    current_captain_name = db.query(Player.player_name).filter(
                        Player.id == current_captain.player_id).scalar()
                    print(f"Removed captain status from {current_captain_name}")
            
            # Handle vice-captain status changes
            if is_vice_captain:
                # Remove vice-captain status from any existing vice-captain
                current_vice = db.query(TeamPlayer).filter(
                    TeamPlayer.team_id == team_id,
                    TeamPlayer.is_vice_captain == True,
                    TeamPlayer.left_at_match == None,
                    TeamPlayer.player_id != player_id  # Don't update the target player yet
                ).with_for_update().first()
                
                if current_vice:
                    current_vice.is_vice_captain = False
                    current_vice_name = db.query(Player.player_name).filter(
                        Player.id == current_vice.player_id).scalar()
                    print(f"Removed vice-captain status from {current_vice_name}")
            
            # Update the target player
            player_on_team.is_captain = is_captain
            player_on_team.is_vice_captain = is_vice_captain
            
            db.flush()
            
        db.commit()
        
        new_role = "captain" if is_captain else ("vice-captain" if is_vice_captain else "regular player")
        
        return ActionResponse(
            success=True,
            message=f"Updated {player_name} to {new_role} for {team.team_name}",
            details={
                "team_id": team_id,
                "player_id": player_id,
                "is_captain": is_captain,
                "is_vice_captain": is_vice_captain,
                "effective_match_id": effective_match_id
            }
        )
        
    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"Error updating captain status: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/teams/{team_id}/total_points/", response_model=dict)
async def get_team_total_points(team_id: int, db: Session = Depends(get_db)):
    """
    Calculate the total fantasy points for a team, applying captain/vice-captain multipliers.
    Points are summed only for matches where players were part of the team.
    Captain points are doubled, vice-captain points are multiplied by 1.5.
    """
    try:
        # Verify team exists
        team = db.query(Shroff_teams).filter(Shroff_teams.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail=f"Team with ID {team_id} not found")
        
        # Get all players who have ever been on this team (including past players)
        team_players = db.query(TeamPlayer).filter(
            TeamPlayer.team_id == team_id
        ).all()
        
        total_team_points = 0.0
        player_contributions = []
        
        # Process each player's contribution
        for tp in team_players:
            # Calculate the correct multiplier based on captain status
            multiplier = 2.0 if tp.is_captain else (1.5 if tp.is_vice_captain else 1.0)
            
            # Query for matches this player played while on the team
            match_stats_query = db.query(
                MatchStats, 
                Match.id.label("match_id"),
                Match.match_name.label("match_name"),
                MatchStats.total_points.label("base_points")
            ).join(
                Match, MatchStats.match_id == Match.id
            ).filter(
                MatchStats.player_id == tp.player_id,
                Match.id >= tp.joined_at_match
            )
            
            # Filter by left_at_match if the player has left
            if tp.left_at_match is not None:
                match_stats_query = match_stats_query.filter(Match.id < tp.left_at_match)
            
            match_stats = match_stats_query.all()
            
            player_total_points = 0.0
            match_details = []
            
            # Sum up points with multiplier applied
            for stat in match_stats:
                base_points = stat.base_points or 0
                match_points = base_points * multiplier
                player_total_points += match_points
                
                match_details.append({
                    "match_id": stat.match_id,
                    "match_name": stat.match_name,
                    "base_points": base_points,
                    "multiplier": multiplier,
                    "total_points": match_points
                })
            
            # Only include players who scored points
            if player_total_points > 0:
                player = db.query(Player).filter(Player.id == tp.player_id).first()
                player_name = player.player_name if player else f"Unknown Player ({tp.player_id})"
                
                player_contributions.append({
                    "player_id": tp.player_id,
                    "player_name": player_name,
                    "is_captain": tp.is_captain,
                    "is_vice_captain": tp.is_vice_captain,
                    "total_points": player_total_points,
                    "matches": match_details
                })
                
                total_team_points += player_total_points
        
        # Sort player contributions by points (highest first)
        player_contributions.sort(key=lambda p: p["total_points"], reverse=True)
        
        return {
            "team_id": team_id,
            "team_name": team.team_name,
            "team_code": team.team_code,
            "total_points": total_team_points,
            "player_contributions": player_contributions
        }
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error calculating team points: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/admin/run-daily-update/", response_model=ActionResponse)
async def trigger_daily_update(api_key: str = Body(..., embed=True)):
    """
    Trigger the daily update process manually or via a scheduled task.
    Protected by API key to prevent unauthorized access.
    
    This endpoint can be called by Render's cron service to run the daily update at 1 AM.
    """
    # Verify API key
    expected_key = os.getenv("API_KEY_DRAVEN")
    if not expected_key or api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Import and run the daily update
        from daily_update import run_daily_update
        processed_count = run_daily_update()
        
        return ActionResponse(
            success=True,
            message=f"Daily update completed successfully. Processed {processed_count} matches.",
            details={
                "matches_processed": processed_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        print(f"Error running daily update: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during daily update: {str(e)}")


# --- Main Execution Block ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Shroff Premier League API server...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
