/**
 * Live Auction Room Page
 */
import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import useAuctionWebSocket from '../hooks/useAuctionWebSocket';
import auctionService from '../services/auctionService';

function LiveAuctionPage() {
    const { auctionId } = useParams();
    const { user } = useAuth();
    const token = localStorage.getItem('token');

    const [auction, setAuction] = useState(null);
    const [customBid, setCustomBid] = useState('');
    const [loading, setLoading] = useState(true);
    const [playerPool, setPlayerPool] = useState([]);
    const [selectedPlayer, setSelectedPlayer] = useState(null);

    const {
        connected,
        auctionState,
        bidHistory,
        error,
        userRole,
        teamId,
        placeBid,
        presentPlayer,
        sellPlayer,
        markUnsold,
    } = useAuctionWebSocket(auctionId, token);

    const isAdmin = userRole === 'admin';

    // Fetch auction details and player pool
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [auctionData, poolData] = await Promise.all([
                    auctionService.getAuction(auctionId),
                    auctionService.getPlayerPool(auctionId),
                ]);
                setAuction(auctionData);
                setPlayerPool(poolData);
            } catch (err) {
                console.error('Failed to fetch auction data:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [auctionId]);

    // Get available players for admin selection
    const availablePlayers = useMemo(() => {
        return playerPool.filter(p => p.status === 'available');
    }, [playerPool]);

    // Calculate bid increments based on current bid
    const bidIncrements = useMemo(() => {
        const current = auctionState?.current_player?.current_bid ||
            auctionState?.current_player?.base_price || 0;
        const min = auction?.min_bid_increment || 0.5;
        return [min, min * 2, min * 4, min * 10];
    }, [auctionState, auction]);

    const currentBid = auctionState?.current_player?.current_bid ||
        auctionState?.current_player?.base_price || 0;

    const handleQuickBid = (increment) => {
        placeBid(currentBid + increment);
    };

    const handleCustomBid = () => {
        const amount = parseFloat(customBid);
        if (amount > currentBid) {
            placeBid(amount);
            setCustomBid('');
        }
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

    const formatCurrency = (amount) => {
        return `₹${amount.toFixed(2)} Cr`;
    };

    if (loading) {
        return (
            <div className="loader" style={{ minHeight: '50vh' }}>
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div className="animate-fadeIn">
            {/* Header */}
            <div className="flex items-center justify-between mb-6" style={{ flexWrap: 'wrap', gap: 'var(--space-4)' }}>
                <div>
                    <Link to={`/auctions/${auctionId}`} className="text-muted mb-2" style={{ display: 'block', fontSize: 'var(--text-sm)' }}>
                        ← Back to auction
                    </Link>
                    <h1>{auction?.name || 'Live Auction'}</h1>
                </div>
                <div className="flex items-center gap-3">
                    <span className={`badge ${connected ? 'badge-success' : 'badge-error'}`}>
                        {connected ? '● Connected' : '○ Disconnected'}
                    </span>
                    {auctionState?.status === 'live' && (
                        <span className="badge badge-live">LIVE</span>
                    )}
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="toast toast-error mb-4" style={{ position: 'relative', width: '100%' }}>
                    {error}
                </div>
            )}

            {/* Main Grid */}
            <div className="auction-room">
                {/* Current Player */}
                <div className="auction-room-player">
                    <div className="card player-card-current card-elevated">
                        {auctionState?.current_player ? (
                            <>
                                <div className="avatar avatar-xl player-avatar-large">
                                    {getInitials(auctionState.current_player.name)}
                                </div>
                                <h2 className="player-name-large">
                                    {auctionState.current_player.name}
                                </h2>
                                <p className="player-team">Base Price: {formatCurrency(auctionState.current_player.base_price)}</p>

                                {/* Current Bid Section */}
                                <div className="current-bid-section">
                                    <p className="current-bid-label">Current Bid</p>
                                    <p className={`current-bid-amount ${bidHistory.length > 0 ? 'animate' : ''}`}>
                                        {formatCurrency(currentBid)}
                                    </p>
                                    {auctionState.current_player.current_bidder_name && (
                                        <p className="current-bidder">
                                            by {auctionState.current_player.current_bidder_name}
                                        </p>
                                    )}
                                </div>

                                {/* Bid Buttons - Only show if user has a team */}
                                {teamId && (
                                    <div className="bid-buttons">
                                        {bidIncrements.map((increment) => (
                                            <button
                                                key={increment}
                                                className="btn btn-primary bid-btn"
                                                onClick={() => handleQuickBid(increment)}
                                                disabled={!connected}
                                            >
                                                +{increment} Cr
                                            </button>
                                        ))}
                                        <div className="bid-btn-custom">
                                            <input
                                                type="number"
                                                className="form-input bid-input"
                                                placeholder="Amount"
                                                value={customBid}
                                                onChange={(e) => setCustomBid(e.target.value)}
                                                step="0.1"
                                                min={currentBid + 0.1}
                                            />
                                            <button
                                                className="btn btn-accent"
                                                onClick={handleCustomBid}
                                                disabled={!connected || !customBid}
                                            >
                                                Bid
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {!teamId && userRole === 'spectator' && (
                                    <p className="text-muted mt-4">
                                        You are viewing as a spectator. Create a team to participate.
                                    </p>
                                )}

                                {/* Admin Controls - Sell/Unsold Buttons */}
                                {isAdmin && auctionState?.current_player && (
                                    <div className="admin-controls mt-4" style={{ borderTop: '1px solid var(--border)', paddingTop: 'var(--space-4)' }}>
                                        <p className="text-muted mb-2" style={{ fontSize: 'var(--text-xs)' }}>Auctioneer Controls</p>
                                        <div className="flex gap-2">
                                            <button
                                                className="btn btn-success"
                                                onClick={() => sellPlayer(auctionState.current_player.id)}
                                                disabled={!auctionState.current_player.current_bidder_id}
                                            >
                                                ✓ Sell to {auctionState.current_player.current_bidder_name || 'highest bidder'}
                                            </button>
                                            <button
                                                className="btn btn-secondary"
                                                onClick={() => markUnsold(auctionState.current_player.id)}
                                            >
                                                ✗ Mark Unsold
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="empty-state">
                                <div className="empty-state-icon">🏏</div>
                                <h3 className="empty-state-title">Waiting for player</h3>
                                <p className="empty-state-description">
                                    {auctionState?.status === 'live'
                                        ? 'The auctioneer will present a player shortly'
                                        : 'The auction has not started yet'}
                                </p>

                                {/* Admin: Select and Present Player */}
                                {isAdmin && auctionState?.status === 'live' && availablePlayers.length > 0 && (
                                    <div className="mt-4" style={{ textAlign: 'left' }}>
                                        <label className="form-label">Select player to present:</label>
                                        <select
                                            className="form-input"
                                            value={selectedPlayer || ''}
                                            onChange={(e) => setSelectedPlayer(e.target.value)}
                                            style={{ marginBottom: 'var(--space-2)' }}
                                        >
                                            <option value="">Choose a player...</option>
                                            {availablePlayers.map((p) => (
                                                <option key={p.id} value={p.id}>
                                                    {p.display_name || p.custom_name} - Base: ₹{p.base_price} Cr
                                                </option>
                                            ))}
                                        </select>
                                        <button
                                            className="btn btn-primary"
                                            disabled={!selectedPlayer}
                                            onClick={() => {
                                                presentPlayer(parseInt(selectedPlayer));
                                                setSelectedPlayer(null);
                                            }}
                                        >
                                            Present Player
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Teams Panel */}
                <div className="auction-room-teams">
                    <div className="card">
                        <div className="card-header">
                            <h3 style={{ margin: 0, fontSize: 'var(--text-base)' }}>Teams</h3>
                        </div>
                        <div className="teams-panel">
                            {auctionState?.teams?.length > 0 ? (
                                auctionState.teams.map((team) => (
                                    <div
                                        key={team.id}
                                        className="team-row"
                                        style={{
                                            background: team.id === teamId ? 'var(--primary-50)' : 'transparent',
                                        }}
                                    >
                                        <div
                                            className="team-color-dot"
                                            style={{ background: `hsl(${(team.id * 47) % 360}, 60%, 50%)` }}
                                        />
                                        <div className="team-info">
                                            <div className="team-name">{team.name}</div>
                                            <div className="team-purse">{formatCurrency(team.purse)}</div>
                                        </div>
                                        <div className="team-players-count">{team.players_count} players</div>
                                    </div>
                                ))
                            ) : (
                                <div className="p-4 text-center text-muted">No teams yet</div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Bid History */}
                <div className="auction-room-history">
                    <div className="card" style={{ height: '100%' }}>
                        <div className="card-header">
                            <h3 style={{ margin: 0, fontSize: 'var(--text-base)' }}>Bid History</h3>
                        </div>
                        <div className="bid-history">
                            {bidHistory.length > 0 ? (
                                bidHistory.map((bid) => (
                                    <div key={bid.id} className="bid-history-item">
                                        <div
                                            className="team-color-dot"
                                            style={{ background: `hsl(${(bid.teamId * 47) % 360}, 60%, 50%)` }}
                                        />
                                        <span className="bid-history-team">{bid.teamName}</span>
                                        <span className="bid-history-amount">{formatCurrency(bid.amount)}</span>
                                    </div>
                                ))
                            ) : (
                                <div className="p-4 text-center text-muted">No bids yet</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Stats Bar */}
            <div className="grid mt-6" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 'var(--space-4)' }}>
                <div className="card p-4 text-center">
                    <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--primary-600)' }}>
                        {auctionState?.available_players || 0}
                    </div>
                    <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Available</div>
                </div>
                <div className="card p-4 text-center">
                    <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--success)' }}>
                        {auctionState?.sold_players || 0}
                    </div>
                    <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Sold</div>
                </div>
                <div className="card p-4 text-center">
                    <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--text-muted)' }}>
                        {auctionState?.unsold_players || 0}
                    </div>
                    <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Unsold</div>
                </div>
            </div>
        </div>
    );
}

export default LiveAuctionPage;
