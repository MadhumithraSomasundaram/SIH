import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Construction, 
  ArrowLeft, 
  Shield, 
  ShieldAlert, 
  MapPin, 
  Briefcase, 
  FileCheck2, 
  Users, 
  Cpu, 
  FileSpreadsheet, 
  ScrollText, 
  Settings 
} from 'lucide-react';
import Breadcrumb from '../components/common/Breadcrumb';

const MODULE_MAP = {
  '/alerts': { name: 'Alerts', icon: ShieldAlert, desc: 'Real-time alert dispatch, filtering, and triage management.' },
  '/risk-map': { name: 'Risk Map', icon: MapPin, desc: 'GIS spatial risk scoring and geographic threat overlay.' },
  '/cases': { name: 'Cases', icon: Briefcase, desc: 'Investigation case filing, assignment, and status workflows.' },
  '/evidence': { name: 'Evidence', icon: FileCheck2, desc: 'Digital forensics chain of custody and evidence repository.' },
  '/teams': { name: 'Teams', icon: Users, desc: 'Field unit roster, dispatch control, and active unit tracking.' },
  '/intelligence': { name: 'Intelligence', icon: Cpu, desc: 'Predictive threat models and pattern recognition analytics.' },
  '/reports': { name: 'Reports', icon: FileSpreadsheet, desc: 'Automated executive summaries and forensic exports.' },
  '/audit-logs': { name: 'Audit Logs', icon: ScrollText, desc: 'Cryptographically verified immutable system access logs.' },
  '/settings': { name: 'Settings', icon: Settings, desc: 'Platform configuration, node telemetry, and security policies.' }
};

export function ModulePlaceholder({ title, icon: CustomIcon, description }) {
  const location = useLocation();
  const matched = MODULE_MAP[location.pathname] || {};

  const moduleName = title || matched.name || 'Module';
  const Icon = CustomIcon || matched.icon || Construction;
  const moduleDesc = description || matched.desc || 'This operational module is scheduled for future deployment.';

  return (
    <div className="max-w-4xl mx-auto py-6 sm:py-8 space-y-6">
      {/* Top Breadcrumb Navigation */}
      <div>
        <Breadcrumb customCurrent={moduleName.toUpperCase()} />
      </div>

      {/* Back to Dashboard Navigation Link */}
      <div>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] text-[var(--cyber-text-secondary)] hover:text-[var(--cyber-accent)] hover:border-[var(--cyber-border-hover)] transition-all group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
          <span>Back to Dashboard</span>
        </Link>
      </div>

      {/* Main Placeholder Cyber Card */}
      <div className="cyber-panel p-8 sm:p-12 rounded-3xl relative overflow-hidden text-center space-y-6">
        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-[var(--cyber-accent)] to-transparent opacity-70" />

        {/* Module Icon */}
        <div className="flex justify-center">
          <div className="relative">
            <div 
              className="absolute -inset-3 rounded-2xl blur-lg opacity-40"
              style={{ background: 'var(--cyber-accent)' }}
            />
            <div className="relative p-5 rounded-2xl bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-xl">
              <Icon className="w-10 h-10" />
            </div>
          </div>
        </div>

        {/* Title & Badge */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[10px] font-mono font-bold tracking-widest text-[var(--cyber-accent)] uppercase">
            <Shield className="w-3 h-3" />
            <span>PHASE 2 DEPLOYMENT</span>
          </div>

          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black font-corptic tracking-wider text-[var(--cyber-text-primary)]">
            {moduleName}
          </h2>

          <p className="text-base sm:text-lg font-bold text-[var(--cyber-accent)] font-sans">
            Module under development
          </p>

          <p className="text-xs sm:text-sm text-[var(--cyber-text-secondary)] max-w-md mx-auto leading-relaxed">
            This module will be activated in a future development phase. {moduleDesc}
          </p>
        </div>

        {/* Actions */}
        <div className="pt-4 flex justify-center">
          <Link
            to="/dashboard"
            className="py-3 px-6 rounded-xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] hover:border-[var(--cyber-accent)] text-[var(--cyber-text-primary)] hover:text-[var(--cyber-accent)] font-bold text-xs font-mono tracking-widest uppercase transition-all shadow-sm flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default ModulePlaceholder;
