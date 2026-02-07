/**
 * My Teams Page
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import auctionService from '../services/auctionService';
import teamService from '../services/teamService';

function MyTeamsPage() {
    const [auctions, setAuctions] = useState([]);
    const [myTeams, setMyTeams] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const auctionsData = await auctionService.listAuctions();
                setAuctions(auctionsData);

                // Fetch teams for each auction
                const teamsPromises = auctionsData.map(async (auction) => {
                    try {
                        const teams = await teamService.listTeams(auction.id);
                        return teams.map((team) => ({ ...team, auctionName: auction.name, auctionId: auction.id }));
                    } catch {
                        return [];
                    }
                });

                const allTeams = await Promise.all(teamsPromises);
                setMyTeams(allTeams.flat());
            } catch (err) {
                console.error('Failed to fetch data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="loader" style={{ minHeight: '50vh' }}>
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div className="animate-fadeIn">
            <div className="page-header">
                <div>
                    <h1 className="page-header-title">My Teams</h1>
                    <p className="text-secondary mt-2">Manage your teams across auctions</p>
                </div>
            </div>

            {myTeams.length === 0 ? (
                <div className="card">
                    <div className="empty-state">
                        <div className="empty-state-icon">👥</div>
                        <h3 className="empty-state-title">No teams yet</h3>
                        <p className="empty-state-description">
                            Join an auction and create a team to get started
                        </p>
                        <Link to="/auctions" className="btn btn-primary">
                            Browse Auctions
                        </Link>
                    </div>
                </div>
            ) : (
                <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 'var(--space-4)' }}>
                    {myTeams.map((team) => (
                        <Link
                            key={team.id}
                            to={`/auctions/${team.auctionId}`}
                            className="card card-elevated"
                            style={{ textDecoration: 'none' }}
                        >
                            <div className="card-body">
                                <div className="flex items-center gap-4">
                                    <div
                                        style={{
                                            width: 56,
                                            height: 56,
                                            borderRadius: 'var(--radius-lg)',
                                            background: team.team_color || 'var(--primary-600)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: 'white',
                                            fontWeight: 700,
                                            fontSize: 'var(--text-lg)',
                                        }}
                                    >
                                        {team.team_code}
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <h3 style={{ margin: 0, marginBottom: 4 }}>{team.team_name}</h3>
                                        <p className="text-muted" style={{ margin: 0, fontSize: 'var(--text-sm)' }}>
                                            {team.auctionName}
                                        </p>
                                    </div>
                                </div>

                                <div className="grid mt-4" style={{ gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-3)' }}>
                                    <div className="text-center p-2" style={{ background: 'var(--surface-secondary)', borderRadius: 'var(--radius-sm)' }}>
                                        <div style={{ fontWeight: 600, color: 'var(--primary-600)' }}>
                                            ₹{team.purse_remaining?.toFixed(2) || team.initial_purse}
                                        </div>
                                        <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Purse (Cr)</div>
                                    </div>
                                    <div className="text-center p-2" style={{ background: 'var(--surface-secondary)', borderRadius: 'var(--radius-sm)' }}>
                                        <div style={{ fontWeight: 600 }}>
                                            ₹{team.initial_purse}
                                        </div>
                                        <div className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Initial (Cr)</div>
                                    </div>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}

export default MyTeamsPage;
