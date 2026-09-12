import React from 'react';
import { AlertCircle, ShieldAlert } from 'lucide-react';
import EmptyState from './EmptyState';

export function AlertPanel({ alerts = [] }) {
  return (
    <div className="cyber-panel p-6 sm:p-7 rounded-2xl relative space-y-5">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-[var(--cyber-border)]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--cyber-text-primary)] font-corptic tracking-wider">
              ACTIVE ALERTS
            </h3>
            <p className="text-xs text-[var(--cyber-text-muted)] font-mono">
              REAL-TIME THREAT DETECTION QUEUE
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-text-muted)]">
            COUNT: {alerts.length}
          </span>
        </div>
      </div>

      {/* Content / Empty State */}
      {alerts.length === 0 ? (
        <EmptyState
          icon={AlertCircle}
          title="No active alerts"
          description="Alerts received from the intelligence system will appear here."
          badge="ALERT STREAM CLEAR"
        />
      ) : (
        <div className="space-y-3">
          {/* Will render active alerts in later phases */}
        </div>
      )}
    </div>
  );
}

export default AlertPanel;
