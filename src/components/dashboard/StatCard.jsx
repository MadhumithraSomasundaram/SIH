import React from 'react';

export function StatCard({ title, value = 0, icon: Icon, tag, accentColor = 'var(--cyber-accent)', accentBorder = 'border-[var(--cyber-border)]' }) {
  return (
    <div className="cyber-panel p-6 rounded-2xl relative group overflow-hidden transition-all duration-300">
      {/* Top ambient highlight line */}
      <div 
        className="absolute top-0 left-0 w-full h-[2px] opacity-60 transition-opacity group-hover:opacity-100"
        style={{ background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)` }}
      />

      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono font-bold tracking-widest uppercase text-[var(--cyber-text-muted)]">
              {tag}
            </span>
          </div>
          <div className="text-xs sm:text-sm font-semibold text-[var(--cyber-text-secondary)] tracking-wide">
            {title}
          </div>
          <div className="text-3xl sm:text-4xl font-black font-corptic tracking-wider text-[var(--cyber-text-primary)]">
            {value}
          </div>
        </div>

        {Icon && (
          <div 
            className={`p-3 rounded-xl bg-[var(--cyber-bg-secondary)] ${accentBorder} border shadow-sm shrink-0`}
            style={{ color: accentColor }}
          >
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-[var(--cyber-border)] flex items-center justify-between text-[11px] text-[var(--cyber-text-muted)] font-mono">
        <span>STATUS // STANDBY</span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
          ACTIVE 0
        </span>
      </div>
    </div>
  );
}

export default StatCard;
