"""
Auction router for managing auction events.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from models.base import get_db
from models.user import User
from models.auction import AuctionEvent, AuctionPlayer, AuctionTeamAuth
from models.team import Team
from auth.dependencies import get_current_active_user, require_admin, require_manager

router = APIRouter(prefix="/auctions", tags=["Auctions"])


# --- Pydantic Schemas ---

class AuctionCreate(BaseModel):
    """Schema for creating a new auction."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    auction_type: str = Field(default="community", pattern="^(ipl_tracker|community)$")
    initial_purse: float = Field(default=100.0, ge=0)
    min_bid_increment: float = Field(default=0.5, ge=0.01)
    base_price_default: float = Field(default=1.0, ge=0)
    max_team_size: int = Field(default=25, ge=1, le=50)


class AuctionUpdate(BaseModel):
    """Schema for updating auction settings."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    min_bid_increment: Optional[float] = Field(None, ge=0.01)
    base_price_default: Optional[float] = Field(None, ge=0)
    max_team_size: Optional[int] = Field(None, ge=1, le=50)


class AuctionResponse(BaseModel):
    """Auction response schema."""
    id: int
    name: str
    description: Optional[str]
    auction_type: str
    status: str
    owner_id: int
    initial_purse: float
    min_bid_increment: float
    base_price_default: float
    max_team_size: int
    created_at: datetime

    class Config:
        from_attributes = True


class AuctionListResponse(BaseModel):
    """Reduced auction info for list views."""
    id: int
    name: str
    auction_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthorizeUserRequest(BaseModel):
    """Request to authorize a user to create a team."""
    user_id: int


class PlayerPoolItem(BaseModel):
    """Schema for adding a player to the auction pool."""
    player_id: Optional[int] = None  # For IPL tracker mode
    custom_name: Optional[str] = None  # For community mode
    base_price: float = Field(default=1.0, ge=0)


# --- Endpoints ---

@router.get("/", response_model=List[AuctionListResponse])
async def list_auctions(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """
    List auctions the current user can access.
    Admins see all auctions, users see auctions they're authorized for.
    """
    if current_user.is_admin():
        auctions = db.query(AuctionEvent).order_by(AuctionEvent.created_at.desc()).all()
    else:
        # User sees auctions they own or are authorized for
        owned = db.query(AuctionEvent).filter(AuctionEvent.owner_id == current_user.id)
        authorized_auction_ids = db.query(AuctionTeamAuth.auction_id).filter(
            AuctionTeamAuth.user_id == current_user.id
        )
        authorized = db.query(AuctionEvent).filter(
            AuctionEvent.id.in_(authorized_auction_ids)
        )
        auctions = owned.union(authorized).order_by(AuctionEvent.created_at.desc()).all()
    
    return auctions


@router.post("/", response_model=AuctionResponse, status_code=status.HTTP_201_CREATED)
async def create_auction(
    auction_data: AuctionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new auction event.
    Any authenticated user can create an auction - they become the owner/manager of that auction.
    """
    auction = AuctionEvent(
        name=auction_data.name,
        description=auction_data.description,
        auction_type=auction_data.auction_type,
        owner_id=current_user.id,
        initial_purse=auction_data.initial_purse,
        min_bid_increment=auction_data.min_bid_increment,
        base_price_default=auction_data.base_price_default,
        max_team_size=auction_data.max_team_size
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)
    
    return auction


@router.get("/{auction_id}", response_model=AuctionResponse)
async def get_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get auction details by ID."""
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Check access - admin, owner, or authorized user
    if not current_user.is_admin():
        if auction.owner_id != current_user.id:
            auth = db.query(AuctionTeamAuth).filter(
                AuctionTeamAuth.auction_id == auction_id,
                AuctionTeamAuth.user_id == current_user.id
            ).first()
            if not auth:
                raise HTTPException(status_code=403, detail="Not authorized to view this auction")
    
    return auction


@router.patch("/{auction_id}", response_model=AuctionResponse)
async def update_auction(
    auction_id: int,
    auction_data: AuctionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Update auction settings. Only owner or admin can update."""
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Only owner or admin can update
    if not current_user.is_admin() and auction.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this auction")
    
    # Cannot update live auction settings
    if auction.status == "live":
        raise HTTPException(status_code=400, detail="Cannot update settings of a live auction")
    
    # Update fields
    for field, value in auction_data.model_dump(exclude_unset=True).items():
        setattr(auction, field, value)
    
    db.commit()
    db.refresh(auction)
    return auction


@router.post("/{auction_id}/authorize", status_code=status.HTTP_201_CREATED)
async def authorize_user(
    auction_id: int,
    auth_data: AuthorizeUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Authorize a user to create a team in this auction.
    Only auction owner or admin can authorize users.
    """
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if not current_user.is_admin() and auction.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this auction")
    
    # Check if user exists
    from models.user import User as UserModel
    target_user = db.query(UserModel).filter(UserModel.id == auth_data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already authorized
    existing = db.query(AuctionTeamAuth).filter(
        AuctionTeamAuth.auction_id == auction_id,
        AuctionTeamAuth.user_id == auth_data.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already authorized for this auction")
    
    # Create authorization
    auth_record = AuctionTeamAuth(
        auction_id=auction_id,
        user_id=auth_data.user_id
    )
    db.add(auth_record)
    db.commit()
    
    return {
        "message": f"User {target_user.display_name} authorized for auction",
        "user_id": auth_data.user_id,
        "auction_id": auction_id
    }


@router.post("/{auction_id}/players", status_code=status.HTTP_201_CREATED)
async def add_player_to_pool(
    auction_id: int,
    player_data: PlayerPoolItem,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Add a player to the auction's player pool.
    For IPL mode: provide player_id
    For community mode: provide custom_name
    """
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if not current_user.is_admin() and auction.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this auction")
    
    # Validate player data based on auction type
    if auction.auction_type == "ipl_tracker":
        if not player_data.player_id:
            raise HTTPException(status_code=400, detail="player_id required for IPL tracker mode")
        # Verify player exists
        from models.player import Player
        player = db.query(Player).filter(Player.id == player_data.player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
    else:
        if not player_data.custom_name:
            raise HTTPException(status_code=400, detail="custom_name required for community mode")
    
    # Get next pool order
    max_order = db.query(AuctionPlayer).filter(
        AuctionPlayer.auction_id == auction_id
    ).count()
    
    auction_player = AuctionPlayer(
        auction_id=auction_id,
        player_id=player_data.player_id,
        custom_name=player_data.custom_name,
        base_price=player_data.base_price or auction.base_price_default,
        pool_order=max_order + 1
    )
    db.add(auction_player)
    db.commit()
    db.refresh(auction_player)
    
    return {
        "id": auction_player.id,
        "name": auction_player.display_name,
        "base_price": auction_player.base_price,
        "status": auction_player.status
    }


@router.get("/{auction_id}/players")
async def get_player_pool(
    auction_id: int,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the player pool for an auction."""
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    query = db.query(AuctionPlayer).filter(AuctionPlayer.auction_id == auction_id)
    
    if status_filter:
        query = query.filter(AuctionPlayer.status == status_filter)
    
    players = query.order_by(AuctionPlayer.pool_order).all()
    
    return [
        {
            "id": p.id,
            "name": p.display_name,
            "base_price": p.base_price,
            "sold_for": p.sold_for,
            "status": p.status,
            "sold_to_team_id": p.sold_to_team_id
        }
        for p in players
    ]


@router.post("/{auction_id}/start")
async def start_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Start a live auction session."""
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if not current_user.is_admin() and auction.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this auction")
    
    if auction.status != "draft":
        raise HTTPException(status_code=400, detail=f"Auction is already {auction.status}")
    
    # Verify there are teams and players
    teams_count = db.query(Team).filter(Team.auction_id == auction_id).count()
    players_count = db.query(AuctionPlayer).filter(AuctionPlayer.auction_id == auction_id).count()
    
    if teams_count < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 teams to start auction")
    
    if players_count == 0:
        raise HTTPException(status_code=400, detail="Need at least 1 player in the pool")
    
    auction.status = "live"
    auction.started_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Auction started", "status": "live"}


@router.post("/{auction_id}/pause")
async def pause_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Pause a live auction."""
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if not current_user.is_admin() and auction.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if auction.status != "live":
        raise HTTPException(status_code=400, detail="Auction is not live")
    
    auction.status = "paused"
    db.commit()
    
    return {"message": "Auction paused", "status": "paused"}


@router.post("/{auction_id}/complete")
async def complete_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Mark auction as completed."""
    auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if not current_user.is_admin() and auction.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    auction.status = "completed"
    auction.ended_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Auction completed", "status": "completed"}
