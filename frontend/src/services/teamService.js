/**
 * Team Service
 */
import api from './api';

export const teamService = {
    /**
     * List teams in an auction
     */
    async listTeams(auctionId) {
        const response = await api.get(`/auctions/${auctionId}/teams`);
        return response.data;
    },

    /**
     * Get team details
     */
    async getTeam(auctionId, teamId) {
        const response = await api.get(`/auctions/${auctionId}/teams/${teamId}`);
        return response.data;
    },

    /**
     * Create a team
     */
    async createTeam(auctionId, data) {
        const response = await api.post(`/auctions/${auctionId}/teams`, data);
        return response.data;
    },

    /**
     * Update team details
     */
    async updateTeam(auctionId, teamId, data) {
        const response = await api.put(`/auctions/${auctionId}/teams/${teamId}`, data);
        return response.data;
    },

    /**
     * Delete a team
     */
    async deleteTeam(auctionId, teamId) {
        const response = await api.delete(`/auctions/${auctionId}/teams/${teamId}`);
        return response.data;
    },

    /**
     * Set captain or vice-captain
     */
    async setCaptain(auctionId, teamId, playerId, isVice = false) {
        const response = await api.post(
            `/auctions/${auctionId}/teams/${teamId}/players/${playerId}/captain`,
            null,
            { params: { is_vice: isVice } }
        );
        return response.data;
    },
};

export default teamService;
