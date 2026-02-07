/**
 * Sidebar Component
 */
import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

function Sidebar({ isOpen, onClose }) {
    const { isManager, isAdmin } = useAuth();

    const navLinks = [
        {
            section: 'Main',
            links: [
                { to: '/', label: 'Dashboard', icon: 'home' },
                { to: '/auctions', label: 'Auctions', icon: 'gavel' },
            ],
        },
        {
            section: 'Teams',
            links: [
                { to: '/my-teams', label: 'My Teams', icon: 'users' },
            ],
        },
        {
            section: 'Players',
            links: [
                { to: '/players', label: 'Search Players', icon: 'search' },
            ],
        },
        {
            section: 'Account',
            links: [
                { to: '/settings', label: 'Settings', icon: 'settings' },
            ],
        },
    ];

    // Add Create Auction link for all users (in Auctions section)
    navLinks[0].links.push({ to: '/auctions/new', label: 'Create Auction', icon: 'plus' });

    // Add admin panel link only for admins
    if (isAdmin) {
        navLinks.splice(3, 0, {
            section: 'Admin',
            links: [
                { to: '/admin', label: 'Admin Panel', icon: 'admin' },
            ],
        });
    }

    const getIcon = (name) => {
        const icons = {
            home: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                    <polyline points="9 22 9 12 15 12 15 22" />
                </svg>
            ),
            gavel: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 6v6l4 2" />
                </svg>
            ),
            users: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>
            ),
            search: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <path d="M21 21l-4.35-4.35" />
                </svg>
            ),
            plus: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="16" />
                    <line x1="8" y1="12" x2="16" y2="12" />
                </svg>
            ),
            settings: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
            ),
            admin: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
            ),
        };
        return icons[name] || null;
    };

    return (
        <>
            {/* Mobile overlay */}
            <div
                className={`sidebar-overlay ${isOpen ? 'visible' : ''}`}
                onClick={onClose}
            />

            <aside className={`app-sidebar ${isOpen ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <Link to="/" className="sidebar-logo" onClick={onClose}>
                        <div className="sidebar-logo-icon">🏏</div>
                        <span className="sidebar-logo-text">SPL Auction</span>
                    </Link>
                </div>

                <nav className="sidebar-nav">
                    {navLinks.map((section) => (
                        <div key={section.section} className="nav-section">
                            <div className="nav-section-title">{section.section}</div>
                            {section.links.map((link) => (
                                <NavLink
                                    key={link.to}
                                    to={link.to}
                                    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                                    onClick={onClose}
                                    end={link.to === '/'}
                                >
                                    <span className="nav-link-icon">{getIcon(link.icon)}</span>
                                    {link.label}
                                </NavLink>
                            ))}
                        </div>
                    ))}
                </nav>

                <div className="sidebar-footer">
                    <div className="nav-link" style={{ opacity: 0.5, fontSize: 'var(--text-xs)' }}>
                        Shroff Premier League v2.0
                    </div>
                </div>
            </aside>
        </>
    );
}

export default Sidebar;
