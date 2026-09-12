import React, { useState, useRef, useEffect } from 'react';
import { 
  Bell, 
  Sparkles, 
  Sun, 
  LogOut, 
  UserCheck, 
  Menu, 
  LogIn,
  ChevronDown,
  ShieldCheck
} from 'lucide-react';
import { useAuth } from '../../context/useAuth';
import { useNavigate, Link } from 'react-router-dom';
import OfficerProfilePopover from './OfficerProfilePopover';
import NotificationPopover from './NotificationPopover';
import SystemStatusPopover from './SystemStatusPopover';
import SessionSecurityPopover from './SessionSecurityPopover';
import DateTimeDisplay from '../common/DateTimeDisplay';

export function Topbar({ onMenuToggle }) {
  const { officer, isAuthenticated, logout, theme, setTheme } = useAuth();
  const navigate = useNavigate();
  
  const [showNotifications, setShowNotifications] = useState(false);
  const [showOfficerPopover, setShowOfficerPopover] = useState(false);
  const [showStatusPopover, setShowStatusPopover] = useState(false);
  const [showSecurityPopover, setShowSecurityPopover] = useState(false);
  
  const notificationRef = useRef(null);
  const officerRef = useRef(null);
  const statusRef = useRef(null);
  const securityRef = useRef(null);

  const handleLogout = () => {
    setShowOfficerPopover(false);
    setShowSecurityPopover(false);
    logout();
    navigate('/dashboard');
  };

  // Close popovers on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
      if (officerRef.current && !officerRef.current.contains(event.target)) {
        setShowOfficerPopover(false);
      }
      if (statusRef.current && !statusRef.current.contains(event.target)) {
        setShowStatusPopover(false);
      }
      if (securityRef.current && !securityRef.current.contains(event.target)) {
        setShowSecurityPopover(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-[var(--cyber-header-bg)] backdrop-blur-xl border-b border-[var(--cyber-border)] px-4 sm:px-6 lg:px-8 py-3 transition-colors duration-300">
      <div className="flex items-center justify-between gap-4">
        
        {/* Left Section: Mobile Menu Button + Branding */}
        <div className="flex items-center gap-3">
          {onMenuToggle && (
            <button
              type="button"
              onClick={onMenuToggle}
              className="lg:hidden p-2 rounded-xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] text-[var(--cyber-accent)] hover:border-[var(--cyber-border-hover)] transition-colors cursor-pointer"
              aria-label="Toggle navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}

          <Link to="/dashboard" className="flex items-center gap-3 group">
            <div className="relative flex items-center justify-center">
              <div 
                className="absolute -inset-1 rounded-xl blur-md opacity-70 group-hover:opacity-100 transition-all duration-300"
                style={{ background: 'var(--cyber-glow-subtle)' }}
              />
              <img
                src="/logo.png"
                alt="Cyber Sentinals"
                className="relative w-8 h-8 sm:w-9 sm:h-9 object-contain drop-shadow-[0_0_10px_var(--cyber-glow)]"
              />
            </div>
            <div>
              <div className="flex items-center gap-1.5 leading-none">
                <span className="text-base sm:text-lg font-black chrome-text font-corptic tracking-wider">
                  CYBER
                </span>
                <span className="text-base sm:text-lg font-black font-corptic tracking-wider neon-accent-text">
                  SENTINELS
                </span>
              </div>
              <span className="text-[10px] text-[var(--cyber-accent)] font-mono tracking-wider block mt-0.5">
                CYBERGUARD LEA PORTAL
              </span>
            </div>
          </Link>
        </div>

        {/* Right Section: System Status + Notifications + DateTime + Theme + Security + Officer Info */}
        <div className="flex items-center gap-2 sm:gap-3 lg:gap-4">
          
          {/* System Status: Clickable SYSTEM READY trigger */}
          <div className="relative" ref={statusRef}>
            <button
              type="button"
              onClick={() => {
                setShowStatusPopover((prev) => !prev);
                setShowNotifications(false);
                setShowOfficerPopover(false);
                setShowSecurityPopover(false);
              }}
              className={`hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--cyber-bg-card)] border text-xs font-mono transition-all duration-200 cursor-pointer ${
                showStatusPopover
                  ? 'border-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.3)]'
                  : 'border-[var(--cyber-border)] hover:border-emerald-400/50 hover:bg-[var(--cyber-bg-secondary)]'
              }`}
              title="View System Readiness Status"
              aria-expanded={showStatusPopover}
              aria-haspopup="dialog"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-emerald-400 font-bold tracking-wider text-[11px]">
                SYSTEM READY
              </span>
            </button>

            {/* System Status Popover */}
            {showStatusPopover && (
              <SystemStatusPopover onClose={() => setShowStatusPopover(false)} />
            )}
          </div>

          {/* Notifications Popover Trigger */}
          <div className="relative" ref={notificationRef}>
            <button
              type="button"
              onClick={() => {
                setShowNotifications((prev) => !prev);
                setShowOfficerPopover(false);
                setShowStatusPopover(false);
                setShowSecurityPopover(false);
              }}
              className={`p-2 rounded-xl bg-[var(--cyber-bg-card)] border transition-all duration-200 relative cursor-pointer ${
                showNotifications
                  ? 'border-[var(--cyber-accent)] text-[var(--cyber-accent)] shadow-[0_0_12px_var(--cyber-glow-subtle)]'
                  : 'border-[var(--cyber-border)] text-[var(--cyber-text-secondary)] hover:text-[var(--cyber-accent)] hover:border-[var(--cyber-border-hover)]'
              }`}
              title="Notifications"
              aria-label="View notifications"
              aria-expanded={showNotifications}
              aria-haspopup="dialog"
            >
              <Bell className="w-4 h-4" />
            </button>

            {showNotifications && (
              <NotificationPopover onClose={() => setShowNotifications(false)} />
            )}
          </div>

          {/* Current Date & Time Display */}
          <DateTimeDisplay />

          {/* DUAL THEME TOGGLE */}
          <div className="flex items-center rounded-xl p-0.5 bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] shadow-sm">
            <button
              type="button"
              onClick={() => setTheme('cyber-blue')}
              className={`p-1.5 sm:px-2.5 sm:py-1 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 cursor-pointer ${
                theme === 'cyber-blue'
                  ? 'bg-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-sm font-bold'
                  : 'text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)]'
              }`}
              title="Cyber Cyan Theme (Dark)"
              aria-label="Switch to Cyber Cyan Theme"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span className="hidden sm:inline font-mono text-[10px] uppercase">Cyan</span>
            </button>

            <button
              type="button"
              onClick={() => setTheme('quantum-light')}
              className={`p-1.5 sm:px-2.5 sm:py-1 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 cursor-pointer ${
                theme === 'quantum-light'
                  ? 'bg-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-sm font-bold'
                  : 'text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)]'
              }`}
              title="Quantum Light Theme (Light)"
              aria-label="Switch to Quantum Light Theme"
            >
              <Sun className="w-3.5 h-3.5" />
              <span className="hidden sm:inline font-mono text-[10px] uppercase">Light</span>
            </button>
          </div>

          {/* Authenticated Officer ID + Session Security + Logout OR Unauthenticated Login Button */}
          {isAuthenticated && officer ? (
            <div className="flex items-center gap-2 sm:gap-2.5 pl-2 border-l border-[var(--cyber-border)]">
              
              {/* Session Security Indicator Button */}
              <div className="relative hidden lg:block" ref={securityRef}>
                <button
                  type="button"
                  onClick={() => {
                    setShowSecurityPopover((prev) => !prev);
                    setShowOfficerPopover(false);
                    setShowNotifications(false);
                    setShowStatusPopover(false);
                  }}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-[var(--cyber-bg-card)] border text-[11px] font-mono transition-all duration-200 cursor-pointer ${
                    showSecurityPopover
                      ? 'border-emerald-400 text-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.25)]'
                      : 'border-[var(--cyber-border)] text-[var(--cyber-text-secondary)] hover:border-emerald-400/40 hover:text-emerald-400'
                  }`}
                  title="View Session Security Status"
                  aria-expanded={showSecurityPopover}
                  aria-haspopup="dialog"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="font-bold text-[10px] uppercase tracking-wider">SESSION SECURE</span>
                </button>

                {/* Session Security Popover */}
                {showSecurityPopover && (
                  <SessionSecurityPopover onClose={() => setShowSecurityPopover(false)} />
                )}
              </div>

              {/* Officer ID Clickable Button */}
              <div className="relative" ref={officerRef}>
                <button
                  type="button"
                  onClick={() => {
                    setShowOfficerPopover((prev) => !prev);
                    setShowNotifications(false);
                    setShowStatusPopover(false);
                    setShowSecurityPopover(false);
                  }}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[var(--cyber-bg-card)] border transition-all duration-200 cursor-pointer group text-left ${
                    showOfficerPopover
                      ? 'border-[var(--cyber-accent)] shadow-[0_0_15px_var(--cyber-glow-subtle)]'
                      : 'border-[var(--cyber-border)] hover:border-[var(--cyber-border-hover)] hover:bg-[var(--cyber-bg-secondary)]'
                  }`}
                  aria-expanded={showOfficerPopover}
                  aria-haspopup="dialog"
                  title="View Officer Profile"
                >
                  <div className="p-1 rounded-lg bg-[var(--cyber-border)] text-[var(--cyber-accent)] group-hover:scale-105 transition-transform">
                    <UserCheck className="w-3.5 h-3.5" />
                  </div>
                  <div className="text-left">
                    <span className="text-[9px] font-mono tracking-widest text-[var(--cyber-text-muted)] block uppercase leading-none">
                      OFFICER ID
                    </span>
                    <span className="text-xs font-bold font-mono text-[var(--cyber-accent)] leading-tight block mt-0.5">
                      {officer.officerId}
                    </span>
                  </div>
                  <ChevronDown className={`w-3.5 h-3.5 text-[var(--cyber-text-muted)] group-hover:text-[var(--cyber-accent)] transition-transform duration-200 ${showOfficerPopover ? 'rotate-180 text-[var(--cyber-accent)]' : ''}`} />
                </button>

                {/* Officer Profile Popover */}
                {showOfficerPopover && (
                  <OfficerProfilePopover
                    officer={officer}
                    onClose={() => setShowOfficerPopover(false)}
                    onLogout={handleLogout}
                  />
                )}
              </div>

              {/* Quick Logout Button */}
              <button
                type="button"
                onClick={handleLogout}
                className="p-2 rounded-xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] text-[var(--cyber-text-secondary)] hover:text-rose-400 hover:border-rose-500/40 transition-all duration-200 group cursor-pointer"
                title="Log out"
                aria-label="Logout"
              >
                <LogOut className="w-4 h-4 group-hover:scale-110 transition-transform" />
              </button>
            </div>
          ) : (
            <div className="pl-2 border-l border-[var(--cyber-border)]">
              <Link
                to="/login"
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-[var(--cyber-accent)] text-[#030714] font-bold text-xs font-mono tracking-wider uppercase hover:opacity-90 active:scale-95 transition-all shadow-[0_0_12px_var(--cyber-glow-subtle)]"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Officer Login</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Topbar;
