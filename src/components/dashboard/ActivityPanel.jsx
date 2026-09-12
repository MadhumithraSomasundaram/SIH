import React from 'react';
import { History, Clock } from 'lucide-react';
import EmptyState from './EmptyState';

export function ActivityPanel({ activities = [] }) {
  return (
    <div className="cyber-panel p-6 sm:p-7 rounded-2xl relative space-y-5">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-[var(--cyber-border)]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--cyber-text-primary)] font-corptic tracking-wider">
              RECENT ACTIVITY
            </h3>
            <p className="text-xs text-[var(--cyber-text-muted)] font-mono">
              SYSTEM & DISPATCH AUDIT LOG
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-text-muted)]">
            LOGS: {activities.length}
          </span>
        </div>
      </div>

      {/* Content / Empty State */}
      {activities.length === 0 ? (
        <EmptyState
          icon={Clock}
          title="No recent activity"
          description="System activity will appear here when events are recorded."
          badge="AUDIT LOG EMPTY"
        />
      ) : (
        <div className="space-y-3">
          {/* Will render activities in later phases */}
        </div>
      )}
    </div>
  );
}

export default ActivityPanel;
