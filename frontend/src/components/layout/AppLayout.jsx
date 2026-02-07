/**
 * App Layout Component
 * Main layout wrapper for authenticated pages
 */
import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

function AppLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="app-layout">
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

            <main className="app-main">
                <Header
                    onMenuClick={() => setSidebarOpen(true)}
                />

                <div className="app-content">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}

export default AppLayout;
