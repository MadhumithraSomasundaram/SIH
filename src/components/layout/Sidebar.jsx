import React from 'react';
import { NavLink, useNavigate, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  ShieldAlert,
  MapPin,
  Briefcase,
  FileCheck2,
  Users,
  Cpu,
  FileSpreadsheet,
  ScrollText,
  Settings,
  LogOut,
  LogIn,
  X,
  Shield
} from 'lucide-react';
import { useAuth } from '../../context/useAuth';

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Alerts', path: '/alerts', icon: ShieldAlert },
  { name: 'Risk Map', path: '/risk-map', icon: MapPin },
  { name: 'Cases', path: '/cases', icon: Briefcase },
  { name: 'Evidence', path: '/evidence', icon: FileCheck2 },
  { name: 'Teams', path: '/teams', icon: Users },
  { name: 'Intelligence', path: '/intelligence', icon: Cpu },
  { name: 'Reports', path: '/reports', icon: FileSpreadsheet },
  { name: 'Audit Logs', path: '/audit-logs', icon: ScrollText },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export function Sidebar({ isOpen, onClose }) {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/dashboard');
    if (onClose) onClose();
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-50 w-64 bg-[var(--cyber-bg-secondary)] border-r border-[var(--cyber-border)] flex flex-col justify-between transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Top Header / Mobile Close */}
        <div className="p-4 border-b border-[var(--cyber-border)] flex items-center justify-between lg:hidden">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-[var(--cyber-accent)]" />
            <span className="font-corptic font-bold text-sm tracking-wider text-[var(--cyber-text-primary)]">
              NAVIGATION
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)] bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)]"
            aria-label="Close sidebar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation Items List */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5 custom-scrollbar">
          <div className="px-3 py-1.5 text-[10px] font-mono font-bold tracking-widest text-[var(--cyber-text-muted)] uppercase">
            OPERATIONAL MODULES
          </div>

          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => {
                  if (onClose) onClose();
                }}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all duration-200 group ${
                    isActive
                      ? 'bg-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-[0_0_15px_var(--cyber-glow-subtle)] border border-[var(--cyber-accent)]/30 font-bold'
                      : 'text-[var(--cyber-text-secondary)] hover:text-[var(--cyber-text-primary)] hover:bg-[var(--cyber-bg-card)]'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={`w-4 h-4 transition-transform group-hover:scale-110 ${
                        isActive ? 'text-[var(--cyber-accent)]' : 'text-[var(--cyber-text-muted)]'
                      }`}
                    />
                    <span>{item.name}</span>
                    {isActive && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--cyber-accent)] shadow-[0_0_6px_var(--cyber-accent)]" />
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Bottom Sidebar Action: Logout when authenticated / Officer Login when unauthenticated */}
        <div className="p-3 border-t border-[var(--cyber-border)] bg-[var(--cyber-bg-card)]/50">
          {isAuthenticated ? (
            <button
              type="button"
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-[var(--cyber-text-secondary)] hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/30 transition-all duration-200 group"
            >
              <LogOut className="w-4 h-4 text-rose-400 group-hover:scale-110 transition-transform" />
              <span>Logout</span>
            </button>
          ) : (
            <Link
              to="/login"
              onClick={() => {
                if (onClose) onClose();
              }}
              className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-[var(--cyber-text-primary)] hover:text-[var(--cyber-accent)] bg-[var(--cyber-bg-card)] hover:bg-[var(--cyber-border)] border border-[var(--cyber-border)] transition-all duration-200 group"
            >
              <LogIn className="w-4 h-4 text-[var(--cyber-accent)] group-hover:scale-110 transition-transform" />
              <span>Officer Login</span>
            </Link>
          )}
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
