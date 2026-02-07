/**
 * Auctions List Page
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import auctionService from '../services/auctionService';

function AuctionsListPage() {
    const { isManager } = useAuth();
    const [auctions, setAuctions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        const fetchAuctions = async () => {
            try {
                const data = await auctionService.listAuctions();
                setAuctions(data);
            } catch (err) {
                console.error('Failed to fetch auctions:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchAuctions();
    }, []);

    const filteredAuctions = auctions.filter((auction) => {
        // Filter by status
        if (filter !== 'all' && auction.status !== filter) {
            return false;
        }
        // Filter by search
        if (searchQuery && !auction.name.toLowerCase().includes(searchQuery.toLowerCase())) {
            return false;
        }
        return true;
    });

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
            {/* Header */}
            <div className="page-header">
                <div>
                    <h1 className="page-header-title">Auctions</h1>
                    <p className="text-secondary mt-2">Browse and join cricket auctions</p>
                </div>
                <Link to="/auctions/new" className="btn btn-primary">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Create Auction
                </Link>
            </div>

            {/* Filters */}
            <div className="flex gap-4 mb-6" style={{ flexWrap: 'wrap' }}>
                <div className="form-group" style={{ marginBottom: 0, flex: '1 1 200px' }}>
                    <input
                        type="text"
                        className="form-input"
                        placeholder="Search auctions..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <div className="flex gap-2">
                    {['all', 'live', 'draft', 'paused', 'completed'].map((status) => (
                        <button
                            key={status}
                            className={`btn btn-sm ${filter === status ? 'btn-primary' : 'btn-secondary'}`}
                            onClick={() => setFilter(status)}
                        >
                            {status.charAt(0).toUpperCase() + status.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Auctions Grid */}
            {loading ? (
                <div className="loader">
                    <div className="spinner" />
                </div>
            ) : filteredAuctions.length === 0 ? (
                <div className="card">
                    <div className="empty-state">
                        <div className="empty-state-icon">🔍</div>
                        <h3 className="empty-state-title">No auctions found</h3>
                        <p className="empty-state-description">
                            {searchQuery || filter !== 'all'
                                ? 'Try adjusting your filters'
                                : 'No auctions have been created yet'}
                        </p>
                    </div>
                </div>
            ) : (
                <div className="auction-grid">
                    {filteredAuctions.map((auction) => (
                        <Link
                            key={auction.id}
                            to={auction.status === 'live' ? `/auctions/${auction.id}/live` : `/auctions/${auction.id}`}
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
                                        {auction.status === 'live' ? '● LIVE' : auction.status.toUpperCase()}
                                    </span>
                                </div>

                                <div className="auction-card-stats mt-4">
                                    <div className="auction-stat">
                                        <div className="auction-stat-value">
                                            {auction.initial_purse || 100}
                                        </div>
                                        <div className="auction-stat-label">Cr Purse</div>
                                    </div>
                                    <div className="auction-stat">
                                        <div className="auction-stat-value">
                                            {auction.max_team_size || 25}
                                        </div>
                                        <div className="auction-stat-label">Max Players</div>
                                    </div>
                                    <div className="auction-stat">
                                        <div className="auction-stat-value">
                                            {auction.min_bid_increment || 0.5}
                                        </div>
                                        <div className="auction-stat-label">Min Bid</div>
                                    </div>
                                </div>

                                {auction.status === 'live' && (
                                    <div className="mt-4">
                                        <span className="btn btn-accent btn-sm" style={{ width: '100%', pointerEvents: 'none' }}>
                                            Join Live Auction →
                                        </span>
                                    </div>
                                )}
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}

export default AuctionsListPage;
