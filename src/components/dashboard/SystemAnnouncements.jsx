import React from 'react';
import { Megaphone, Radio } from 'lucide-react';
import EmptyState from './EmptyState';

export function SystemAnnouncements({ announcements = [] }) {
  return (
    <div className="cyber-panel p-6 sm:p-7 rounded-2xl relative space-y-5">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-[var(--cyber-border)]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/30">
            <Megaphone className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--cyber-text-primary)] font-corptic tracking-wider">
              SYSTEM ANNOUNCEMENTS
            </h3>
            <p className="text-xs text-[var(--cyber-text-muted)] font-mono">
              COMMAND DIRECTIVES & ADVISORY BROADCASTS
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-text-muted)]">
            BROADCASTS: {announcements.length}
          </span>
        </div>
      </div>

      {/* Content / Empty State */}
      {announcements.length === 0 ? (
        <EmptyState
          icon={Radio}
          title="No system announcements"
          description="Administrative announcements will appear here."
          badge="BROADCAST CHANNEL CLEAR"
        />
      ) : (
        <div className="space-y-3">
          {/* Announcements will appear here in future phases */}
        </div>
      )}
    </div>
  );
}

export default SystemAnnouncements;
