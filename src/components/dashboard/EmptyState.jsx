import React from 'react';
import { Inbox } from 'lucide-react';

export function EmptyState({ 
  icon: Icon = Inbox, 
  title = "No data available", 
  description = "Information will appear here once received.",
  badge = "AWAITING TELEMETRY"
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center rounded-xl bg-[var(--cyber-bg-secondary)]/40 border border-dashed border-[var(--cyber-border)]">
      <div className="p-4 rounded-2xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-[0_0_15px_var(--cyber-glow-subtle)] mb-4">
        <Icon className="w-8 h-8 opacity-80" />
      </div>

      <span className="text-[10px] font-mono font-bold tracking-widest text-[var(--cyber-accent)] uppercase px-2.5 py-0.5 rounded-full bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] mb-2">
        {badge}
      </span>

      <h4 className="text-base font-bold text-[var(--cyber-text-primary)] tracking-wide mb-1 font-sans">
        {title}
      </h4>

      <p className="text-xs text-[var(--cyber-text-secondary)] max-w-sm leading-relaxed">
        {description}
      </p>
    </div>
  );
}

export default EmptyState;
