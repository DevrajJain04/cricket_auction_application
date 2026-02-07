"""
Teams router for team CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from models.base import get_db
from models.user import User
from models.team import Team, TeamPlayer
from models.auction import AuctionEvent, AuctionTeamAuth, AuctionPlayer
from auth.dependencies import get_current_active_user, require_manager

router = APIRouter(prefix="/auctions/{auction_id}/teams", tags=["Teams"])


# --- Pydantic Schemas ---

class TeamCreate(BaseModel):
    """Schema for creating a team."""
    team_name: str = Field(..., min_length=2, max_length=50)
    team_code: str = Field(..., min_length=2, max_length=10)
    team_color: Optional[str] = None


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    team_name: Optional[str] = Field(None, min_length=2, max_length=50)
    team_code: Optional[str] = Field(None, min_length=2, max_length=10)
    team_color: Optional[str] = None


class TeamResponse(BaseModel):
    """Team response schema."""
    id: int
    team_name: str
    team_code: str
    team_color: Optional[str]
    owner_id: int
    initial_purse: float
    purse_remaining: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class TeamPlayerResponse(BaseModel):
    """Team player info."""
    id: int
    player_name: str
    is_captain: bool
    is_vice_captain: bool
    bought_for: float


class TeamDetailResponse(TeamResponse):
    """Team with player list."""
    players: List[TeamPlayerResponse] = []


# --- Endpoints ---

@router.get("/", response_model=List[TeamResponse])
async def list_teams(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all teams in an auction."""
    # Verify auction exists
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    teams = db.query(Team).filter(Team.auction_id == auction_id).all()
    return teams


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    auction_id: int,
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a team in an auction.
    User must be authorized by admin for this auction.
    """
    # Verify auction exists
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Check if auction is still in draft
    if auction.status not in ("draft", "paused"):
        raise HTTPException(status_code=400, detail="Cannot create team - auction is not in draft or paused status")
    
    # Check authorization - admin/owner can always create, others need auth
    if not current_user.is_admin() and auction.owner_id != current_user.id:
        auth = db.query(AuctionTeamAuth).filter(
            AuctionTeamAuth.auction_id == auction_id,
            AuctionTeamAuth.user_id == current_user.id
        ).first()
        
        if not auth:
            raise HTTPException(status_code=403, detail="Not authorized to create a team in this auction")
        
        # Check if already created a team
        if auth.team_id:
            raise HTTPException(status_code=400, detail="You have already created a team in this auction")
    
    # Check team code uniqueness within auction
    existing = db.query(Team).filter(
        Team.auction_id == auction_id,
        Team.team_code == team_data.team_code.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Team code already exists in this auction")
    
    # Create team
    team = Team(
        team_name=team_data.team_name,
        team_code=team_data.team_code.upper(),
        team_color=team_data.team_color,
        auction_id=auction_id,
        owner_id=current_user.id,
        initial_purse=auction.initial_purse,
        purse_remaining=auction.initial_purse
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    
    # Update authorization record if exists
    auth = db.query(AuctionTeamAuth).filter(
        AuctionTeamAuth.auction_id == auction_id,
        AuctionTeamAuth.user_id == current_user.id
    ).first()
    if auth:
        auth.team_id = team.id
        db.commit()
    
    return team


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    auction_id: int,
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get team details with player list."""
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.auction_id == auction_id
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get active players
    team_players = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.left_at_match == None
    ).all()
    
    response = TeamDetailResponse(
        id=team.id,
        team_name=team.team_name,
        team_code=team.team_code,
        team_color=team.team_color,
        owner_id=team.owner_id,
        initial_purse=team.initial_purse,
        purse_remaining=team.purse_remaining,
        created_at=team.created_at,
        players=[
            TeamPlayerResponse(
                id=tp.id,
                player_name=tp.display_name,
                is_captain=tp.is_captain,
                is_vice_captain=tp.is_vice_captain,
                bought_for=tp.bought_for
            )
            for tp in team_players
        ]
    )
    
    return response


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    auction_id: int,
    team_id: int,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update team details. Only team owner or admin can update."""
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.auction_id == auction_id
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Only owner or admin can update
    if not current_user.is_admin() and team.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this team")
    
    # Check team code uniqueness if changing
    if team_data.team_code and team_data.team_code.upper() != team.team_code:
        existing = db.query(Team).filter(
            Team.auction_id == auction_id,
            Team.team_code == team_data.team_code.upper(),
            Team.id != team_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Team code already exists")
    
    # Update fields
    for field, value in team_data.model_dump(exclude_unset=True).items():
        if field == "team_code" and value:
            value = value.upper()
        setattr(team, field, value)
    
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    auction_id: int,
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Delete a team. Only allowed in draft status and by admin/owner."""
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.auction_id == auction_id
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if auction.status != "draft":
        raise HTTPException(status_code=400, detail="Can only delete teams in draft status")
    
    if not current_user.is_admin() and team.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Remove authorization link
    auth = db.query(AuctionTeamAuth).filter(AuctionTeamAuth.team_id == team_id).first()
    if auth:
        auth.team_id = None
    
    db.delete(team)
    db.commit()
    return None


@router.post("/{team_id}/captain/{player_id}")
async def set_captain(
    auction_id: int,
    team_id: int,
    player_id: int,
    is_vice: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set a player as captain or vice-captain."""
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.auction_id == auction_id
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not current_user.is_admin() and team.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Find the team player record
    team_player = db.query(TeamPlayer).filter(
        TeamPlayer.id == player_id,
        TeamPlayer.team_id == team_id,
        TeamPlayer.left_at_match == None
    ).first()
    
    if not team_player:
        raise HTTPException(status_code=404, detail="Player not found in team")
    
    if is_vice:
        # Remove existing vice captain
        db.query(TeamPlayer).filter(
            TeamPlayer.team_id == team_id,
            TeamPlayer.is_vice_captain == True
        ).update({"is_vice_captain": False})
        team_player.is_vice_captain = True
        team_player.is_captain = False
    else:
        # Remove existing captain
        db.query(TeamPlayer).filter(
            TeamPlayer.team_id == team_id,
            TeamPlayer.is_captain == True
        ).update({"is_captain": False})
        team_player.is_captain = True
        team_player.is_vice_captain = False
    
    db.commit()
    
    return {
        "message": f"Player set as {'vice-captain' if is_vice else 'captain'}",
        "player_id": player_id
    }
