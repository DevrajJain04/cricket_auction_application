"""
Pydantic schemas for WebSocket auction messages.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# --- Message Types ---
MessageType = Literal[
    # Admin actions
    "auction:start",
    "auction:pause",
    "auction:resume",
    "player:present",
    "player:sell",
    "player:unsold",
    
    # Team actions
    "bid:place",
    
    # Broadcasts
    "state:update",
    "bid:new",
    "player:sold",
    "error",
    "connected"
]


# --- Base Message ---
class WSMessage(BaseModel):
    """Base WebSocket message."""
    type: str
    data: Optional[dict] = None


# --- Client to Server Messages ---

class BidPlaceMessage(BaseModel):
    """Message from client to place a bid."""
    type: Literal["bid:place"] = "bid:place"
    team_id: int
    amount: float


class PlayerPresentMessage(BaseModel):
    """Admin message to present a player for bidding."""
    type: Literal["player:present"] = "player:present"
    auction_player_id: int


class PlayerSellMessage(BaseModel):
    """Admin message to confirm player sale."""
    type: Literal["player:sell"] = "player:sell"
    auction_player_id: int


class PlayerUnsoldMessage(BaseModel):
    """Admin message to mark player as unsold."""
    type: Literal["player:unsold"] = "player:unsold"
    auction_player_id: int


# --- Server to Client Messages ---

class TeamState(BaseModel):
    """Team state in auction."""
    id: int
    name: str
    code: str
    purse: float
    players_count: int


class PlayerState(BaseModel):
    """Current player being auctioned."""
    id: int
    name: str
    base_price: float
    current_bid: Optional[float] = None
    current_bidder_id: Optional[int] = None
    current_bidder_name: Optional[str] = None


class AuctionState(BaseModel):
    """Full auction state broadcast."""
    auction_id: int
    status: str  # draft, live, paused, completed
    current_player: Optional[PlayerState] = None
    teams: List[TeamState] = []
    available_players: int = 0
    sold_players: int = 0
    unsold_players: int = 0


class StateUpdateMessage(BaseModel):
    """Full state update broadcast."""
    type: Literal["state:update"] = "state:update"
    data: AuctionState


class BidNewMessage(BaseModel):
    """New bid broadcast."""
    type: Literal["bid:new"] = "bid:new"
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    amount: float
    next_minimum: float


class PlayerSoldMessage(BaseModel):
    """Player sold broadcast."""
    type: Literal["player:sold"] = "player:sold"
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    sold_for: float


class ErrorMessage(BaseModel):
    """Error message."""
    type: Literal["error"] = "error"
    message: str
    code: Optional[str] = None


class ConnectedMessage(BaseModel):
    """Connection established message."""
    type: Literal["connected"] = "connected"
    auction_id: int
    user_id: int
    role: str  # admin, team_owner, spectator
    team_id: Optional[int] = None
