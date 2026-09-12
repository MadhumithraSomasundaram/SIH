import React, { useEffect, useRef } from 'react';
import { Activity, X } from 'lucide-react';

const STATUS_ITEMS = [
  { name: 'Authentication', status: 'READY', ready: true },
  { name: 'Dashboard', status: 'READY', ready: true },
  { name: 'Intelligence', status: 'WAITING', ready: false },
  { name: 'GIS Service', status: 'WAITING', ready: false },
];

export function SystemStatusPopover({ onClose }) {
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
      className="absolute left-0 sm:left-auto sm:right-0 top-full mt-2 w-72 sm:w-80 rounded-2xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] shadow-2xl backdrop-blur-2xl p-4 z-50 animate-in fade-in zoom-in-95 duration-200 text-left"
      role="dialog"
      aria-label="System Readiness Status"
    >
      {/* Popover Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[var(--cyber-border)]">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-black font-corptic tracking-wider text-[var(--cyber-text-primary)]">
            SYSTEM STATUS
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)] p-1 rounded-lg cursor-pointer transition-colors"
          aria-label="Close status popover"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Status Items List */}
      <div className="py-3 space-y-2 text-xs font-mono">
        {STATUS_ITEMS.map((item) => (
          <div 
            key={item.name} 
            className="flex items-center justify-between py-1.5 px-2.5 rounded-xl bg-[var(--cyber-bg-secondary)]/50 border border-[var(--cyber-border)]"
          >
            <div className="flex items-center gap-2">
              <span 
                className={`w-2 h-2 rounded-full ${
                  item.ready 
                    ? 'bg-emerald-400 shadow-[0_0_8px_#34d399] animate-pulse' 
                    : 'bg-amber-400/80'
                }`} 
              />
              <span className="text-[var(--cyber-text-secondary)] font-medium">
                {item.name}
              </span>
            </div>

            <span 
              className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                item.ready 
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' 
                  : 'bg-amber-500/10 text-amber-400/90 border border-amber-500/30'
              }`}
            >
              {item.status}
            </span>
          </div>
        ))}
      </div>

      {/* Footer Info Note */}
      <div className="pt-2 border-t border-[var(--cyber-border)] text-center">
        <span className="text-[10px] font-mono text-[var(--cyber-text-muted)]">
          TELEMETRY // CENTRAL NODE READY
        </span>
      </div>
    </div>
  );
}

export default SystemStatusPopover;
