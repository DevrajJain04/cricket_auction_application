/**
 * Authentication Context
 * Provides auth state and functions throughout the app
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Initialize auth state from localStorage
    useEffect(() => {
        const storedUser = authService.getStoredUser();
        if (storedUser) {
            setUser(storedUser);
        }
        setLoading(false);
    }, []);

    const login = useCallback(async (email, password) => {
        setError(null);
        try {
            const userData = await authService.login(email, password);
            setUser(userData);
            return userData;
        } catch (err) {
            const message = err.message || 'Login failed';
            setError(message);
            throw new Error(message);
        }
    }, []);

    const register = useCallback(async (email, password, displayName) => {
        setError(null);
        try {
            const userData = await authService.register(email, password, displayName);
            return userData;
        } catch (err) {
            const message = err.message || 'Registration failed';
            setError(message);
            throw new Error(message);
        }
    }, []);

    const logout = useCallback(() => {
        authService.logout();
        setUser(null);
    }, []);

    const refreshUser = useCallback(async () => {
        try {
            const userData = await authService.getCurrentUser();
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));
            return userData;
        } catch (err) {
            logout();
            throw err;
        }
    }, [logout]);

    const value = {
        user,
        loading,
        error,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        isManager: user?.role === 'admin' || user?.role === 'auction_manager',
        login,
        register,
        logout,
        refreshUser,
        clearError: () => setError(null),
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export default AuthContext;
