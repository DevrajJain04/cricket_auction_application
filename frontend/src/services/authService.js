/**
 * Authentication Service
 */
import api from './api';

export const authService = {
    /**
     * Login with email and password
     */
    async login(email, password) {
        // Use JSON login endpoint (easier for frontend)
        const response = await api.post('/auth/login/json', {
            email,
            password,
        });

        const { access_token } = response.data;
        localStorage.setItem('token', access_token);

        // Get user info
        const userResponse = await api.get('/auth/me');
        localStorage.setItem('user', JSON.stringify(userResponse.data));

        return userResponse.data;
    },

    /**
     * Register a new user
     */
    async register(email, password, displayName) {
        const response = await api.post('/auth/register', {
            email,
            password,
            display_name: displayName,
        });

        return response.data;
    },

    /**
     * Get current authenticated user
     */
    async getCurrentUser() {
        const response = await api.get('/auth/me');
        return response.data;
    },

    /**
     * Logout - clear stored data
     */
    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    },

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!localStorage.getItem('token');
    },

    /**
     * Get stored user data
     */
    getStoredUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },
};

export default authService;
