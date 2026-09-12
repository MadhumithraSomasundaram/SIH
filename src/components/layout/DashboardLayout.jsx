import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Topbar from './Topbar';
import Sidebar from './Sidebar';

export function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[var(--cyber-bg)] text-[var(--cyber-text-secondary)] font-sans transition-colors duration-300 relative flex flex-col">
      {/* Ambient Top Glow Orbs (matching existing design) */}
      <div 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] rounded-full blur-[140px] pointer-events-none transition-all duration-700 opacity-30 z-0"
        style={{ background: 'var(--cyber-accent)' }}
      />
      <div 
        className="fixed top-[25%] left-[-150px] w-[450px] h-[450px] rounded-full blur-[160px] pointer-events-none transition-all duration-700 opacity-15 z-0"
        style={{ background: 'var(--cyber-accent-secondary)' }}
      />

      {/* Main Topbar */}
      <Topbar onMenuToggle={() => setSidebarOpen((prev) => !prev)} />

      {/* Layout Body: Sidebar + Dynamic Main Content */}
      <div className="flex-1 flex overflow-hidden relative z-10">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 custom-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
