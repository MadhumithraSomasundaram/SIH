import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Briefcase, 
  AlertTriangle, 
  Users,
  Activity
} from 'lucide-react';
import { dashboardService } from '../services/dashboardService';
import Breadcrumb from '../components/common/Breadcrumb';
import StatCard from '../components/dashboard/StatCard';
import AlertPanel from '../components/dashboard/AlertPanel';
import RiskPanel from '../components/dashboard/RiskPanel';
import ActivityPanel from '../components/dashboard/ActivityPanel';
import SystemAnnouncements from '../components/dashboard/SystemAnnouncements';
import QuickActions from '../components/dashboard/QuickActions';

export function Dashboard() {
  const [data, setData] = useState({
    stats: {
      totalAlerts: 0,
      activeCases: 0,
      highRiskZones: 0,
      activeTeams: 0
    },
    activeAlerts: [],
    riskIntelligence: [],
    recentActivity: [],
    announcements: [],
    notifications: []
  });

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const res = await dashboardService.getDashboardData();
        if (isMounted) {
          setData(res);
        }
      } catch (e) {
        console.error('Failed to load dashboard data:', e);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      
      {/* Top Breadcrumb Navigation */}
      <div>
        <Breadcrumb />
      </div>

      {/* Dashboard Header Section with Operational Mode Badge */}
      <div className="space-y-2 border-b border-[var(--cyber-border)] pb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="w-2 h-2 rounded-full bg-[var(--cyber-accent)] animate-ping" />
              <span className="text-[11px] font-mono font-bold tracking-widest text-[var(--cyber-accent)] uppercase">
                OPERATIONAL TELEMETRY // ACTIVE
              </span>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black font-corptic tracking-wider text-[var(--cyber-text-primary)]">
              COMMAND DASHBOARD
            </h1>
            <p className="text-sm sm:text-base text-[var(--cyber-text-secondary)] font-sans mt-1">
              Law Enforcement Cyber Intelligence & Response Center
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Operational Mode Indicator */}
            <div className="px-3.5 py-1.5 rounded-xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] text-xs font-mono text-[var(--cyber-text-secondary)] flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">
                OPERATIONAL
              </span>
            </div>

            <div className="hidden sm:flex px-3.5 py-1.5 rounded-xl bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] text-xs font-mono text-[var(--cyber-text-muted)] items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-[var(--cyber-accent)]" />
              <span>STATION: CENTRAL NODE</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4 Statistics Cards (Total Alerts, Active Cases, High Risk Zones, Active Teams) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Total Alerts"
          value={data.stats.totalAlerts}
          icon={ShieldAlert}
          tag="[ STAT // 01 ]"
          accentColor="var(--cyber-accent)"
          accentBorder="border-[var(--cyber-border)]"
        />

        <StatCard
          title="Active Cases"
          value={data.stats.activeCases}
          icon={Briefcase}
          tag="[ STAT // 02 ]"
          accentColor="#0284C7"
          accentBorder="border-sky-500/30"
        />

        <StatCard
          title="High Risk Zones"
          value={data.stats.highRiskZones}
          icon={AlertTriangle}
          tag="[ STAT // 03 ]"
          accentColor="#F43F5E"
          accentBorder="border-rose-500/30"
        />

        <StatCard
          title="Active Teams"
          value={data.stats.activeTeams}
          icon={Users}
          tag="[ STAT // 04 ]"
          accentColor="#10B981"
          accentBorder="border-emerald-500/30"
        />
      </div>

      {/* Main Grid: Active Alerts & Risk Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AlertPanel alerts={data.activeAlerts} />
        <RiskPanel data={data.riskIntelligence} />
      </div>

      {/* Recent Activity Panel */}
      <div className="w-full">
        <ActivityPanel activities={data.recentActivity} />
      </div>

      {/* System Announcements Panel */}
      <div className="w-full">
        <SystemAnnouncements announcements={data.announcements} />
      </div>

      {/* Quick Actions Shortcuts Section */}
      <div className="w-full">
        <QuickActions />
      </div>
    </div>
  );
}

export default Dashboard;
