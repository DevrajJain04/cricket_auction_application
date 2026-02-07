/**
 * Main Application Entry
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import AuctionsListPage from './pages/AuctionsListPage';
import CreateAuctionPage from './pages/CreateAuctionPage';
import AuctionDetailPage from './pages/AuctionDetailPage';
import LiveAuctionPage from './pages/LiveAuctionPage';
import PlayersPage from './pages/PlayersPage';
import MyTeamsPage from './pages/MyTeamsPage';
import SettingsPage from './pages/SettingsPage';
import AdminPage from './pages/AdminPage';

// Styles
import './styles/index.css';
import './styles/components.css';
import './styles/pages.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected Routes */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/auctions" element={<AuctionsListPage />} />
            <Route path="/auctions/new" element={<CreateAuctionPage />} />
            <Route path="/auctions/:auctionId" element={<AuctionDetailPage />} />
            <Route path="/auctions/:auctionId/live" element={<LiveAuctionPage />} />
            <Route path="/players" element={<PlayersPage />} />
            <Route path="/my-teams" element={<MyTeamsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
