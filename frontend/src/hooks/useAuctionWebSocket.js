/**
 * WebSocket hook for live auction functionality
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { API_BASE_URL } from '../services/api';

export function useAuctionWebSocket(auctionId, token) {
    const [connected, setConnected] = useState(false);
    const [auctionState, setAuctionState] = useState(null);
    const [bidHistory, setBidHistory] = useState([]);
    const [error, setError] = useState(null);
    const [userRole, setUserRole] = useState(null);
    const [teamId, setTeamId] = useState(null);

    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);

    const connect = useCallback(() => {
        if (!auctionId || !token) return;

        // Build WebSocket URL
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
        const wsUrl = `${wsProtocol}//${wsHost}/auctions/${auctionId}/ws?token=${token}`;

        try {
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('WebSocket connected');
                setConnected(true);
                setError(null);
                reconnectAttemptsRef.current = 0;
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    handleMessage(message);
                } catch (err) {
                    console.error('Failed to parse WebSocket message:', err);
                }
            };

            ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                setConnected(false);
                wsRef.current = null;

                // Attempt reconnection unless closed intentionally
                if (event.code !== 1000 && reconnectAttemptsRef.current < 5) {
                    reconnectAttemptsRef.current += 1;
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
                    reconnectTimeoutRef.current = setTimeout(connect, delay);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                setError('Connection error');
            };
        } catch (err) {
            console.error('Failed to create WebSocket:', err);
            setError('Failed to connect');
        }
    }, [auctionId, token]);

    const handleMessage = (message) => {
        switch (message.type) {
            case 'connected':
                setUserRole(message.role);
                setTeamId(message.team_id);
                break;

            case 'state:update':
                setAuctionState(message.data);
                break;

            case 'bid:new':
                // Update bid history
                setBidHistory((prev) => [
                    {
                        id: Date.now(),
                        teamId: message.team_id,
                        teamName: message.team_name,
                        amount: message.amount,
                        playerName: message.player_name,
                        timestamp: new Date(),
                    },
                    ...prev.slice(0, 49), // Keep last 50 bids
                ]);
                break;

            case 'player:sold':
                // Could trigger a celebration animation
                console.log('Player sold:', message);
                break;

            case 'error':
                setError(message.message);
                // Clear error after 5 seconds
                setTimeout(() => setError(null), 5000);
                break;

            default:
                console.log('Unknown message type:', message.type);
        }
    };

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close(1000, 'User disconnected');
            wsRef.current = null;
        }
        setConnected(false);
    }, []);

    const sendMessage = useCallback((message) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        } else {
            console.error('WebSocket not connected');
        }
    }, []);

    // Action helpers
    const placeBid = useCallback((amount) => {
        if (!teamId) {
            setError('No team assigned');
            return;
        }
        sendMessage({
            type: 'bid:place',
            team_id: teamId,
            amount,
        });
    }, [sendMessage, teamId]);

    const presentPlayer = useCallback((auctionPlayerId) => {
        sendMessage({
            type: 'player:present',
            auction_player_id: auctionPlayerId,
        });
    }, [sendMessage]);

    const sellPlayer = useCallback((auctionPlayerId) => {
        sendMessage({
            type: 'player:sell',
            auction_player_id: auctionPlayerId,
        });
    }, [sendMessage]);

    const markUnsold = useCallback((auctionPlayerId) => {
        sendMessage({
            type: 'player:unsold',
            auction_player_id: auctionPlayerId,
        });
    }, [sendMessage]);

    // Connect on mount
    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        connected,
        auctionState,
        bidHistory,
        error,
        userRole,
        teamId,
        placeBid,
        presentPlayer,
        sellPlayer,
        markUnsold,
        reconnect: connect,
    };
}

export default useAuctionWebSocket;
