"""
WebSocket handler for real-time auction bidding.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Set, Optional
import json
import asyncio

from models.base import SessionLocal
from models.user import User
from models.auction import AuctionEvent, AuctionTeamAuth
from models.team import Team
from auth.jwt import verify_token
from auction.manager import AuctionManager
from auction.schemas import (
    WSMessage, BidNewMessage, PlayerSoldMessage, 
    StateUpdateMessage, ErrorMessage, ConnectedMessage
)

router = APIRouter(tags=["Auction WebSocket"])


class ConnectionManager:
    """Manages WebSocket connections for all auctions."""
    
    def __init__(self):
        # auction_id -> set of (websocket, user_id, role, team_id)
        self.connections: Dict[int, Set[tuple]] = {}
        # auction_id -> AuctionManager
        self.managers: Dict[int, AuctionManager] = {}
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def connect(
        self, 
        auction_id: int, 
        websocket: WebSocket, 
        user_id: int,
        role: str,
        team_id: Optional[int]
    ):
        """Add a new connection to an auction."""
        # Note: websocket.accept() is called in the handler before this
        
        async with self._lock:
            if auction_id not in self.connections:
                self.connections[auction_id] = set()
            
            self.connections[auction_id].add((websocket, user_id, role, team_id))
        
        # Send connected message
        connected_msg = ConnectedMessage(
            auction_id=auction_id,
            user_id=user_id,
            role=role,
            team_id=team_id
        )
        await websocket.send_json(connected_msg.model_dump())
        
        # Send current state
        await self.send_state(auction_id, websocket)
    
    async def disconnect(self, auction_id: int, websocket: WebSocket):
        """Remove a connection from an auction."""
        async with self._lock:
            if auction_id in self.connections:
                # Find and remove the connection
                to_remove = None
                for conn in self.connections[auction_id]:
                    if conn[0] == websocket:
                        to_remove = conn
                        break
                
                if to_remove:
                    self.connections[auction_id].discard(to_remove)
                
                # Clean up empty sets
                if not self.connections[auction_id]:
                    del self.connections[auction_id]
                    if auction_id in self.managers:
                        del self.managers[auction_id]
    
    def get_manager(self, auction_id: int, db: Session) -> AuctionManager:
        """Get or create an AuctionManager for an auction."""
        if auction_id not in self.managers:
            self.managers[auction_id] = AuctionManager(auction_id, db)
        return self.managers[auction_id]
    
    async def broadcast(self, auction_id: int, message: dict):
        """Broadcast a message to all connections in an auction."""
        if auction_id not in self.connections:
            return
        
        disconnected = []
        for conn in self.connections[auction_id]:
            websocket = conn[0]
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(conn)
        
        # Clean up disconnected
        for conn in disconnected:
            self.connections[auction_id].discard(conn)
    
    async def send_state(self, auction_id: int, websocket: WebSocket):
        """Send current auction state to a specific connection."""
        db = SessionLocal()
        try:
            manager = self.get_manager(auction_id, db)
            state = manager.get_state()
            msg = StateUpdateMessage(data=state)
            await websocket.send_json(msg.model_dump())
        finally:
            db.close()
    
    async def broadcast_state(self, auction_id: int):
        """Broadcast current state to all connections."""
        db = SessionLocal()
        try:
            manager = self.get_manager(auction_id, db)
            state = manager.get_state()
            msg = StateUpdateMessage(data=state)
            await self.broadcast(auction_id, msg.model_dump())
        finally:
            db.close()


# Global connection manager
manager = ConnectionManager()


def get_user_role(user: User, auction: AuctionEvent, team: Optional[Team]) -> str:
    """Determine user's role in an auction."""
    if user.is_admin() or auction.owner_id == user.id:
        return "admin"
    elif team and team.owner_id == user.id:
        return "team_owner"
    else:
        return "spectator"


@router.websocket("/auctions/{auction_id}/ws")
async def auction_websocket(
    websocket: WebSocket,
    auction_id: int,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time auction participation.
    
    Connect with: ws://host/auctions/{id}/ws?token={jwt_token}
    """
    # Must accept connection first to be able to send proper close codes
    await websocket.accept()
    
    db = SessionLocal()
    
    try:
        # Authenticate
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        payload = verify_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            await websocket.close(code=4001, reason="User not found or inactive")
            return
        
        # Verify auction exists
        auction = db.query(AuctionEvent).filter(AuctionEvent.id == auction_id).first()
        if not auction:
            await websocket.close(code=4004, reason="Auction not found")
            return
        
        # Check access
        is_authorized = (
            user.is_admin() or 
            auction.owner_id == user.id or
            db.query(AuctionTeamAuth).filter(
                AuctionTeamAuth.auction_id == auction_id,
                AuctionTeamAuth.user_id == user_id
            ).first() is not None
        )
        
        if not is_authorized:
            await websocket.close(code=4003, reason="Not authorized for this auction")
            return
        
        # Get user's team if any
        team = db.query(Team).filter(
            Team.auction_id == auction_id,
            Team.owner_id == user_id
        ).first()
        
        role = get_user_role(user, auction, team)
        team_id = team.id if team else None
        
        # Connect
        await manager.connect(auction_id, websocket, user_id, role, team_id)
        
        # Handle messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_message(auction_id, websocket, data, user, role, team_id, db)
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error = ErrorMessage(message="Invalid JSON")
                await websocket.send_json(error.model_dump())
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(auction_id, websocket)
        db.close()


async def handle_message(
    auction_id: int,
    websocket: WebSocket,
    data: dict,
    user: User,
    role: str,
    team_id: Optional[int],
    db: Session
):
    """Handle incoming WebSocket messages."""
    msg_type = data.get("type")
    
    if not msg_type:
        error = ErrorMessage(message="Missing message type")
        await websocket.send_json(error.model_dump())
        return
    
    auction_manager = manager.get_manager(auction_id, db)
    
    # Admin-only actions
    admin_actions = ["auction:start", "auction:pause", "auction:resume", 
                     "player:present", "player:sell", "player:unsold"]
    
    if msg_type in admin_actions:
        if role != "admin":
            error = ErrorMessage(message="Admin access required", code="forbidden")
            await websocket.send_json(error.model_dump())
            return
        
        try:
            if msg_type == "player:present":
                player_id = data.get("auction_player_id")
                if not player_id:
                    raise ValueError("auction_player_id required")
                auction_manager.present_player(player_id)
            
            elif msg_type == "player:sell":
                result = auction_manager.sell_player()
                sold_msg = PlayerSoldMessage(
                    player_id=result["player_id"],
                    player_name=result["player_name"],
                    team_id=result["team_id"],
                    team_name=result["team_name"],
                    sold_for=result["sold_for"]
                )
                await manager.broadcast(auction_id, sold_msg.model_dump())
            
            elif msg_type == "player:unsold":
                auction_manager.unsold_player()
            
            # Broadcast updated state
            await manager.broadcast_state(auction_id)
        
        except ValueError as e:
            error = ErrorMessage(message=str(e))
            await websocket.send_json(error.model_dump())
    
    # Team actions
    elif msg_type == "bid:place":
        if role not in ("admin", "team_owner"):
            error = ErrorMessage(message="Must own a team to bid", code="forbidden")
            await websocket.send_json(error.model_dump())
            return
        
        bid_team_id = data.get("team_id") or team_id
        amount = data.get("amount")
        
        if not bid_team_id or not amount:
            error = ErrorMessage(message="team_id and amount required")
            await websocket.send_json(error.model_dump())
            return
        
        # Admin can bid for any team, team_owner only for their own
        if role == "team_owner" and bid_team_id != team_id:
            error = ErrorMessage(message="Can only bid for your own team", code="forbidden")
            await websocket.send_json(error.model_dump())
            return
        
        try:
            result = auction_manager.place_bid(bid_team_id, float(amount))
            
            # Broadcast the new bid
            bid_msg = BidNewMessage(
                player_id=result["player_id"],
                player_name=result["player_name"],
                team_id=result["team_id"],
                team_name=result["team_name"],
                amount=result["amount"],
                next_minimum=result["next_minimum"]
            )
            await manager.broadcast(auction_id, bid_msg.model_dump())
            await manager.broadcast_state(auction_id)
        
        except ValueError as e:
            error = ErrorMessage(message=str(e))
            await websocket.send_json(error.model_dump())
    
    # State request
    elif msg_type == "state:request":
        await manager.send_state(auction_id, websocket)
    
    else:
        error = ErrorMessage(message=f"Unknown message type: {msg_type}")
        await websocket.send_json(error.model_dump())
