"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def fantasy_calculator():
    """Create a fresh FantasyPointsCalculator for each test."""
    from calculate_points import FantasyPointsCalculator
    return FantasyPointsCalculator()


@pytest.fixture
def sample_batsman():
    """Sample batsman data for testing."""
    return {
        'player_name': 'Test Batsman',
        'team': 'Test Team',
        'runs': 50,
        'balls_faced': 30,
        'fours': 4,
        'sixes': 2,
        'dismissal_type': '',
        'dismissal_bowler': '',
    }


@pytest.fixture
def sample_bowler():
    """Sample bowler data for testing."""
    return {
        'player_name': 'Test Bowler',
        'team': 'Test Team',
        'overs_bowled': 4,
        'wickets': 3,
        'runs_conceded': 25,
        'maidens': 1,
        'wides': 1,
        'no_balls': 0,
        'economy': 6.25,
    }


@pytest.fixture
def sample_dismissal_bowled():
    """Sample batsman dismissed by being bowled."""
    return {
        'player_name': 'Dismissed Batsman',
        'runs': 20,
        'balls_faced': 18,
        'dismissal_type': 'bowled',
        'dismissal_bowler': 'Strike Bowler',
    }


@pytest.fixture
def sample_dismissal_lbw():
    """Sample batsman dismissed LBW."""
    return {
        'player_name': 'LBW Batsman',
        'runs': 15,
        'balls_faced': 12,
        'dismissal_type': 'lbw',
        'dismissal_bowler': 'LBW Bowler',
    }


@pytest.fixture
def player_matcher():
    """Create a PlayerMatcher with mock data."""
    from services.player_matcher import PlayerMatcher
    
    matcher = PlayerMatcher()
    # Populate with test data
    matcher._player_cache = {
        'virat kohli': 1,
        'rohit sharma': 2,
        'mahendra singh dhoni': 3,
        'suryakumar yadav': 4,
        'jasprit bumrah': 5,
        'hardik pandya': 6,
    }
    return matcher


@pytest.fixture
def auction_state():
    """Sample auction state for testing."""
    return {
        'auction_id': 1,
        'status': 'live',
        'current_player_id': 1,
        'current_bid': 5.0,
        'current_bid_team_id': 1,
        'teams': [
            {'id': 1, 'name': 'Team A', 'purse': 95.0},
            {'id': 2, 'name': 'Team B', 'purse': 100.0},
        ]
    }
