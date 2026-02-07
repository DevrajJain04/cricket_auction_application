/**
 * Player Service
 */
import api from './api';

export const playerService = {
    /**
     * Search players by name with fuzzy matching
     */
    async searchPlayers(query, limit = 20) {
        const response = await api.get('/players/search', {
            params: { q: query, limit },
        });
        return response.data;
    },

    /**
     * Get player by ID
     */
    async getPlayer(playerId) {
        const response = await api.get(`/players/${playerId}`);
        return response.data;
    },

    /**
     * Add alias for a player (admin only)
     */
    async addPlayerAlias(playerId, alias) {
        const response = await api.post(`/players/${playerId}/alias`, null, {
            params: { alias },
        });
        return response.data;
    },
};

export default playerService;
