import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, 
  MapPin, 
  Briefcase, 
  Users, 
  Zap, 
  ArrowUpRight 
} from 'lucide-react';

const ACTIONS = [
  {
    label: 'VIEW ALERTS',
    path: '/alerts',
    icon: ShieldAlert,
    tag: 'OP // 01',
    accent: 'var(--cyber-accent)',
    borderColor: 'hover:border-[var(--cyber-accent)]'
  },
  {
    label: 'RISK MAP',
    path: '/risk-map',
    icon: MapPin,
    tag: 'OP // 02',
    accent: '#00F0FF',
    borderColor: 'hover:border-cyan-400'
  },
  {
    label: 'ACTIVE CASES',
    path: '/cases',
    icon: Briefcase,
    tag: 'OP // 03',
    accent: '#0284C7',
    borderColor: 'hover:border-sky-400'
  },
  {
    label: 'TEAMS',
    path: '/teams',
    icon: Users,
    tag: 'OP // 04',
    accent: '#10B981',
    borderColor: 'hover:border-emerald-400'
  }
];

export function QuickActions() {
  const navigate = useNavigate();

  return (
    <div className="cyber-panel p-6 sm:p-7 rounded-2xl relative space-y-5">
      {/* Section Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[var(--cyber-border)]">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-[var(--cyber-border)] text-[var(--cyber-accent)] border border-[var(--cyber-border)]">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-black font-corptic tracking-wider text-[var(--cyber-text-primary)]">
              QUICK ACTIONS
            </h3>
            <p className="text-[11px] font-mono text-[var(--cyber-text-muted)]">
              DIRECT DISPATCH & OPERATIONAL SHORTCUTS
            </p>
          </div>
        </div>

        <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded-lg bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-text-muted)]">
          4 SHORTCUTS
        </span>
      </div>

      {/* 4 Action Buttons Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.path}
              type="button"
              onClick={() => navigate(action.path)}
              className={`cyber-panel p-4 rounded-xl border border-[var(--cyber-border)] ${action.borderColor} hover:bg-[var(--cyber-bg-secondary)] transition-all duration-200 group text-left cursor-pointer flex flex-col justify-between h-28`}
            >
              <div className="flex items-start justify-between w-full">
                <div 
                  className="p-2 rounded-lg bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-accent)] group-hover:scale-110 transition-transform"
                  style={{ color: action.accent }}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex items-center gap-1 text-[10px] font-mono text-[var(--cyber-text-muted)] group-hover:text-[var(--cyber-accent)] transition-colors">
                  <span>{action.tag}</span>
                  <ArrowUpRight className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </div>
              </div>

              <div>
                <span className="text-xs font-bold font-mono tracking-wider text-[var(--cyber-text-primary)] group-hover:text-[var(--cyber-accent)] transition-colors block">
                  {action.label}
                </span>
                <span className="text-[10px] text-[var(--cyber-text-muted)] block mt-0.5">
                  Launch Module
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default QuickActions;
