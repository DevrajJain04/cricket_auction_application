"""
Team models for auction team management.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Team(Base):
    """
    A team participating in an auction.
    
    Note: Renamed from Shroff_teams for cleaner naming.
    Teams are scoped to a specific auction event.
    """
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    
    # Team identity
    team_name = Column(String, nullable=False)
    team_code = Column(String, index=True)  # Short code like "RCB"
    team_logo = Column(String, nullable=True)
    team_color = Column(String, nullable=True)
    
    # Auction context
    auction_id = Column(Integer, ForeignKey("auction_events.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Finances
    initial_purse = Column(Float, default=100.0)
    purse_remaining = Column(Float, default=100.0)
    
    # Relationships
    players = relationship("TeamPlayer", back_populates="team")
    owner = relationship("User")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def active_players(self):
        """Get currently active players (not released)."""
        return [tp for tp in self.players if tp.left_at_match is None]


class TeamPlayer(Base):
    """
    Association between teams and players.
    Tracks player tenure with a team (when joined/left).
    """
    __tablename__ = "team_players"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)  # Nullable for community mode
    
    # For community mode - custom player info
    custom_player_name = Column(String, nullable=True)
    
    # Player role in team
    is_captain = Column(Boolean, default=False)
    is_vice_captain = Column(Boolean, default=False)
    
    # Acquisition details
    bought_for = Column(Float, default=0.0)
    joined_at_match = Column(Integer, default=0)  # 0 = initial auction
    left_at_match = Column(Integer, nullable=True)  # NULL = still active
    
    # Relationships
    team = relationship("Team", back_populates="players")
    player = relationship("Player")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def display_name(self) -> str:
        """Get player name (handles both IPL and community modes)."""
        if self.player:
            return self.player.player_name
        return self.custom_player_name or "Unknown Player"


class PlayerTransfer(Base):
    """Record of player transfers between teams."""
    __tablename__ = "player_transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auction_events.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    custom_player_name = Column(String, nullable=True)
    
    from_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # NULL = from pool
    to_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # NULL = released
    
    transfer_amount = Column(Float, default=0.0)
    transfer_type = Column(String)  # "auction", "trade", "buy", "release"
    transfer_at_match = Column(Integer, default=0)
    reason = Column(String, nullable=True)
    
    # Relationships
    player = relationship("Player")
    from_team = relationship("Team", foreign_keys=[from_team_id])
    to_team = relationship("Team", foreign_keys=[to_team_id])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
