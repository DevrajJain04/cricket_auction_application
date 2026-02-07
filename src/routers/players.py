"""
Players router for player data and search.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from models.base import get_db
from models.user import User
from models.player import Player, PlayerAlias
from auth.dependencies import get_current_active_user

# Optional: Use rapidfuzz for fuzzy matching if available
try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

router = APIRouter(prefix="/players", tags=["Players"])


# --- Pydantic Schemas ---

class PlayerSearchResult(BaseModel):
    """Player search result."""
    id: int
    player_name: str
    team: Optional[str]
    matches_played: int
    total_runs: int
    total_wickets: int
    total_fantasy_points: float
    match_score: Optional[float] = None  # Fuzzy match score

    class Config:
        from_attributes = True


# --- Endpoints ---

@router.get("/search", response_model=List[PlayerSearchResult])
async def search_players(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search for players by name with fuzzy matching.
    Handles common variations and aliases.
    """
    search_term = q.strip()
    
    # First check aliases
    alias_match = db.query(PlayerAlias).filter(
        PlayerAlias.alias.ilike(f"%{search_term}%")
    ).first()
    
    if alias_match:
        # Found an alias, get the player
        player = db.query(Player).filter(Player.id == alias_match.player_id).first()
        if player:
            return [PlayerSearchResult(
                id=player.id,
                player_name=player.player_name,
                team=player.team,
                matches_played=player.matches_played,
                total_runs=player.total_runs,
                total_wickets=player.total_wickets,
                total_fantasy_points=player.total_fantasy_points,
                match_score=100.0
            )]
    
    # Get all players for fuzzy matching
    all_players = db.query(Player).all()
    
    if FUZZY_AVAILABLE and all_players:
        # Use fuzzy matching
        player_names = [(p.id, p.player_name) for p in all_players]
        
        # Match against player names
        results = process.extract(
            search_term,
            {p[0]: p[1] for p in player_names},
            scorer=fuzz.WRatio,
            limit=limit
        )
        
        # Filter by score threshold (> 50)
        matched_ids = [r[2] for r in results if r[1] > 50]
        
        if matched_ids:
            players = db.query(Player).filter(Player.id.in_(matched_ids)).all()
            
            # Create result with scores
            id_to_score = {r[2]: r[1] for r in results}
            return [
                PlayerSearchResult(
                    id=p.id,
                    player_name=p.player_name,
                    team=p.team,
                    matches_played=p.matches_played,
                    total_runs=p.total_runs,
                    total_wickets=p.total_wickets,
                    total_fantasy_points=p.total_fantasy_points,
                    match_score=id_to_score.get(p.id, 0)
                )
                for p in sorted(players, key=lambda x: id_to_score.get(x.id, 0), reverse=True)
            ]
    
    # Fallback: Simple LIKE query
    players = db.query(Player).filter(
        Player.player_name.ilike(f"%{search_term}%")
    ).limit(limit).all()
    
    return [
        PlayerSearchResult(
            id=p.id,
            player_name=p.player_name,
            team=p.team,
            matches_played=p.matches_played,
            total_runs=p.total_runs,
            total_wickets=p.total_wickets,
            total_fantasy_points=p.total_fantasy_points
        )
        for p in players
    ]


@router.get("/{player_id}", response_model=PlayerSearchResult)
async def get_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get player details by ID."""
    from fastapi import HTTPException
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return PlayerSearchResult(
        id=player.id,
        player_name=player.player_name,
        team=player.team,
        matches_played=player.matches_played,
        total_runs=player.total_runs,
        total_wickets=player.total_wickets,
        total_fantasy_points=player.total_fantasy_points
    )


@router.post("/{player_id}/alias")
async def add_player_alias(
    player_id: int,
    alias: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add an alias for a player to improve search.
    E.g., "SKY" -> Suryakumar Yadav
    """
    from fastapi import HTTPException
    from auth.dependencies import require_admin
    
    # Only admins can add aliases
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Admin access required")
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Check if alias already exists
    existing = db.query(PlayerAlias).filter(PlayerAlias.alias == alias).first()
    if existing:
        raise HTTPException(status_code=400, detail="Alias already exists")
    
    new_alias = PlayerAlias(player_id=player_id, alias=alias)
    db.add(new_alias)
    db.commit()
    
    return {
        "message": f"Alias '{alias}' added for {player.player_name}",
        "player_id": player_id
    }
