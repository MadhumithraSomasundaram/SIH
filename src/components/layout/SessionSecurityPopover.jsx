import React, { useEffect, useRef } from 'react';
import { ShieldCheck, X } from 'lucide-react';

export function SessionSecurityPopover({ onClose }) {
  const popoverRef = useRef(null);

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        onClose();
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      ref={popoverRef}
      className="absolute right-0 top-full mt-2 w-72 sm:w-80 rounded-2xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] shadow-2xl backdrop-blur-2xl p-4 z-50 animate-in fade-in zoom-in-95 duration-200 text-left"
      role="dialog"
      aria-label="Session Security Status"
    >
      {/* Popover Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[var(--cyber-border)]">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-black font-corptic tracking-wider text-[var(--cyber-text-primary)]">
            SESSION SECURITY
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)] p-1 rounded-lg cursor-pointer transition-colors"
          aria-label="Close security popover"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Security Items List */}
      <div className="py-3 space-y-2.5 text-xs font-mono">
        <div className="flex items-center justify-between py-1 px-2 rounded-lg bg-[var(--cyber-bg-secondary)]/50 border border-[var(--cyber-border)]">
          <span className="text-[var(--cyber-text-muted)] text-[11px]">Session</span>
          <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            ACTIVE
          </span>
        </div>

        <div className="flex items-center justify-between py-1 px-2 rounded-lg bg-[var(--cyber-bg-secondary)]/50 border border-[var(--cyber-border)]">
          <span className="text-[var(--cyber-text-muted)] text-[11px]">Authentication</span>
          <span className="text-[10px] font-bold text-[var(--cyber-accent)]">
            VERIFIED
          </span>
        </div>

        <div className="flex items-center justify-between py-1 px-2 rounded-lg bg-[var(--cyber-bg-secondary)]/50 border border-[var(--cyber-border)]">
          <span className="text-[var(--cyber-text-muted)] text-[11px]">Connection</span>
          <span className="text-[10px] font-bold text-emerald-400">
            SECURE
          </span>
        </div>
      </div>

      {/* Info Note */}
      <div className="pt-2 border-t border-[var(--cyber-border)] text-center">
        <span className="text-[10px] font-mono text-[var(--cyber-text-muted)]">
          SESSION ID // VERIFIED LEA TOKEN
        </span>
      </div>
    </div>
  );
}

export default SessionSecurityPopover;
