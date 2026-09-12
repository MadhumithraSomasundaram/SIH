import React, { useEffect, useRef } from 'react';
import { Bell, X } from 'lucide-react';

export function NotificationPopover({ onClose }) {
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
      className="absolute right-0 top-full mt-2 w-80 sm:w-88 rounded-2xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] shadow-2xl backdrop-blur-2xl p-4 z-50 animate-in fade-in zoom-in-95 duration-200 text-left"
      role="dialog"
      aria-label="Notifications"
    >
      <div className="flex items-center justify-between pb-3 border-b border-[var(--cyber-border)]">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-[var(--cyber-accent)]" />
          <span className="text-xs font-black font-corptic tracking-wider text-[var(--cyber-text-primary)]">
            NOTIFICATIONS
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)] p-1 rounded-lg cursor-pointer transition-colors"
          aria-label="Close notifications"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="py-8 text-center space-y-3">
        <div className="inline-flex p-3 rounded-2xl bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-text-muted)] shadow-inner">
          <Bell className="w-6 h-6 text-[var(--cyber-accent)] opacity-80" />
        </div>
        <div>
          <p className="text-xs font-bold text-[var(--cyber-text-primary)] tracking-wide">
            No new notifications
          </p>
          <p className="text-[11px] text-[var(--cyber-text-muted)] mt-1 max-w-[240px] mx-auto">
            Alerts received from the intelligence system will appear here.
          </p>
        </div>
      </div>
    </div>
  );
}

export default NotificationPopover;
