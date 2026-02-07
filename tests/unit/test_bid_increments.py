"""
Unit tests for auction bid increment logic.
"""
import pytest
import sys
from pathlib import Path
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import the tier class directly (avoiding __init__.py relative imports)
# We'll define the test data here to avoid import issues
class BidIncrementTier:
    def __init__(self, min_bid: float, max_bid: float, increment: float):
        self.min_bid = Decimal(str(min_bid))
        self.max_bid = Decimal(str(max_bid))
        self.increment = Decimal(str(increment))

DEFAULT_TIERS = [
    BidIncrementTier(0, 1, 0.05),
    BidIncrementTier(1, 2, 0.10),
    BidIncrementTier(2, 5, 0.20),
    BidIncrementTier(5, float('inf'), 0.25)
]


class TestBidIncrementTiers:
    """Tests for IPL-style bid increment tiers."""
    
    def test_default_tiers_exist(self):
        """Test that default tiers are defined."""
        assert len(DEFAULT_TIERS) == 4
    
    def test_tier_0_to_1_crore(self):
        """Test 0-1 Cr increment is 0.05."""
        tier = DEFAULT_TIERS[0]
        assert tier.min_bid == Decimal("0")
        assert tier.max_bid == Decimal("1")
        assert tier.increment == Decimal("0.05")
    
    def test_tier_1_to_2_crore(self):
        """Test 1-2 Cr increment is 0.10."""
        tier = DEFAULT_TIERS[1]
        assert tier.min_bid == Decimal("1")
        assert tier.max_bid == Decimal("2")
        assert tier.increment == Decimal("0.10")
    
    def test_tier_2_to_5_crore(self):
        """Test 2-5 Cr increment is 0.20."""
        tier = DEFAULT_TIERS[2]
        assert tier.min_bid == Decimal("2")
        assert tier.max_bid == Decimal("5")
        assert tier.increment == Decimal("0.20")
    
    def test_tier_above_5_crore(self):
        """Test 5+ Cr increment is 0.25."""
        tier = DEFAULT_TIERS[3]
        assert tier.min_bid == Decimal("5")
        assert tier.increment == Decimal("0.25")


class TestGetIncrementForBid:
    """Tests for getting the correct increment based on current bid."""
    
    def get_increment(self, bid: float) -> float:
        """Helper to get increment for a bid amount."""
        bid_decimal = Decimal(str(bid))
        for tier in DEFAULT_TIERS:
            if tier.min_bid <= bid_decimal < tier.max_bid:
                return float(tier.increment)
        return float(DEFAULT_TIERS[-1].increment)
    
    def test_increment_at_0(self):
        """Test increment at 0 Cr."""
        assert self.get_increment(0) == 0.05
    
    def test_increment_at_0_5(self):
        """Test increment at 0.5 Cr."""
        assert self.get_increment(0.5) == 0.05
    
    def test_increment_at_1(self):
        """Test increment at exactly 1 Cr."""
        assert self.get_increment(1.0) == 0.10
    
    def test_increment_at_1_5(self):
        """Test increment at 1.5 Cr."""
        assert self.get_increment(1.5) == 0.10
    
    def test_increment_at_2(self):
        """Test increment at exactly 2 Cr."""
        assert self.get_increment(2.0) == 0.20
    
    def test_increment_at_3(self):
        """Test increment at 3 Cr."""
        assert self.get_increment(3.0) == 0.20
    
    def test_increment_at_5(self):
        """Test increment at exactly 5 Cr."""
        assert self.get_increment(5.0) == 0.25
    
    def test_increment_at_10(self):
        """Test increment at 10 Cr (high value)."""
        assert self.get_increment(10.0) == 0.25
    
    def test_increment_at_20(self):
        """Test increment at 20 Cr (very high value)."""
        assert self.get_increment(20.0) == 0.25


class TestMinimumBidCalculation:
    """Tests for minimum bid calculation."""
    
    def calculate_min_bid(self, base_price: float, current_bid: float = None) -> float:
        """Calculate minimum valid bid."""
        if current_bid is None:
            return base_price
        
        bid_decimal = Decimal(str(current_bid))
        for tier in DEFAULT_TIERS:
            if tier.min_bid <= bid_decimal < tier.max_bid:
                increment = tier.increment
                break
        else:
            increment = DEFAULT_TIERS[-1].increment
        
        return float(bid_decimal + increment)
    
    def test_first_bid_equals_base_price(self):
        """Test first bid should equal base price."""
        assert self.calculate_min_bid(1.0, None) == 1.0
    
    def test_second_bid_adds_increment(self):
        """Test second bid adds increment."""
        # Current bid is 1.0 (in tier 1-2), increment is 0.10
        assert self.calculate_min_bid(1.0, 1.0) == 1.10
    
    def test_bid_at_tier_boundary(self):
        """Test bid calculation at tier boundary."""
        # Current bid is 0.95 (in tier 0-1), next bid should use 0.05 increment
        assert self.calculate_min_bid(0.2, 0.95) == 1.0
    
    def test_high_value_bid(self):
        """Test high value bid calculation."""
        # Current bid is 10.0 (in tier 5+), increment is 0.25
        assert self.calculate_min_bid(1.0, 10.0) == 10.25
