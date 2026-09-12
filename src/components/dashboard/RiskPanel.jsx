import React from 'react';
import { Radar, Activity } from 'lucide-react';
import EmptyState from './EmptyState';

export function RiskPanel({ data = [] }) {
  return (
    <div className="cyber-panel p-6 sm:p-7 rounded-2xl relative space-y-5">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-[var(--cyber-border)]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[var(--cyber-border)] text-[var(--cyber-accent)] border border-[var(--cyber-border)]">
            <Radar className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--cyber-text-primary)] font-corptic tracking-wider">
              RISK INTELLIGENCE
            </h3>
            <p className="text-xs text-[var(--cyber-text-muted)] font-mono">
              PREDICTIVE GEOGRAPHIC THREAT METRICS
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-text-muted)]">
            ZONES MONITORED: 0
          </span>
        </div>
      </div>

      {/* Content / Empty State */}
      {data.length === 0 ? (
        <EmptyState
          icon={Activity}
          title="No risk intelligence available"
          description="Risk information will appear when the prediction engine provides results."
          badge="MODEL IDLE"
        />
      ) : (
        <div className="space-y-3">
          {/* Will render risk data in later phases */}
        </div>
      )}
    </div>
  );
}

export default RiskPanel;
