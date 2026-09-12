import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Terminal } from 'lucide-react';

const ROUTE_NAME_MAP = {
  '/dashboard': 'COMMAND DASHBOARD',
  '/alerts': 'ALERTS',
  '/risk-map': 'RISK MAP',
  '/cases': 'CASES',
  '/evidence': 'EVIDENCE',
  '/teams': 'TEAMS',
  '/intelligence': 'INTELLIGENCE',
  '/reports': 'REPORTS',
  '/audit-logs': 'AUDIT LOGS',
  '/settings': 'SETTINGS',
};

export function Breadcrumb({ customCurrent }) {
  const location = useLocation();
  const currentPath = location.pathname;
  const pageName = customCurrent || ROUTE_NAME_MAP[currentPath] || 'COMMAND DASHBOARD';

  return (
    <nav 
      aria-label="Breadcrumb"
      className="inline-flex items-center gap-2 text-[11px] font-mono tracking-wider text-[var(--cyber-text-muted)] py-1"
    >
      <Link 
        to="/dashboard"
        className="hover:text-[var(--cyber-accent)] transition-colors flex items-center gap-1 uppercase font-bold"
      >
        <Terminal className="w-3.5 h-3.5 text-[var(--cyber-accent)]" />
        <span>LEA PORTAL</span>
      </Link>
      
      <ChevronRight className="w-3 h-3 text-[var(--cyber-border-hover)]" />

      <span className="text-[var(--cyber-text-primary)] font-bold uppercase">
        {pageName}
      </span>
    </nav>
  );
}

export default Breadcrumb;
