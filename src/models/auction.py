"""
Auction models for managing live auction events.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class AuctionEvent(Base):
    """
    A live auction event.
    
    Types:
    - ipl_tracker: Linked to real IPL players and matches
    - community: Custom players for local cricket groups
    """
    __tablename__ = "auction_events"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    auction_type = Column(String, default="community")  # "ipl_tracker" or "community"
    
    # Status: draft, live, paused, completed
    status = Column(String, default="draft")
    
    # Owner (admin/auction_manager who created it)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Auction settings
    initial_purse = Column(Float, default=100.0)
    min_bid_increment = Column(Float, default=0.5)
    base_price_default = Column(Float, default=1.0)
    max_team_size = Column(Integer, default=25)
    
    # Custom bid increment tiers (JSON string)
    # Format: [{"min": 0, "max": 1, "increment": 0.05}, ...]
    bid_increment_tiers = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # Current auction state (for live auctions)
    current_player_id = Column(Integer, nullable=True)  # Player being auctioned
    current_bid = Column(Float, nullable=True)
    current_bid_team_id = Column(Integer, nullable=True)
    
    # Relationships
    owner = relationship("User")
    teams = relationship("Team", backref="auction")
    players = relationship("AuctionPlayer", back_populates="auction")
    bids = relationship("AuctionBid", back_populates="auction")
    authorized_users = relationship("AuctionTeamAuth", back_populates="auction")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_live(self) -> bool:
        return self.status == "live"
    
    def can_bid(self) -> bool:
        return self.status in ("live",)


class AuctionPlayer(Base):
    """
    A player available in a specific auction's player pool.
    
    For IPL tracker: Links to Player.id
    For community: Uses custom_name
    """
    __tablename__ = "auction_players"
    
    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auction_events.id"), nullable=False)
    
    # Either link to IPL player OR custom name
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    custom_name = Column(String, nullable=True)
    
    # Auction details
    base_price = Column(Float, default=1.0)
    sold_for = Column(Float, nullable=True)
    sold_to_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    
    # Status: available, current, sold, unsold
    status = Column(String, default="available")
    
    # Order in auction pool
    pool_order = Column(Integer, default=0)
    
    # Relationships
    auction = relationship("AuctionEvent", back_populates="players")
    player = relationship("Player")
    sold_to_team = relationship("Team")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def display_name(self) -> str:
        if self.player:
            return self.player.player_name
        return self.custom_name or "Unknown Player"


class AuctionBid(Base):
    """Individual bid during an auction."""
    __tablename__ = "auction_bids"
    
    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auction_events.id"), nullable=False)
    auction_player_id = Column(Integer, ForeignKey("auction_players.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    bid_amount = Column(Float, nullable=False)
    is_winning_bid = Column(Boolean, default=False)
    
    # Relationships
    auction = relationship("AuctionEvent", back_populates="bids")
    auction_player = relationship("AuctionPlayer")
    team = relationship("Team")
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


class AuctionTeamAuth(Base):
    """
    Authorization for a user to create/manage a team in an auction.
    Admin grants this, then user can create their team.
    """
    __tablename__ = "auction_team_auths"
    
    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auction_events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Has the user created their team yet?
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    
    # Relationships
    auction = relationship("AuctionEvent", back_populates="authorized_users")
    user = relationship("User")
    team = relationship("Team")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
