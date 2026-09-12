import React, { useEffect, useRef } from 'react';
import { 
  UserCheck, 
  LogOut, 
  X, 
  Shield, 
  Clock
} from 'lucide-react';

function formatLastLogin(timestamp) {
  if (!timestamp) return 'Not available';
  try {
    const d = new Date(timestamp);
    if (isNaN(d.getTime())) return 'Not available';
    return d.toLocaleString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  } catch {
    return 'Not available';
  }
}

export function OfficerProfilePopover({ officer, onClose, onLogout }) {
  const popoverRef = useRef(null);

  // Close on Escape key press
  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        onClose();
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!officer) return null;

  const lastLoginText = formatLastLogin(officer.loggedInAt);

  return (
    <div
      ref={popoverRef}
      className="absolute right-0 top-full mt-2 w-80 sm:w-84 rounded-2xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] shadow-2xl backdrop-blur-2xl p-5 z-50 animate-in fade-in zoom-in-95 duration-200 text-left"
      role="dialog"
      aria-label="Officer Profile Details"
    >
      {/* Popover Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[var(--cyber-border)]">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-[var(--cyber-accent)]" />
          <span className="text-xs font-black font-corptic tracking-wider text-[var(--cyber-text-primary)]">
            OFFICER PROFILE
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded-lg text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)] hover:bg-[var(--cyber-bg-secondary)] transition-colors cursor-pointer"
          aria-label="Close profile details"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Avatar & Officer Identifier */}
      <div className="py-3.5 flex items-center gap-3.5">
        <div className="relative">
          <div 
            className="absolute -inset-1 rounded-2xl blur-md opacity-60"
            style={{ background: 'var(--cyber-accent)' }}
          />
          <div className="relative p-2.5 rounded-2xl bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-md">
            <UserCheck className="w-5 h-5" />
          </div>
        </div>

        <div className="space-y-0.5">
          <div className="text-base font-bold font-mono text-[var(--cyber-accent)] tracking-wider">
            {officer.officerId}
          </div>
          <div className="text-[11px] text-[var(--cyber-text-secondary)] font-sans">
            Authorized Officer
          </div>
        </div>
      </div>

      {/* Details List (Only render available fields) */}
      <div className="py-3 border-t border-[var(--cyber-border)] space-y-2.5 text-xs font-mono">
        {/* Officer ID */}
        {officer.officerId && (
          <div className="flex items-center justify-between">
            <span className="text-[var(--cyber-text-muted)] text-[11px]">Officer ID</span>
            <span className="font-bold text-[var(--cyber-text-primary)]">{officer.officerId}</span>
          </div>
        )}

        {/* Role */}
        {officer.role && (
          <div className="flex items-center justify-between">
            <span className="text-[var(--cyber-text-muted)] text-[11px]">Role</span>
            <span className="font-medium text-[var(--cyber-text-secondary)]">{officer.role}</span>
          </div>
        )}

        {/* Account Status */}
        {officer.status && (
          <div className="flex items-center justify-between">
            <span className="text-[var(--cyber-text-muted)] text-[11px]">Status</span>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {officer.status}
            </span>
          </div>
        )}

        {/* Access Level */}
        {officer.accessLevel && (
          <div className="flex items-center justify-between">
            <span className="text-[var(--cyber-text-muted)] text-[11px]">Access</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-accent)]">
              {officer.accessLevel}
            </span>
          </div>
        )}
      </div>

      {/* Last Login Info Section */}
      <div className="py-3 border-t border-[var(--cyber-border)] flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-1.5 text-[var(--cyber-text-muted)] text-[11px]">
          <Clock className="w-3.5 h-3.5" />
          <span>Last Login</span>
        </div>
        <span className="text-[11px] font-medium text-[var(--cyber-text-secondary)]">
          {lastLoginText}
        </span>
      </div>

      {/* Logout Action Button */}
      <div className="pt-3 border-t border-[var(--cyber-border)]">
        <button
          type="button"
          onClick={onLogout}
          className="w-full py-2.5 px-4 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 border border-rose-500/30 hover:border-rose-500/50 text-xs font-mono font-bold tracking-widest uppercase transition-all flex items-center justify-center gap-2 group cursor-pointer shadow-sm"
        >
          <LogOut className="w-4 h-4 group-hover:scale-110 transition-transform" />
          <span>LOGOUT</span>
        </button>
      </div>
    </div>
  );
}

export default OfficerProfilePopover;
