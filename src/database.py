from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./cricdata.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, index=True)
    team = Column(String)
    
    # Career statistics
    matches_played = Column(Integer, default=0)
    total_runs = Column(Integer, default=0)
    total_balls_faced = Column(Integer, default=0)
    total_fours = Column(Integer, default=0)
    total_sixes = Column(Integer, default=0)
    total_wickets = Column(Integer, default=0)
    total_overs_bowled = Column(Float, default=0)
    total_maidens = Column(Integer, default=0)
    total_runs_conceded = Column(Integer, default=0)
    total_catches = Column(Integer, default=0)
    total_stumpings = Column(Integer, default=0)
    total_run_outs = Column(Integer, default=0)
    
    # Career fantasy points
    total_fantasy_points = Column(Float, default=0)
    
    # Relationships
    match_stats = relationship("MatchStats", back_populates="player")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, unique=True, index=True)
    match_name = Column(String)
    match_date = Column(DateTime)
    venue = Column(String)
    teams = Column(String)  # Store as JSON string
    
    # Relationships
    match_stats = relationship("MatchStats", back_populates="match")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MatchStats(Base):
    __tablename__ = "match_stats"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    match_id = Column(Integer, ForeignKey("matches.id"))
    
    # Match-specific statistics
    runs = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    strike_rate = Column(Float, default=0)
    dismissals = Column(Integer, default=0)
    dismissal_type = Column(String)
    dismissal_bowler = Column(String)
    
    overs_bowled = Column(Float, default=0)
    maidens = Column(Integer, default=0)
    runs_conceded = Column(Integer, default=0)
    wickets = Column(Integer, default=0)
    no_balls = Column(Integer, default=0)
    wides = Column(Integer, default=0)
    economy = Column(Float, default=0)
    
    catches = Column(Integer, default=0)
    stumpings = Column(Integer, default=0)
    run_outs = Column(Integer, default=0)
    
    # Match-specific fantasy points
    total_points = Column(Float, default=0)
    batting_points = Column(Float, default=0)
    bowling_points = Column(Float, default=0)
    fielding_points = Column(Float, default=0)
    
    # Relationships
    player = relationship("Player", back_populates="match_stats")
    match = relationship("Match", back_populates="match_stats")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create all tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 