import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

export function DateTimeDisplay() {
  const [timeState, setTimeState] = useState(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeState(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const dateStr = timeState.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }).toUpperCase();

  const timeStr = timeState.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });

  return (
    <div className="hidden xl:flex items-center gap-2 px-3 py-1 rounded-xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] text-xs font-mono text-[var(--cyber-text-secondary)] shadow-sm">
      <Clock className="w-3.5 h-3.5 text-[var(--cyber-accent)]" />
      <div className="flex items-center gap-1.5 leading-none text-[11px]">
        <span className="font-bold text-[var(--cyber-text-primary)]">{dateStr}</span>
        <span className="text-[var(--cyber-text-muted)]">//</span>
        <span className="text-[var(--cyber-accent)]">{timeStr}</span>
      </div>
    </div>
  );
}

export default DateTimeDisplay;
