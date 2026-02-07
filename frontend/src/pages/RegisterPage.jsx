/**
 * Register Page
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function RegisterPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        // Validation
        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        setLoading(true);

        try {
            await register(email, password, displayName);
            setSuccess(true);
            // Redirect to login after short delay
            setTimeout(() => navigate('/login'), 2000);
        } catch (err) {
            setError(err.message || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="auth-layout">
                <div className="auth-hero">
                    <div className="auth-hero-content">
                        <h1 className="auth-hero-title">Shroff Premier League</h1>
                        <p className="auth-hero-subtitle">
                            The ultimate cricket auction experience.<br />
                            Build your dream team.
                        </p>
                    </div>
                </div>

                <div className="auth-content">
                    <div className="auth-form-container text-center">
                        <div style={{ fontSize: '4rem', marginBottom: 'var(--space-4)' }}>🎉</div>
                        <h2 className="auth-title">Account Created!</h2>
                        <p className="auth-subtitle">
                            Your account has been created successfully. Redirecting to login...
                        </p>
                        <div className="loader">
                            <div className="spinner" />
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="auth-layout">
            {/* Hero Section */}
            <div className="auth-hero">
                <div className="auth-hero-content">
                    <h1 className="auth-hero-title">Shroff Premier League</h1>
                    <p className="auth-hero-subtitle">
                        The ultimate cricket auction experience.<br />
                        Build your dream team.
                    </p>
                </div>
            </div>

            {/* Register Form */}
            <div className="auth-content">
                <div className="auth-form-container">
                    <div className="auth-logo">
                        <div className="auth-logo-icon">🏏</div>
                        <span className="auth-logo-text">SPL Auction</span>
                    </div>

                    <h2 className="auth-title">Create an account</h2>
                    <p className="auth-subtitle">Join the auction and build your team</p>

                    {error && (
                        <div className="toast toast-error mb-4" style={{ position: 'relative', animation: 'none' }}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="15" y1="9" x2="9" y2="15" />
                                <line x1="9" y1="9" x2="15" y2="15" />
                            </svg>
                            {error}
                        </div>
                    )}

                    <form className="auth-form" onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="displayName" className="form-label">Display Name</label>
                            <input
                                type="text"
                                id="displayName"
                                className="form-input"
                                placeholder="John Doe"
                                value={displayName}
                                onChange={(e) => setDisplayName(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="email" className="form-label">Email</label>
                            <input
                                type="email"
                                id="email"
                                className="form-input"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                autoComplete="email"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="password" className="form-label">Password</label>
                            <input
                                type="password"
                                id="password"
                                className="form-input"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={6}
                            />
                            <p className="form-helper">At least 6 characters</p>
                        </div>

                        <div className="form-group">
                            <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
                            <input
                                type="password"
                                id="confirmPassword"
                                className="form-input"
                                placeholder="••••••••"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary btn-lg"
                            style={{ width: '100%' }}
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner" style={{ width: 20, height: 20 }} />
                                    Creating account...
                                </>
                            ) : (
                                'Create account'
                            )}
                        </button>
                    </form>

                    <p className="auth-footer">
                        Already have an account? <Link to="/login">Sign in</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

export default RegisterPage;
