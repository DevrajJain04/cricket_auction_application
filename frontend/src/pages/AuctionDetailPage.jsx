/**
 * Auction Detail Page
 */
import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import auctionService from '../services/auctionService';
import teamService from '../services/teamService';

function AuctionDetailPage() {
    const { auctionId } = useParams();
    const navigate = useNavigate();
    const { user, isManager } = useAuth();

    const [auction, setAuction] = useState(null);
    const [teams, setTeams] = useState([]);
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Create Team Modal
    const [showCreateTeam, setShowCreateTeam] = useState(false);
    const [teamForm, setTeamForm] = useState({ team_name: '', team_code: '', team_color: '#2f4c3e' });
    const [creatingTeam, setCreatingTeam] = useState(false);

    // Add Player Modal
    const [showAddPlayer, setShowAddPlayer] = useState(false);
    const [playerForm, setPlayerForm] = useState({ custom_name: '', base_price: 1.0 });
    const [addingPlayer, setAddingPlayer] = useState(false);

    useEffect(() => {
        // Only fetch if auctionId is a valid numeric ID
        if (auctionId && !isNaN(parseInt(auctionId))) {
            fetchData();
        } else {
            setLoading(false);
            setError('Invalid auction ID');
        }
    }, [auctionId]);

    const fetchData = async () => {
        try {
            const [auctionData, teamsData, playersData] = await Promise.all([
                auctionService.getAuction(auctionId),
                teamService.listTeams(auctionId),
                auctionService.getPlayerPool(auctionId),
            ]);
            setAuction(auctionData);
            setTeams(teamsData);
            setPlayers(playersData);
        } catch (err) {
            setError(err.message || 'Failed to load auction');
        } finally {
            setLoading(false);
        }
    };

    const handleStartAuction = async () => {
        try {
            await auctionService.startAuction(auctionId);
            navigate(`/auctions/${auctionId}/live`);
        } catch (err) {
            setError(err.message || 'Failed to start auction');
        }
    };

    const handleCreateTeam = async (e) => {
        e.preventDefault();
        setCreatingTeam(true);
        try {
            await teamService.createTeam(auctionId, teamForm);
            setShowCreateTeam(false);
            setTeamForm({ team_name: '', team_code: '', team_color: '#2f4c3e' });
            fetchData();
        } catch (err) {
            setError(err.message || 'Failed to create team');
        } finally {
            setCreatingTeam(false);
        }
    };

    const handleAddPlayer = async (e) => {
        e.preventDefault();
        setAddingPlayer(true);
        try {
            await auctionService.addPlayerToPool(auctionId, playerForm);
            setShowAddPlayer(false);
            setPlayerForm({ custom_name: '', base_price: 1.0 });
            fetchData();
        } catch (err) {
            setError(err.message || 'Failed to add player');
        } finally {
            setAddingPlayer(false);
        }
    };

    const getStatusBadge = (status) => {
        const badges = {
            draft: 'badge-neutral',
            live: 'badge-live',
            paused: 'badge-warning',
            completed: 'badge-success',
        };
        return badges[status] || 'badge-neutral';
    };

    const isOwner = auction?.owner_id === user?.id;
    const canManage = isManager || isOwner;

    if (loading) {
        return (
            <div className="loader" style={{ minHeight: '50vh' }}>
                <div className="spinner" />
            </div>
        );
    }

    if (!auction) {
        return (
            <div className="card">
                <div className="empty-state">
                    <div className="empty-state-icon">🔍</div>
                    <h3 className="empty-state-title">Auction not found</h3>
                    <Link to="/auctions" className="btn btn-primary">Back to Auctions</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="animate-fadeIn">
            {/* Header */}
            <div className="mb-4">
                <Link to="/auctions" className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>
                    ← Back to auctions
                </Link>
            </div>

            {error && (
                <div className="toast toast-error mb-4" style={{ position: 'relative', width: '100%' }}>
                    {error}
                    <button onClick={() => setError('')} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer' }}>×</button>
                </div>
            )}

            <div className="page-header">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="page-header-title">{auction.name}</h1>
                        <span className={`badge ${getStatusBadge(auction.status)}`}>
                            {auction.status.toUpperCase()}
                        </span>
                    </div>
                    <p className="text-secondary mt-2">{auction.description || 'No description'}</p>
                </div>
                <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                    {auction.status === 'live' && (
                        <Link to={`/auctions/${auctionId}/live`} className="btn btn-accent">
                            Join Live →
                        </Link>
                    )}
                    {canManage && auction.status === 'draft' && teams.length >= 2 && players.length > 0 && (
                        <button onClick={handleStartAuction} className="btn btn-primary">
                            Start Auction
                        </button>
                    )}
                </div>
            </div>

            {/* Stats */}
            <div className="grid mb-6" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 'var(--space-4)' }}>
                <div className="card p-4 text-center">
                    <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--primary-600)' }}>
                        ₹{auction.initial_purse} Cr
                    </div>
                    <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Initial Purse</div>
                </div>
                <div className="card p-4 text-center">
                    <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--accent)' }}>
                        {teams.length}
                    </div>
                    <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Teams</div>
                </div>
                <div className="card p-4 text-center">
                    <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--success)' }}>
                        {players.length}
                    </div>
                    <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Players</div>
                </div>
                <div className="card p-4 text-center">
                    <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700 }}>
                        {auction.max_team_size}
                    </div>
                    <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Max Team Size</div>
                </div>
            </div>

            {/* Teams Section */}
            <div className="mb-8">
                <div className="flex items-center justify-between mb-4">
                    <h2>Teams ({teams.length})</h2>
                    {auction.status === 'draft' && (
                        <button onClick={() => setShowCreateTeam(true)} className="btn btn-primary btn-sm">
                            + Create Team
                        </button>
                    )}
                </div>

                {teams.length === 0 ? (
                    <div className="card p-6 text-center">
                        <p className="text-muted">No teams yet. Create a team to get started.</p>
                    </div>
                ) : (
                    <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 'var(--space-4)' }}>
                        {teams.map((team) => (
                            <div key={team.id} className="card card-elevated p-4">
                                <div className="flex items-center gap-3 mb-3">
                                    <div
                                        style={{
                                            width: 40,
                                            height: 40,
                                            borderRadius: 'var(--radius-md)',
                                            background: team.team_color || 'var(--primary-600)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: 'white',
                                            fontWeight: 700,
                                        }}
                                    >
                                        {team.team_code}
                                    </div>
                                    <div>
                                        <h4 style={{ margin: 0 }}>{team.team_name}</h4>
                                        <p className="text-muted" style={{ fontSize: 'var(--text-xs)', margin: 0 }}>
                                            Purse: ₹{team.purse_remaining?.toFixed(2) || team.initial_purse} Cr
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Players Section */}
            <div>
                <div className="flex items-center justify-between mb-4">
                    <h2>Player Pool ({players.length})</h2>
                    {canManage && auction.status === 'draft' && auction.auction_type === 'community' && (
                        <button onClick={() => setShowAddPlayer(true)} className="btn btn-primary btn-sm">
                            + Add Player
                        </button>
                    )}
                </div>

                {players.length === 0 ? (
                    <div className="card p-6 text-center">
                        <p className="text-muted">No players in the pool yet.</p>
                    </div>
                ) : (
                    <div className="card">
                        <div className="table-container">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Base Price</th>
                                        <th>Status</th>
                                        <th>Sold For</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {players.map((player) => (
                                        <tr key={player.id}>
                                            <td className="font-medium">{player.name}</td>
                                            <td>₹{player.base_price} Cr</td>
                                            <td>
                                                <span className={`badge ${player.status === 'sold' ? 'badge-success' : player.status === 'unsold' ? 'badge-error' : 'badge-neutral'}`}>
                                                    {player.status}
                                                </span>
                                            </td>
                                            <td>{player.sold_for ? `₹${player.sold_for} Cr` : '-'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>

            {/* Create Team Modal */}
            {showCreateTeam && (
                <div className="modal-overlay" onClick={() => setShowCreateTeam(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Create Team</h3>
                            <button className="modal-close" onClick={() => setShowCreateTeam(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreateTeam}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Team Name</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={teamForm.team_name}
                                        onChange={(e) => setTeamForm({ ...teamForm, team_name: e.target.value })}
                                        required
                                        minLength={2}
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Team Code (2-10 chars)</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={teamForm.team_code}
                                        onChange={(e) => setTeamForm({ ...teamForm, team_code: e.target.value.toUpperCase() })}
                                        required
                                        minLength={2}
                                        maxLength={10}
                                        placeholder="e.g., CSK, MI"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Team Color</label>
                                    <input
                                        type="color"
                                        className="form-input"
                                        value={teamForm.team_color}
                                        onChange={(e) => setTeamForm({ ...teamForm, team_color: e.target.value })}
                                        style={{ height: 44, padding: 4 }}
                                    />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateTeam(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={creatingTeam}>
                                    {creatingTeam ? 'Creating...' : 'Create Team'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Add Player Modal */}
            {showAddPlayer && (
                <div className="modal-overlay" onClick={() => setShowAddPlayer(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add Player to Pool</h3>
                            <button className="modal-close" onClick={() => setShowAddPlayer(false)}>×</button>
                        </div>
                        <form onSubmit={handleAddPlayer}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Player Name</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={playerForm.custom_name}
                                        onChange={(e) => setPlayerForm({ ...playerForm, custom_name: e.target.value })}
                                        required
                                        placeholder="Enter player name"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Base Price (Cr)</label>
                                    <input
                                        type="number"
                                        className="form-input"
                                        value={playerForm.base_price}
                                        onChange={(e) => setPlayerForm({ ...playerForm, base_price: parseFloat(e.target.value) })}
                                        min={0}
                                        step={0.1}
                                    />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowAddPlayer(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={addingPlayer}>
                                    {addingPlayer ? 'Adding...' : 'Add Player'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AuctionDetailPage;
