/**
 * Auction Service
 */
import api from './api';

export const auctionService = {
    /**
     * List all accessible auctions
     */
    async listAuctions() {
        const response = await api.get('/auctions');
        return response.data;
    },

    /**
     * Get auction by ID
     */
    async getAuction(auctionId) {
        const response = await api.get(`/auctions/${auctionId}`);
        return response.data;
    },

    /**
     * Create a new auction
     */
    async createAuction(data) {
        const response = await api.post('/auctions', data);
        return response.data;
    },

    /**
     * Update auction settings
     */
    async updateAuction(auctionId, data) {
        const response = await api.put(`/auctions/${auctionId}`, data);
        return response.data;
    },

    /**
     * Start an auction
     */
    async startAuction(auctionId) {
        const response = await api.post(`/auctions/${auctionId}/start`);
        return response.data;
    },

    /**
     * Pause an auction
     */
    async pauseAuction(auctionId) {
        const response = await api.post(`/auctions/${auctionId}/pause`);
        return response.data;
    },

    /**
     * Complete an auction
     */
    async completeAuction(auctionId) {
        const response = await api.post(`/auctions/${auctionId}/complete`);
        return response.data;
    },

    /**
     * Get player pool for an auction
     */
    async getPlayerPool(auctionId, statusFilter = null) {
        const params = statusFilter ? { status_filter: statusFilter } : {};
        const response = await api.get(`/auctions/${auctionId}/players`, { params });
        return response.data;
    },

    /**
     * Add player to auction pool
     */
    async addPlayerToPool(auctionId, playerData) {
        const response = await api.post(`/auctions/${auctionId}/players`, playerData);
        return response.data;
    },

    /**
     * Authorize a user for the auction
     */
    async authorizeUser(auctionId, userId) {
        const response = await api.post(`/auctions/${auctionId}/authorize`, {
            user_id: userId,
        });
        return response.data;
    },
};

export default auctionService;
