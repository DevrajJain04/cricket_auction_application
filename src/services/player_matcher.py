"""
Player matching service with fuzzy search and alias support.
Handles the challenge of matching player names from different data sources.
"""
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from collections import defaultdict

# Try to import rapidfuzz, fall back to basic matching if not available
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


@dataclass
class MatchResult:
    """Result of a player name match."""
    player_id: int
    player_name: str
    match_score: float
    matched_via: str  # "exact", "alias", "fuzzy"


class PlayerMatcher:
    """
    Matches player names using multiple strategies:
    1. Exact match
    2. Alias lookup
    3. Fuzzy string matching
    
    Example usage:
        matcher = PlayerMatcher(session)
        result = matcher.find_player("Virat")  # Matches "Virat Kohli"
        result = matcher.find_player("SKY")    # Matches via alias for "Suryakumar Yadav"
    """
    
    # Common name variations and their patterns
    NAME_NORMALIZATIONS = {
        # Remove titles
        r'\b(mr|ms|mrs|dr)\b\.?\s*': '',
        # Normalize spaces
        r'\s+': ' ',
        # Remove dots
        r'\.': '',
    }
    
    # Common player aliases (can be expanded)
    KNOWN_ALIASES = {
        # IPL Stars
        "virat": "Virat Kohli",
        "vk": "Virat Kohli",
        "king kohli": "Virat Kohli",
        "rohit": "Rohit Sharma",
        "hitman": "Rohit Sharma",
        "msd": "Mahendra Singh Dhoni",
        "ms dhoni": "Mahendra Singh Dhoni",
        "dhoni": "Mahendra Singh Dhoni",
        "thala": "Mahendra Singh Dhoni",
        "sky": "Suryakumar Yadav",
        "surya": "Suryakumar Yadav",
        "bumrah": "Jasprit Bumrah",
        "boom": "Jasprit Bumrah",
        "jaddu": "Ravindra Jadeja",
        "jadeja": "Ravindra Jadeja",
        "pant": "Rishabh Pant",
        "gabbar": "Shikhar Dhawan",
        "ab": "AB de Villiers",
        "abd": "AB de Villiers",
        "mr 360": "AB de Villiers",
        "gayle": "Chris Gayle",
        "universe boss": "Chris Gayle",
        "raina": "Suresh Raina",
        "chinnaswamy express": "Suresh Raina",
        "hardik": "Hardik Pandya",
        "krunal": "Krunal Pandya",
        "ishan": "Ishan Kishan",
        "shubman": "Shubman Gill",
        "gill": "Shubman Gill",
        "chahal": "Yuzvendra Chahal",
        "kuldeep": "Kuldeep Yadav",
        "ashwin": "Ravichandran Ashwin",
        "ash": "Ravichandran Ashwin",
        "shami": "Mohammed Shami",
        "siraj": "Mohammed Siraj",
        "arshdeep": "Arshdeep Singh",
        "avesh": "Avesh Khan",
        "rahul": "KL Rahul",
        "kl": "KL Rahul",
        "warner": "David Warner",
        "buttler": "Jos Buttler",
        "samson": "Sanju Samson",
        "sanju": "Sanju Samson",
        "shreyas": "Shreyas Iyer",
        "iyer": "Shreyas Iyer",
        "venky": "Venkatesh Iyer",
        "pandya": "Hardik Pandya",
        "csk": "Chennai Super Kings",
        "mi": "Mumbai Indians",
        "rcb": "Royal Challengers Bangalore",
        "srh": "Sunrisers Hyderabad",
        "dc": "Delhi Capitals",
        "kkr": "Kolkata Knight Riders",
        "pbks": "Punjab Kings",
        "rr": "Rajasthan Royals",
        "gt": "Gujarat Titans",
        "lsg": "Lucknow Super Giants",
    }
    
    def __init__(self, db_session=None, min_fuzzy_score: int = 70):
        """
        Initialize the player matcher.
        
        Args:
            db_session: SQLAlchemy session for database lookups
            min_fuzzy_score: Minimum fuzzy match score (0-100) to consider a match
        """
        self.db = db_session
        self.min_fuzzy_score = min_fuzzy_score
        self._player_cache: Dict[str, int] = {}
        self._alias_cache: Dict[str, int] = {}
    
    def load_players_from_db(self):
        """Load all players and aliases from database into cache."""
        if not self.db:
            return
        
        from models.player import Player, PlayerAlias
        
        # Load players
        players = self.db.query(Player).all()
        for player in players:
            self._player_cache[player.player_name.lower()] = player.id
        
        # Load aliases from database
        aliases = self.db.query(PlayerAlias).all()
        for alias in aliases:
            self._alias_cache[alias.alias.lower()] = alias.player_id
    
    def normalize_name(self, name: str) -> str:
        """Normalize a player name for matching."""
        import re
        
        name = name.lower().strip()
        
        for pattern, replacement in self.NAME_NORMALIZATIONS.items():
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
        
        return name.strip()
    
    def find_by_exact(self, query: str) -> Optional[MatchResult]:
        """Try exact match in player cache."""
        normalized = self.normalize_name(query)
        
        if normalized in self._player_cache:
            player_id = self._player_cache[normalized]
            return MatchResult(
                player_id=player_id,
                player_name=normalized,
                match_score=100.0,
                matched_via="exact"
            )
        
        return None
    
    def find_by_alias(self, query: str) -> Optional[MatchResult]:
        """Try alias lookup."""
        normalized = self.normalize_name(query)
        
        # Check database aliases first
        if normalized in self._alias_cache:
            player_id = self._alias_cache[normalized]
            return MatchResult(
                player_id=player_id,
                player_name=normalized,
                match_score=100.0,
                matched_via="alias"
            )
        
        # Check built-in known aliases
        if normalized in self.KNOWN_ALIASES:
            canonical_name = self.KNOWN_ALIASES[normalized].lower()
            if canonical_name in self._player_cache:
                return MatchResult(
                    player_id=self._player_cache[canonical_name],
                    player_name=self.KNOWN_ALIASES[normalized],
                    match_score=95.0,
                    matched_via="alias"
                )
        
        return None
    
    def find_by_fuzzy(self, query: str, limit: int = 5) -> List[MatchResult]:
        """
        Find players using fuzzy string matching.
        
        Uses rapidfuzz if available, otherwise falls back to basic matching.
        """
        if not self._player_cache:
            return []
        
        normalized = self.normalize_name(query)
        results = []
        
        if RAPIDFUZZ_AVAILABLE:
            # Use rapidfuzz for high-quality matches
            matches = process.extract(
                normalized,
                list(self._player_cache.keys()),
                scorer=fuzz.WRatio,
                limit=limit
            )
            
            for match_name, score, _ in matches:
                if score >= self.min_fuzzy_score:
                    results.append(MatchResult(
                        player_id=self._player_cache[match_name],
                        player_name=match_name,
                        match_score=score,
                        matched_via="fuzzy"
                    ))
        else:
            # Basic fallback: substring matching
            for player_name, player_id in self._player_cache.items():
                if normalized in player_name or player_name in normalized:
                    score = 80.0 if normalized in player_name else 70.0
                    results.append(MatchResult(
                        player_id=player_id,
                        player_name=player_name,
                        match_score=score,
                        matched_via="fuzzy"
                    ))
                    if len(results) >= limit:
                        break
        
        return sorted(results, key=lambda x: x.match_score, reverse=True)
    
    def find_player(self, query: str) -> Optional[MatchResult]:
        """
        Find a player using all matching strategies.
        
        Order of precedence:
        1. Exact match
        2. Alias match
        3. Best fuzzy match (if score >= threshold)
        """
        # Try exact match first
        result = self.find_by_exact(query)
        if result:
            return result
        
        # Try alias
        result = self.find_by_alias(query)
        if result:
            return result
        
        # Try fuzzy
        fuzzy_results = self.find_by_fuzzy(query, limit=1)
        if fuzzy_results:
            return fuzzy_results[0]
        
        return None
    
    def find_players(self, query: str, limit: int = 10) -> List[MatchResult]:
        """
        Find multiple potential player matches.
        Returns all matching strategies combined and sorted by score.
        """
        results = []
        seen_ids = set()
        
        # Exact match
        exact = self.find_by_exact(query)
        if exact:
            results.append(exact)
            seen_ids.add(exact.player_id)
        
        # Alias match
        alias = self.find_by_alias(query)
        if alias and alias.player_id not in seen_ids:
            results.append(alias)
            seen_ids.add(alias.player_id)
        
        # Fuzzy matches
        for fuzzy in self.find_by_fuzzy(query, limit=limit):
            if fuzzy.player_id not in seen_ids:
                results.append(fuzzy)
                seen_ids.add(fuzzy.player_id)
        
        return sorted(results, key=lambda x: x.match_score, reverse=True)[:limit]
    
    def add_alias(self, alias: str, player_id: int):
        """Add an alias to the cache (and optionally to database)."""
        normalized = self.normalize_name(alias)
        self._alias_cache[normalized] = player_id
        
        if self.db:
            from models.player import PlayerAlias
            
            # Check if already exists
            existing = self.db.query(PlayerAlias).filter(
                PlayerAlias.alias == normalized
            ).first()
            
            if not existing:
                new_alias = PlayerAlias(player_id=player_id, alias=normalized)
                self.db.add(new_alias)
                self.db.commit()


def create_matcher(db_session=None) -> PlayerMatcher:
    """Factory function to create and initialize a PlayerMatcher."""
    matcher = PlayerMatcher(db_session)
    matcher.load_players_from_db()
    return matcher
