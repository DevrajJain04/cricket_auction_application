"""
Auction Manager - State machine for live auction management.
Handles bidding logic, player presentation, and state tracking.
"""
from typing import Dict, Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
import json

from models.auction import AuctionEvent, AuctionPlayer, AuctionBid
from models.team import Team, TeamPlayer, PlayerTransfer
from auction.schemas import AuctionState, TeamState, PlayerState


class BidIncrementTier:
    """Bid increment tier configuration."""
    def __init__(self, min_bid: float, max_bid: float, increment: float):
        self.min_bid = Decimal(str(min_bid))
        self.max_bid = Decimal(str(max_bid))
        self.increment = Decimal(str(increment))


# Default IPL-style bid increments
DEFAULT_TIERS = [
    BidIncrementTier(0, 1, 0.05),
    BidIncrementTier(1, 2, 0.10),
    BidIncrementTier(2, 5, 0.20),
    BidIncrementTier(5, float('inf'), 0.25)
]


class AuctionManager:
    """
    Manages the state and logic for a single live auction.
    
    Each auction has its own manager instance that tracks:
    - Current player being auctioned
    - Current bid and bidder
    - Team purses
    - Available player queue
    """
    
    def __init__(self, auction_id: int, db: Session):
        self.auction_id = auction_id
        self.db = db
        self.bid_tiers: List[BidIncrementTier] = DEFAULT_TIERS
        
        # Load auction from database
        self._load_auction()
    
    def _load_auction(self):
        """Load auction data from database."""
        self.auction = self.db.query(AuctionEvent).filter(
            AuctionEvent.id == self.auction_id
        ).first()
        
        if not self.auction:
            raise ValueError(f"Auction {self.auction_id} not found")
        
        # Parse custom bid tiers if defined
        if self.auction.bid_increment_tiers:
            try:
                tiers_data = json.loads(self.auction.bid_increment_tiers)
                self.bid_tiers = [
                    BidIncrementTier(t["min"], t["max"], t["increment"])
                    for t in tiers_data
                ]
            except (json.JSONDecodeError, KeyError):
                pass  # Use default tiers
    
    def refresh(self):
        """Refresh auction data from database."""
        self.db.refresh(self.auction)
    
    def get_increment_for_bid(self, current_bid: float) -> Decimal:
        """Get the minimum increment for a given bid amount."""
        bid = Decimal(str(current_bid))
        for tier in self.bid_tiers:
            if tier.min_bid <= bid < tier.max_bid:
                return tier.increment
        return self.bid_tiers[-1].increment  # Use last tier for very high bids
    
    def get_minimum_bid(self, base_price: float, current_bid: Optional[float]) -> float:
        """Calculate minimum valid bid amount."""
        if current_bid is None:
            return base_price
        
        increment = self.get_increment_for_bid(current_bid)
        return float(Decimal(str(current_bid)) + increment)
    
    def validate_bid(self, team_id: int, amount: float) -> tuple[bool, str]:
        """
        Validate a bid.
        
        Returns:
            (is_valid, error_message)
        """
        # Check auction is live
        if self.auction.status != "live":
            return False, "Auction is not live"
        
        # Check there's a current player
        if not self.auction.current_player_id:
            return False, "No player is currently being auctioned"
        
        # Get current player
        current_player = self.db.query(AuctionPlayer).filter(
            AuctionPlayer.id == self.auction.current_player_id
        ).first()
        
        if not current_player or current_player.status != "current":
            return False, "No active player auction"
        
        # Get team
        team = self.db.query(Team).filter(
            Team.id == team_id,
            Team.auction_id == self.auction_id
        ).first()
        
        if not team:
            return False, "Team not found in this auction"
        
        # Check purse
        if team.purse_remaining < amount:
            return False, f"Insufficient purse ({team.purse_remaining} < {amount})"
        
        # Check minimum bid
        min_bid = self.get_minimum_bid(
            current_player.base_price,
            self.auction.current_bid
        )
        
        if amount < min_bid:
            return False, f"Bid must be at least {min_bid}"
        
        # Check not already highest bidder
        if self.auction.current_bid_team_id == team_id:
            return False, "You are already the highest bidder"
        
        return True, ""
    
    def place_bid(self, team_id: int, amount: float) -> dict:
        """
        Place a bid for the current player.
        
        Uses database-level locking (SELECT FOR UPDATE) to prevent race conditions
        when multiple teams bid simultaneously.
        
        Returns bid result with next minimum bid.
        """
        # Lock the auction row to prevent race conditions
        # This ensures only one bid can be processed at a time
        locked_auction = self.db.query(AuctionEvent).filter(
            AuctionEvent.id == self.auction_id
        ).with_for_update().first()
        
        if not locked_auction:
            raise ValueError("Auction not found")
        
        # Re-validate with locked data (bid state may have changed)
        if locked_auction.status != "live":
            raise ValueError("Auction is not live")
        
        if not locked_auction.current_player_id:
            raise ValueError("No player is currently being auctioned")
        
        current_player = self.db.query(AuctionPlayer).filter(
            AuctionPlayer.id == locked_auction.current_player_id
        ).first()
        
        if not current_player or current_player.status != "current":
            raise ValueError("No active player auction")
        
        team = self.db.query(Team).filter(
            Team.id == team_id,
            Team.auction_id == self.auction_id
        ).first()
        
        if not team:
            raise ValueError("Team not found in this auction")
        
        # Check purse
        if team.purse_remaining < amount:
            raise ValueError(f"Insufficient purse ({team.purse_remaining} < {amount})")
        
        # Check minimum bid with current locked state
        min_bid = self.get_minimum_bid(
            current_player.base_price,
            locked_auction.current_bid
        )
        
        if amount < min_bid:
            raise ValueError(f"Bid must be at least {min_bid}")
        
        # Check not already highest bidder
        if locked_auction.current_bid_team_id == team_id:
            raise ValueError("You are already the highest bidder")
        
        # Record the bid
        bid = AuctionBid(
            auction_id=self.auction_id,
            auction_player_id=current_player.id,
            team_id=team_id,
            bid_amount=amount
        )
        self.db.add(bid)
        
        # Update auction state atomically
        locked_auction.current_bid = amount
        locked_auction.current_bid_team_id = team_id
        
        self.db.commit()
        self.db.refresh(self.auction)  # Refresh our cached auction
        
        return {
            "player_id": current_player.id,
            "player_name": current_player.display_name,
            "team_id": team_id,
            "team_name": team.team_name,
            "amount": amount,
            "next_minimum": self.get_minimum_bid(current_player.base_price, amount)
        }
    
    def present_player(self, auction_player_id: int) -> PlayerState:
        """Put a player up for bidding."""
        player = self.db.query(AuctionPlayer).filter(
            AuctionPlayer.id == auction_player_id,
            AuctionPlayer.auction_id == self.auction_id
        ).first()
        
        if not player:
            raise ValueError("Player not found in auction pool")
        
        if player.status != "available":
            raise ValueError(f"Player is {player.status}, not available")
        
        # Clear any previous current player
        self.db.query(AuctionPlayer).filter(
            AuctionPlayer.auction_id == self.auction_id,
            AuctionPlayer.status == "current"
        ).update({"status": "available"})
        
        # Set this player as current
        player.status = "current"
        self.auction.current_player_id = player.id
        self.auction.current_bid = None
        self.auction.current_bid_team_id = None
        
        self.db.commit()
        self.refresh()
        
        return PlayerState(
            id=player.id,
            name=player.display_name,
            base_price=player.base_price
        )
    
    def sell_player(self) -> dict:
        """Confirm sale of current player to highest bidder."""
        if not self.auction.current_player_id:
            raise ValueError("No player being auctioned")
        
        if not self.auction.current_bid_team_id:
            raise ValueError("No bids placed, cannot sell")
        
        player = self.db.query(AuctionPlayer).filter(
            AuctionPlayer.id == self.auction.current_player_id
        ).first()
        
        team = self.db.query(Team).filter(
            Team.id == self.auction.current_bid_team_id
        ).first()
        
        # Update player status
        player.status = "sold"
        player.sold_for = self.auction.current_bid
        player.sold_to_team_id = team.id
        
        # Update team purse
        team.purse_remaining -= self.auction.current_bid
        
        # Mark winning bid
        self.db.query(AuctionBid).filter(
            AuctionBid.auction_player_id == player.id,
            AuctionBid.team_id == team.id,
            AuctionBid.bid_amount == self.auction.current_bid
        ).update({"is_winning_bid": True})
        
        # Create team player record
        team_player = TeamPlayer(
            team_id=team.id,
            player_id=player.player_id,
            custom_player_name=player.custom_name if not player.player_id else None,
            bought_for=self.auction.current_bid,
            joined_at_match=0
        )
        self.db.add(team_player)
        
        # Create transfer record
        transfer = PlayerTransfer(
            auction_id=self.auction_id,
            player_id=player.player_id,
            custom_player_name=player.custom_name,
            to_team_id=team.id,
            transfer_amount=self.auction.current_bid,
            transfer_type="auction"
        )
        self.db.add(transfer)
        
        # Clear current player state
        result = {
            "player_id": player.id,
            "player_name": player.display_name,
            "team_id": team.id,
            "team_name": team.team_name,
            "sold_for": self.auction.current_bid
        }
        
        self.auction.current_player_id = None
        self.auction.current_bid = None
        self.auction.current_bid_team_id = None
        
        self.db.commit()
        self.refresh()
        
        return result
    
    def unsold_player(self) -> dict:
        """Mark current player as unsold."""
        if not self.auction.current_player_id:
            raise ValueError("No player being auctioned")
        
        player = self.db.query(AuctionPlayer).filter(
            AuctionPlayer.id == self.auction.current_player_id
        ).first()
        
        player.status = "unsold"
        
        result = {
            "player_id": player.id,
            "player_name": player.display_name
        }
        
        self.auction.current_player_id = None
        self.auction.current_bid = None
        self.auction.current_bid_team_id = None
        
        self.db.commit()
        self.refresh()
        
        return result
    
    def get_state(self) -> AuctionState:
        """Get full auction state for broadcast."""
        self.refresh()
        
        # Get teams
        teams = self.db.query(Team).filter(Team.auction_id == self.auction_id).all()
        team_states = []
        for team in teams:
            player_count = self.db.query(TeamPlayer).filter(
                TeamPlayer.team_id == team.id,
                TeamPlayer.left_at_match == None
            ).count()
            
            team_states.append(TeamState(
                id=team.id,
                name=team.team_name,
                code=team.team_code,
                purse=team.purse_remaining,
                players_count=player_count
            ))
        
        # Get current player if any
        current_player = None
        if self.auction.current_player_id:
            player = self.db.query(AuctionPlayer).filter(
                AuctionPlayer.id == self.auction.current_player_id
            ).first()
            
            if player:
                bidder_name = None
                if self.auction.current_bid_team_id:
                    bidder = self.db.query(Team).filter(
                        Team.id == self.auction.current_bid_team_id
                    ).first()
                    bidder_name = bidder.team_name if bidder else None
                
                current_player = PlayerState(
                    id=player.id,
                    name=player.display_name,
                    base_price=player.base_price,
                    current_bid=self.auction.current_bid,
                    current_bidder_id=self.auction.current_bid_team_id,
                    current_bidder_name=bidder_name
                )
        
        # Get player counts
        available = self.db.query(AuctionPlayer).filter(
            AuctionPlayer.auction_id == self.auction_id,
            AuctionPlayer.status == "available"
        ).count()
        
        sold = self.db.query(AuctionPlayer).filter(
            AuctionPlayer.auction_id == self.auction_id,
            AuctionPlayer.status == "sold"
        ).count()
        
        unsold = self.db.query(AuctionPlayer).filter(
            AuctionPlayer.auction_id == self.auction_id,
            AuctionPlayer.status == "unsold"
        ).count()
        
        return AuctionState(
            auction_id=self.auction_id,
            status=self.auction.status,
            current_player=current_player,
            teams=team_states,
            available_players=available,
            sold_players=sold,
            unsold_players=unsold
        )
