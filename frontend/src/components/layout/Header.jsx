/**
 * Header Component
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

function Header({ onMenuClick, pageTitle }) {
    const { user, logout } = useAuth();
    const [dropdownOpen, setDropdownOpen] = useState(false);

    const getInitials = (name) => {
        if (!name) return 'U';
        return name
            .split(' ')
            .map((n) => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    };

    return (
        <header className="app-header">
            <div className="header-left">
                <button className="menu-toggle" onClick={onMenuClick} aria-label="Toggle menu">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 12h18M3 6h18M3 18h18" />
                    </svg>
                </button>
                {pageTitle && <h1 className="page-title">{pageTitle}</h1>}
            </div>

            <div className="header-right">
                {/* Notifications */}
                <button className="btn btn-ghost btn-icon" aria-label="Notifications">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                    </svg>
                </button>

                {/* User Menu */}
                <div className="dropdown">
                    <div
                        className="header-user"
                        onClick={() => setDropdownOpen(!dropdownOpen)}
                        role="button"
                        tabIndex={0}
                    >
                        <div className="avatar avatar-sm">
                            {getInitials(user?.display_name || user?.email)}
                        </div>
                        <span className="header-user-name">{user?.display_name || user?.email}</span>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M6 9l6 6 6-6" />
                        </svg>
                    </div>

                    {dropdownOpen && (
                        <>
                            <div
                                className="sidebar-overlay visible"
                                style={{ background: 'transparent' }}
                                onClick={() => setDropdownOpen(false)}
                            />
                            <div className="dropdown-menu">
                                <div className="dropdown-item" style={{ pointerEvents: 'none' }}>
                                    <span className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>
                                        Signed in as
                                    </span>
                                </div>
                                <div className="dropdown-item" style={{ pointerEvents: 'none' }}>
                                    <strong>{user?.email}</strong>
                                </div>
                                <div className="dropdown-divider" />
                                <Link to="/profile" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                        <circle cx="12" cy="7" r="4" />
                                    </svg>
                                    Profile
                                </Link>
                                <div className="dropdown-divider" />
                                <button className="dropdown-item" onClick={logout}>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                        <polyline points="16 17 21 12 16 7" />
                                        <line x1="21" y1="12" x2="9" y2="12" />
                                    </svg>
                                    Logout
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}

export default Header;
