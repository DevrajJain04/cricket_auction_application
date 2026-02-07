/**
 * Players Search Page
 */
import { useState, useCallback } from 'react';
import playerService from '../services/playerService';

function PlayersPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    const searchPlayers = useCallback(async () => {
        if (searchQuery.length < 2) return;

        setLoading(true);
        try {
            const results = await playerService.searchPlayers(searchQuery);
            setPlayers(results);
            setSearched(true);
        } catch (err) {
            console.error('Search failed:', err);
        } finally {
            setLoading(false);
        }
    }, [searchQuery]);

    const handleSubmit = (e) => {
        e.preventDefault();
        searchPlayers();
    };

    const getInitials = (name) => {
        if (!name) return '?';
        return name
            .split(' ')
            .map((n) => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    };

    return (
        <div className="animate-fadeIn">
            <div className="page-header">
                <div>
                    <h1 className="page-header-title">Player Search</h1>
                    <p className="text-secondary mt-2">Find players by name with fuzzy matching</p>
                </div>
            </div>

            {/* Search Form */}
            <form onSubmit={handleSubmit} className="card p-6 mb-6">
                <div className="flex gap-4" style={{ flexWrap: 'wrap' }}>
                    <div className="form-group" style={{ marginBottom: 0, flex: '1 1 300px' }}>
                        <input
                            type="text"
                            className="form-input"
                            placeholder="Search for a player (e.g., Virat, SKY, Bumrah)..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            minLength={2}
                        />
                    </div>
                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={loading || searchQuery.length < 2}
                    >
                        {loading ? (
                            <>
                                <span className="spinner" style={{ width: 20, height: 20 }} />
                                Searching...
                            </>
                        ) : (
                            <>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="11" cy="11" r="8" />
                                    <path d="M21 21l-4.35-4.35" />
                                </svg>
                                Search
                            </>
                        )}
                    </button>
                </div>
            </form>

            {/* Results */}
            {loading ? (
                <div className="loader">
                    <div className="spinner" />
                </div>
            ) : searched && players.length === 0 ? (
                <div className="card">
                    <div className="empty-state">
                        <div className="empty-state-icon">🔍</div>
                        <h3 className="empty-state-title">No players found</h3>
                        <p className="empty-state-description">
                            Try a different search term
                        </p>
                    </div>
                </div>
            ) : players.length > 0 ? (
                <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 'var(--space-4)' }}>
                    {players.map((player) => (
                        <div key={player.id} className="card player-card card-elevated">
                            <div className="avatar avatar-lg" style={{ background: 'var(--primary-100)', color: 'var(--primary-700)' }}>
                                {getInitials(player.player_name)}
                            </div>
                            <div className="player-card-info">
                                <h3 className="player-card-name">{player.player_name}</h3>
                                {player.team && (
                                    <p className="player-card-role">{player.team}</p>
                                )}
                                <div className="flex gap-4 mt-3">
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{player.matches_played}</div>
                                        <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Matches</div>
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{player.total_runs}</div>
                                        <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Runs</div>
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{player.total_wickets}</div>
                                        <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Wickets</div>
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: 600, color: 'var(--primary-600)' }}>
                                            {player.total_fantasy_points.toFixed(0)}
                                        </div>
                                        <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Points</div>
                                    </div>
                                </div>
                                {player.match_score && (
                                    <div className="mt-2">
                                        <span className="badge badge-neutral">
                                            Match: {player.match_score.toFixed(0)}%
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="card">
                    <div className="empty-state">
                        <div className="empty-state-icon">🏏</div>
                        <h3 className="empty-state-title">Search for players</h3>
                        <p className="empty-state-description">
                            Enter a player name to find matching results
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

export default PlayersPage;
