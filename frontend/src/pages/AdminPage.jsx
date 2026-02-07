/**
 * Admin Panel Page - User Management & System Stats
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import api from '../services/api';

function AdminPage() {
    const { user, isAdmin } = useAuth();
    const [activeTab, setActiveTab] = useState('overview');
    const [stats, setStats] = useState({ users: 0, auctions: 0, teams: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                // These would be admin-only endpoints in a real app
                const auctionsRes = await api.get('/auctions');
                setStats({
                    auctions: auctionsRes.data?.length || 0,
                    users: 12, // Placeholder
                    teams: 8,  // Placeholder
                });
            } catch (err) {
                console.error('Failed to fetch stats:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (!isAdmin) {
        return <Navigate to="/" replace />;
    }

    return (
        <div className="animate-fadeIn">
            <div className="page-header">
                <div>
                    <h1 className="page-header-title">Admin Panel</h1>
                    <p className="text-secondary mt-2">System administration and monitoring</p>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid mb-6" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-4)' }}>
                <div className="card card-elevated p-4">
                    <div className="flex items-center gap-4">
                        <div style={{ fontSize: '2rem' }}>👥</div>
                        <div>
                            <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700 }}>{stats.users}</div>
                            <div className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>Total Users</div>
                        </div>
                    </div>
                </div>
                <div className="card card-elevated p-4">
                    <div className="flex items-center gap-4">
                        <div style={{ fontSize: '2rem' }}>🏏</div>
                        <div>
                            <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700 }}>{stats.auctions}</div>
                            <div className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>Auctions</div>
                        </div>
                    </div>
                </div>
                <div className="card card-elevated p-4">
                    <div className="flex items-center gap-4">
                        <div style={{ fontSize: '2rem' }}>🏆</div>
                        <div>
                            <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700 }}>{stats.teams}</div>
                            <div className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>Teams</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
                {['overview', 'users', 'system'].map((tab) => (
                    <button
                        key={tab}
                        className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setActiveTab(tab)}
                    >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="card">
                <div className="card-body">
                    {loading ? (
                        <div className="loader"><div className="spinner" /></div>
                    ) : activeTab === 'overview' ? (
                        <div>
                            <h3>System Overview</h3>
                            <p className="text-muted">Welcome to the administration panel, {user?.display_name}.</p>

                            <div className="mt-6">
                                <h4>Quick Actions</h4>
                                <div className="flex gap-3 mt-4" style={{ flexWrap: 'wrap' }}>
                                    <button className="btn btn-primary">Create Auction</button>
                                    <button className="btn btn-secondary">Manage Users</button>
                                    <button className="btn btn-secondary">View Reports</button>
                                </div>
                            </div>

                            <div className="mt-8">
                                <h4>Recent Activity</h4>
                                <div className="card mt-4" style={{ background: 'var(--bg-secondary)' }}>
                                    <div className="p-4">
                                        <p className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>
                                            <strong>System:</strong> Application started successfully
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : activeTab === 'users' ? (
                        <div>
                            <h3>User Management</h3>
                            <p className="text-muted mb-4">Manage user accounts and permissions</p>

                            <div className="table-container">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>User</th>
                                            <th>Email</th>
                                            <th>Role</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td className="font-medium">{user?.display_name}</td>
                                            <td>{user?.email}</td>
                                            <td><span className="badge badge-error">ADMIN</span></td>
                                            <td><span className="badge badge-success">Active</span></td>
                                            <td>
                                                <button className="btn btn-ghost btn-sm">Edit</button>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : (
                        <div>
                            <h3>System Settings</h3>
                            <p className="text-muted mb-4">Configure system-wide settings</p>

                            <div className="form-group">
                                <label className="form-label">Application Name</label>
                                <input type="text" className="form-input" defaultValue="SPL Auction" style={{ maxWidth: '400px' }} />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Default Purse Amount (Cr)</label>
                                <input type="number" className="form-input" defaultValue="100" style={{ maxWidth: '200px' }} />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Max Team Size</label>
                                <input type="number" className="form-input" defaultValue="25" style={{ maxWidth: '200px' }} />
                            </div>

                            <button className="btn btn-primary mt-4">Save Settings</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default AdminPage;
