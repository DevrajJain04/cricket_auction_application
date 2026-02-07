/**
 * Settings Page - User Profile & Account Settings
 */
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

function SettingsPage() {
    const { user, logout } = useAuth();
    const [activeTab, setActiveTab] = useState('profile');

    const tabs = [
        { id: 'profile', label: 'Profile', icon: '👤' },
        { id: 'preferences', label: 'Preferences', icon: '⚙️' },
        { id: 'security', label: 'Security', icon: '🔒' },
    ];

    return (
        <div className="animate-fadeIn">
            <div className="page-header">
                <div>
                    <h1 className="page-header-title">Settings</h1>
                    <p className="text-secondary mt-2">Manage your account and preferences</p>
                </div>
            </div>

            <div className="grid" style={{ gridTemplateColumns: '240px 1fr', gap: 'var(--space-6)', alignItems: 'start' }}>
                {/* Sidebar Tabs */}
                <div className="card p-4">
                    <nav style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-ghost'}`}
                                style={{ justifyContent: 'flex-start' }}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                <span>{tab.icon}</span>
                                {tab.label}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Content */}
                <div className="card">
                    <div className="card-body">
                        {activeTab === 'profile' && (
                            <div>
                                <h2 style={{ marginBottom: 'var(--space-6)' }}>Profile Information</h2>

                                <div className="flex items-center gap-6 mb-8">
                                    <div className="avatar avatar-xl" style={{ fontSize: 'var(--text-3xl)' }}>
                                        {user?.display_name?.charAt(0) || '?'}
                                    </div>
                                    <div>
                                        <h3 style={{ margin: 0 }}>{user?.display_name}</h3>
                                        <p className="text-muted" style={{ margin: 0 }}>{user?.email}</p>
                                        <span className={`badge mt-2 ${user?.role === 'admin' ? 'badge-error' : user?.role === 'auction_manager' ? 'badge-warning' : 'badge-neutral'}`}>
                                            {user?.role?.replace('_', ' ')?.toUpperCase() || 'USER'}
                                        </span>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Display Name</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={user?.display_name || ''}
                                        disabled
                                        style={{ maxWidth: '400px' }}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Email Address</label>
                                    <input
                                        type="email"
                                        className="form-input"
                                        value={user?.email || ''}
                                        disabled
                                        style={{ maxWidth: '400px' }}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">User ID</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={user?.id || ''}
                                        disabled
                                        style={{ maxWidth: '200px' }}
                                    />
                                </div>
                            </div>
                        )}

                        {activeTab === 'preferences' && (
                            <div>
                                <h2 style={{ marginBottom: 'var(--space-6)' }}>Preferences</h2>

                                <div className="form-group">
                                    <label className="form-label">Theme</label>
                                    <select className="form-input" style={{ maxWidth: '300px' }} defaultValue="light">
                                        <option value="light">Light (Cricket Classic)</option>
                                        <option value="dark">Dark Mode</option>
                                        <option value="system">System Default</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Notifications</label>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                                            <input type="checkbox" defaultChecked /> Auction start alerts
                                        </label>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                                            <input type="checkbox" defaultChecked /> Bid notifications
                                        </label>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                                            <input type="checkbox" defaultChecked /> Player sold alerts
                                        </label>
                                    </div>
                                </div>

                                <button className="btn btn-primary mt-4">
                                    Save Preferences
                                </button>
                            </div>
                        )}

                        {activeTab === 'security' && (
                            <div>
                                <h2 style={{ marginBottom: 'var(--space-6)' }}>Security</h2>

                                <div className="card p-4 mb-4" style={{ background: 'var(--bg-secondary)' }}>
                                    <h4 style={{ margin: '0 0 var(--space-2)' }}>Change Password</h4>
                                    <p className="text-muted" style={{ fontSize: 'var(--text-sm)', margin: '0 0 var(--space-4)' }}>
                                        Update your password to keep your account secure
                                    </p>
                                    <button className="btn btn-secondary">Change Password</button>
                                </div>

                                <div className="card p-4 mb-4" style={{ background: 'var(--bg-secondary)' }}>
                                    <h4 style={{ margin: '0 0 var(--space-2)' }}>Active Sessions</h4>
                                    <p className="text-muted" style={{ fontSize: 'var(--text-sm)', margin: '0 0 var(--space-4)' }}>
                                        You are currently logged in on this device
                                    </p>
                                    <button className="btn btn-secondary btn-sm">View All Sessions</button>
                                </div>

                                <div className="card p-4" style={{ background: 'rgba(196, 90, 81, 0.1)', border: '1px solid var(--accent-500)' }}>
                                    <h4 style={{ margin: '0 0 var(--space-2)', color: 'var(--accent-600)' }}>Danger Zone</h4>
                                    <p className="text-muted" style={{ fontSize: 'var(--text-sm)', margin: '0 0 var(--space-4)' }}>
                                        Log out from all devices
                                    </p>
                                    <button className="btn btn-accent" onClick={logout}>
                                        Log Out
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SettingsPage;
