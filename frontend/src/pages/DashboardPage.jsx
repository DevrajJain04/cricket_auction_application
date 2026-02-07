/**
 * Dashboard Page
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import auctionService from '../services/auctionService';

function DashboardPage() {
    const { user } = useAuth();
    const [auctions, setAuctions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await auctionService.listAuctions();
                setAuctions(data);
            } catch (err) {
                console.error('Failed to fetch auctions:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const liveAuctions = auctions.filter((a) => a.status === 'live');
    const myTeamsCount = 0; // TODO: Fetch actual team count

    const getStatusBadge = (status) => {
        const badges = {
            draft: 'badge-neutral',
            live: 'badge-live',
            paused: 'badge-warning',
            completed: 'badge-success',
        };
        return badges[status] || 'badge-neutral';
    };

    return (
        <div className="animate-fadeIn">
            {/* Welcome Section */}
            <div className="mb-8">
                <h1 style={{ marginBottom: 'var(--space-2)' }}>
                    Welcome back, {user?.display_name?.split(' ')[0] || 'Player'}! 👋
                </h1>
                <p className="text-secondary">
                    Here's what's happening in the Shroff Premier League
                </p>
            </div>

            {/* Stats Grid */}
            <div className="dashboard-grid mb-8">
                <div className="card stat-card card-elevated">
                    <div className="stat-icon stat-icon-primary">🏏</div>
                    <div className="stat-value">{liveAuctions.length}</div>
                    <div className="stat-label">Live Auctions</div>
                </div>

                <div className="card stat-card card-elevated">
                    <div className="stat-icon stat-icon-accent">👥</div>
                    <div className="stat-value">{myTeamsCount}</div>
                    <div className="stat-label">My Teams</div>
                </div>

                <div className="card stat-card card-elevated">
                    <div className="stat-icon stat-icon-gold">🏆</div>
                    <div className="stat-value">{auctions.length}</div>
                    <div className="stat-label">Total Auctions</div>
                </div>
            </div>

            {/* Live Auctions */}
            {liveAuctions.length > 0 && (
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h2>🔴 Live Now</h2>
                        <Link to="/auctions" className="btn btn-ghost btn-sm">
                            View All
                        </Link>
                    </div>

                    <div className="auction-grid">
                        {liveAuctions.map((auction) => (
                            <Link
                                key={auction.id}
                                to={`/auctions/${auction.id}/live`}
                                className="card card-elevated auction-card"
                                style={{ textDecoration: 'none' }}
                            >
                                <div className="card-body">
                                    <div className="auction-card-header">
                                        <div>
                                            <h3 className="auction-card-title">{auction.name}</h3>
                                            <p className="auction-card-type">
                                                {auction.auction_type === 'ipl_tracker' ? 'IPL Tracker' : 'Community'}
                                            </p>
                                        </div>
                                        <span className={`badge ${getStatusBadge(auction.status)}`}>
                                            {auction.status.toUpperCase()}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 mt-4">
                                        <span className="btn btn-primary btn-sm" style={{ pointerEvents: 'none' }}>
                                            Join Auction →
                                        </span>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* Recent Auctions */}
            <div>
                <div className="flex items-center justify-between mb-4">
                    <h2>Recent Auctions</h2>
                    <Link to="/auctions" className="btn btn-ghost btn-sm">
                        View All
                    </Link>
                </div>

                {loading ? (
                    <div className="loader">
                        <div className="spinner" />
                    </div>
                ) : auctions.length === 0 ? (
                    <div className="card">
                        <div className="empty-state">
                            <div className="empty-state-icon">🏏</div>
                            <h3 className="empty-state-title">No auctions yet</h3>
                            <p className="empty-state-description">
                                Create your first auction or wait for one to be created.
                            </p>
                            <Link to="/auctions/new" className="btn btn-primary">
                                Create Auction
                            </Link>
                        </div>
                    </div>
                ) : (
                    <div className="auction-grid">
                        {auctions.slice(0, 6).map((auction) => (
                            <Link
                                key={auction.id}
                                to={`/auctions/${auction.id}`}
                                className="card card-elevated auction-card"
                                style={{ textDecoration: 'none' }}
                            >
                                <div className="card-body">
                                    <div className="auction-card-header">
                                        <div>
                                            <h3 className="auction-card-title">{auction.name}</h3>
                                            <p className="auction-card-type">
                                                {auction.auction_type === 'ipl_tracker' ? 'IPL Tracker' : 'Community'}
                                            </p>
                                        </div>
                                        <span className={`badge ${getStatusBadge(auction.status)}`}>
                                            {auction.status}
                                        </span>
                                    </div>
                                    <p className="text-muted mt-2" style={{ fontSize: 'var(--text-xs)' }}>
                                        Created {new Date(auction.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default DashboardPage;
