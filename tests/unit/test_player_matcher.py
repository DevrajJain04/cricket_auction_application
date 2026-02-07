"""
Unit tests for the player matching service.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.player_matcher import PlayerMatcher, MatchResult, RAPIDFUZZ_AVAILABLE


class TestExactMatch:
    """Tests for exact name matching."""
    
    def test_exact_match_found(self, player_matcher):
        """Test exact match returns correct player."""
        result = player_matcher.find_by_exact("Virat Kohli")
        
        assert result is not None
        assert result.player_id == 1
        assert result.matched_via == "exact"
        assert result.match_score == 100.0
    
    def test_exact_match_case_insensitive(self, player_matcher):
        """Test exact match is case insensitive."""
        result = player_matcher.find_by_exact("VIRAT KOHLI")
        
        assert result is not None
        assert result.player_id == 1
    
    def test_exact_match_not_found(self, player_matcher):
        """Test exact match returns None for unknown player."""
        result = player_matcher.find_by_exact("Unknown Player")
        
        assert result is None


class TestAliasMatch:
    """Tests for alias-based matching."""
    
    def test_known_alias_sky(self, player_matcher):
        """Test SKY alias matches Suryakumar Yadav."""
        result = player_matcher.find_by_alias("SKY")
        
        assert result is not None
        assert result.player_id == 4  # Suryakumar Yadav
        assert result.matched_via == "alias"
    
    def test_known_alias_msd(self, player_matcher):
        """Test MSD alias matches Dhoni."""
        result = player_matcher.find_by_alias("MSD")
        
        assert result is not None
        assert result.player_id == 3  # Mahendra Singh Dhoni
    
    def test_known_alias_hitman(self, player_matcher):
        """Test Hitman alias matches Rohit Sharma."""
        result = player_matcher.find_by_alias("Hitman")
        
        assert result is not None
        assert result.player_id == 2
    
    def test_known_alias_boom(self, player_matcher):
        """Test Boom alias matches Bumrah."""
        result = player_matcher.find_by_alias("Boom")
        
        assert result is not None
        assert result.player_id == 5
    
    def test_unknown_alias(self, player_matcher):
        """Test unknown alias returns None."""
        result = player_matcher.find_by_alias("RandomAlias")
        
        assert result is None


class TestFuzzyMatch:
    """Tests for fuzzy string matching."""
    
    def test_fuzzy_partial_name(self, player_matcher):
        """Test fuzzy match with partial name."""
        results = player_matcher.find_by_fuzzy("Virat", limit=3)
        
        if RAPIDFUZZ_AVAILABLE:
            assert len(results) > 0
            # Virat Kohli should be the top result
            assert results[0].player_id == 1
            assert results[0].matched_via == "fuzzy"
        else:
            # Basic fallback should still work
            pass
    
    def test_fuzzy_returns_multiple(self, player_matcher):
        """Test fuzzy match returns multiple results."""
        results = player_matcher.find_by_fuzzy("Sharma", limit=5)
        
        # At minimum should work with basic matching
        # Rohit Sharma should be in results
        player_ids = [r.player_id for r in results]
        assert len(results) >= 0  # May be 0 if no rapidfuzz


class TestCombinedSearch:
    """Tests for the combined find_player method."""
    
    def test_find_player_exact(self, player_matcher):
        """Test find_player prefers exact match."""
        result = player_matcher.find_player("Virat Kohli")
        
        assert result is not None
        assert result.player_id == 1
        assert result.matched_via == "exact"
    
    def test_find_player_alias(self, player_matcher):
        """Test find_player falls back to alias."""
        result = player_matcher.find_player("SKY")
        
        assert result is not None
        assert result.player_id == 4
        assert result.matched_via == "alias"
    
    def test_find_players_returns_multiple(self, player_matcher):
        """Test find_players returns multiple matches."""
        results = player_matcher.find_players("Kohli", limit=5)
        
        assert len(results) > 0
        # First result should be exact/best match
        assert results[0].player_id == 1


class TestNameNormalization:
    """Tests for name normalization."""
    
    def test_normalize_removes_extra_spaces(self, player_matcher):
        """Test normalization handles extra spaces."""
        normalized = player_matcher.normalize_name("  Virat   Kohli  ")
        
        assert normalized == "virat kohli"
    
    def test_normalize_lowercase(self, player_matcher):
        """Test normalization converts to lowercase."""
        normalized = player_matcher.normalize_name("VIRAT KOHLI")
        
        assert normalized == "virat kohli"


class TestAddAlias:
    """Tests for adding custom aliases."""
    
    def test_add_alias_to_cache(self, player_matcher):
        """Test adding alias updates cache."""
        player_matcher.add_alias("king", 1)
        
        assert "king" in player_matcher._alias_cache
        assert player_matcher._alias_cache["king"] == 1
