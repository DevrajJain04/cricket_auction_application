"""
Unit tests for the fantasy points calculator.
Tests the bug fixes and core point calculation logic.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBattingPoints:
    """Tests for batting points calculation."""
    
    def test_basic_run_scoring(self, fantasy_calculator):
        """Test basic runs scoring."""
        player = {
            'player_name': 'Test',
            'runs': 30,
            'balls_faced': 25,
            'fours': 2,
            'sixes': 1,
        }
        points = fantasy_calculator.calculate_batting_points(player)
        
        # Should include run points + boundary bonuses
        assert points > 0
        assert points >= 30  # At least 1 pt per run
    
    def test_half_century_bonus(self, fantasy_calculator):
        """Test 50-run bonus."""
        player_49 = {'player_name': 'Test', 'runs': 49, 'balls_faced': 35}
        player_50 = {'player_name': 'Test', 'runs': 50, 'balls_faced': 35}
        
        points_49 = fantasy_calculator.calculate_batting_points(player_49)
        points_50 = fantasy_calculator.calculate_batting_points(player_50)
        
        # 50 should get a bonus beyond just 1 extra run
        assert points_50 - points_49 >= 4  # At least 4 pt difference
    
    def test_century_bonus(self, fantasy_calculator):
        """Test 100-run bonus."""
        player_99 = {'player_name': 'Test', 'runs': 99, 'balls_faced': 60}
        player_100 = {'player_name': 'Test', 'runs': 100, 'balls_faced': 60}
        
        points_99 = fantasy_calculator.calculate_batting_points(player_99)
        points_100 = fantasy_calculator.calculate_batting_points(player_100)
        
        # 100 should get a bonus beyond just 1 extra run
        assert points_100 - points_99 >= 8  # At least 8 pt difference


class TestBowlerBonusFixes:
    """
    Tests for the critical bug fixes in dismissal bonuses.
    
    BUG FIX #1: Line 63 - Changed AND to OR for bowled/lbw check
    BUG FIX #2: get_bowlers_fielders_bonus - Fixed undefined variable
    """
    
    def test_bowled_dismissal_gives_bonus(self, fantasy_calculator, sample_dismissal_bowled):
        """
        Test that bowled dismissals give bonus to bowler.
        This tests the AND -> OR fix on line 63.
        """
        fantasy_calculator.calculate_batting_points(sample_dismissal_bowled)
        
        bowler = {'player_name': 'Strike Bowler'}
        bonus = fantasy_calculator.get_bowlers_fielders_bonus(bowler)
        
        assert bonus > 0, "Bowled dismissal should award bonus points"
        assert bonus == 8, "LBW/Bowled bonus should be 8 points"
    
    def test_lbw_dismissal_gives_bonus(self, fantasy_calculator, sample_dismissal_lbw):
        """
        Test that LBW dismissals give bonus to bowler.
        This tests the AND -> OR fix on line 63.
        """
        fantasy_calculator.calculate_batting_points(sample_dismissal_lbw)
        
        bowler = {'player_name': 'LBW Bowler'}
        bonus = fantasy_calculator.get_bowlers_fielders_bonus(bowler)
        
        assert bonus > 0, "LBW dismissal should award bonus points"
        assert bonus == 8, "LBW/Bowled bonus should be 8 points"
    
    def test_no_bonus_for_non_bowler(self, fantasy_calculator, sample_dismissal_bowled):
        """
        Test that non-bowlers get 0 bonus, not an error.
        This tests the undefined variable fix.
        """
        fantasy_calculator.calculate_batting_points(sample_dismissal_bowled)
        
        # Player who didn't take the wicket
        other_player = {'player_name': 'Other Player'}
        bonus = fantasy_calculator.get_bowlers_fielders_bonus(other_player)
        
        # Should return 0, not crash with undefined variable
        assert bonus == 0
    
    def test_stumped_dismissal_bonus(self, fantasy_calculator):
        """Test stumped dismissal gives bonus."""
        player = {
            'player_name': 'Stumped Batsman',
            'runs': 10,
            'balls_faced': 8,
            'dismissal_type': 'stumped',
            'dismissal_bowler': 'Keeper',
        }
        fantasy_calculator.calculate_batting_points(player)
        
        keeper = {'player_name': 'Keeper'}
        bonus = fantasy_calculator.get_bowlers_fielders_bonus(keeper)
        
        assert bonus > 0


class TestBowlingPoints:
    """Tests for bowling points calculation."""
    
    def test_wicket_points(self, fantasy_calculator, sample_bowler):
        """Test wickets earn points."""
        points = fantasy_calculator.calculate_bowling_points(sample_bowler)
        assert points > 0
    
    def test_maiden_bonus(self, fantasy_calculator):
        """Test maiden overs give bonus."""
        bowler_no_maiden = {
            'player_name': 'Test',
            'overs_bowled': 4,
            'wickets': 0,
            'runs_conceded': 30,
            'maidens': 0,
        }
        bowler_with_maiden = {
            'player_name': 'Test', 
            'overs_bowled': 4,
            'wickets': 0,
            'runs_conceded': 24,
            'maidens': 1,
        }
        
        points_no = fantasy_calculator.calculate_bowling_points(bowler_no_maiden)
        points_yes = fantasy_calculator.calculate_bowling_points(bowler_with_maiden)
        
        # Maiden should give bonus
        assert points_yes > points_no


class TestFieldingPoints:
    """Tests for fielding points calculation."""
    
    def test_catch_points(self, fantasy_calculator):
        """Test catches earn points."""
        fielder = {
            'player_name': 'Test',
            'catches': 2,
            'stumpings': 0,
            'run_outs': 0,
        }
        points = fantasy_calculator.calculate_fielding_points(fielder)
        assert points > 0
    
    def test_run_out_points(self, fantasy_calculator):
        """Test run outs earn points."""
        fielder = {
            'player_name': 'Test',
            'catches': 0,
            'stumpings': 0,
            'run_outs': 1,
        }
        points = fantasy_calculator.calculate_fielding_points(fielder)
        assert points > 0
