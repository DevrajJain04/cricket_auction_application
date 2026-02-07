/**
 * Create Auction Page
 */
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import auctionService from '../services/auctionService';

function CreateAuctionPage() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [formData, setFormData] = useState({
        name: '',
        description: '',
        auction_type: 'community',
        initial_purse: 100,
        min_bid_increment: 0.5,
        base_price_default: 1.0,
        max_team_size: 25,
    });

    const handleChange = (e) => {
        const { name, value, type } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: type === 'number' ? parseFloat(value) : value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const auction = await auctionService.createAuction(formData);
            navigate(`/auctions/${auction.id}`);
        } catch (err) {
            setError(err.message || 'Failed to create auction');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="animate-fadeIn">
            <div className="mb-6">
                <Link to="/auctions" className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>
                    ← Back to auctions
                </Link>
            </div>

            <div className="page-header">
                <div>
                    <h1 className="page-header-title">Create New Auction</h1>
                    <p className="text-secondary mt-2">Set up your cricket auction event</p>
                </div>
            </div>

            <div className="card card-elevated" style={{ maxWidth: '700px' }}>
                <div className="card-body">
                    {error && (
                        <div className="toast toast-error mb-4" style={{ position: 'relative', animation: 'none' }}>
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="name" className="form-label">Auction Name *</label>
                            <input
                                type="text"
                                id="name"
                                name="name"
                                className="form-input"
                                placeholder="e.g., SPL Season 3"
                                value={formData.name}
                                onChange={handleChange}
                                required
                                minLength={3}
                                maxLength={100}
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="description" className="form-label">Description</label>
                            <textarea
                                id="description"
                                name="description"
                                className="form-input"
                                placeholder="Describe your auction..."
                                value={formData.description}
                                onChange={handleChange}
                                rows={3}
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="auction_type" className="form-label">Auction Type</label>
                            <select
                                id="auction_type"
                                name="auction_type"
                                className="form-input"
                                value={formData.auction_type}
                                onChange={handleChange}
                            >
                                <option value="community">Community (Custom Players)</option>
                                <option value="ipl_tracker">IPL Tracker (Real Players)</option>
                            </select>
                            <p className="form-helper">
                                Community mode lets you add custom players. IPL Tracker uses real IPL player data.
                            </p>
                        </div>

                        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 'var(--space-4)' }}>
                            <div className="form-group">
                                <label htmlFor="initial_purse" className="form-label">Initial Purse (Cr)</label>
                                <input
                                    type="number"
                                    id="initial_purse"
                                    name="initial_purse"
                                    className="form-input"
                                    value={formData.initial_purse}
                                    onChange={handleChange}
                                    min={0}
                                    step={0.5}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="min_bid_increment" className="form-label">Min Bid Increment (Cr)</label>
                                <input
                                    type="number"
                                    id="min_bid_increment"
                                    name="min_bid_increment"
                                    className="form-input"
                                    value={formData.min_bid_increment}
                                    onChange={handleChange}
                                    min={0.01}
                                    step="any"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="base_price_default" className="form-label">Default Base Price (Cr)</label>
                                <input
                                    type="number"
                                    id="base_price_default"
                                    name="base_price_default"
                                    className="form-input"
                                    value={formData.base_price_default}
                                    onChange={handleChange}
                                    min={0}
                                    step={0.1}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="max_team_size" className="form-label">Max Team Size</label>
                                <input
                                    type="number"
                                    id="max_team_size"
                                    name="max_team_size"
                                    className="form-input"
                                    value={formData.max_team_size}
                                    onChange={handleChange}
                                    min={1}
                                    max={50}
                                />
                            </div>
                        </div>

                        <div className="flex gap-4 mt-6">
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <span className="spinner" style={{ width: 20, height: 20 }} />
                                        Creating...
                                    </>
                                ) : (
                                    'Create Auction'
                                )}
                            </button>
                            <Link to="/auctions" className="btn btn-secondary">
                                Cancel
                            </Link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}

export default CreateAuctionPage;
