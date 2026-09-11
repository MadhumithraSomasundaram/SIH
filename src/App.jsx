import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  ShieldCheck,
  Lock,
  Cpu,
  Globe,
  Key,
  AlertTriangle,
  Flame,
  Activity,
  CheckCircle2,
  Database,
  Wifi,
  Terminal,
  Cloud,
  Smartphone,
  Palette,
  Sparkles,
  Moon,
  Sun,
  ChevronDown,
  Check
} from 'lucide-react';

const THEMES = [
  {
    id: 'cyber-blue',
    name: 'Cyber Cyan',
    label: 'Cyber Cyan',
    icon: Sparkles,
    accent: '#00F0FF',
    desc: 'Electric Circuit & Deep Space Void (Logo Signature)',
    tag: 'Dark'
  },
  {
    id: 'quantum-light',
    name: 'Quantum Light',
    label: 'Quantum Light',
    icon: Sun,
    accent: '#0284C7',
    desc: 'High-Tech Arctic Protocol (Light Mode)',
    tag: 'Light'
  }
];

export function App() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('cyber-sentinals-theme');
    return saved === 'quantum-light' ? 'quantum-light' : 'cyber-blue';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('cyber-sentinals-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'cyber-blue' ? 'quantum-light' : 'cyber-blue'));
  };

  return (
    <div className="min-h-screen bg-[var(--cyber-bg)] text-[var(--cyber-text-secondary)] font-sans transition-colors duration-300 relative overflow-hidden">
      {/* Ambient Top Glow Orbs */}
      <div 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] rounded-full blur-[140px] pointer-events-none transition-all duration-700 opacity-40 z-0"
        style={{ background: 'var(--cyber-accent)' }}
      />
      <div 
        className="fixed top-[20%] left-[-150px] w-[450px] h-[450px] rounded-full blur-[160px] pointer-events-none transition-all duration-700 opacity-20 z-0"
        style={{ background: 'var(--cyber-accent-secondary)' }}
      />

      {/* Top Header / Navigation Bar */}
      <header className="sticky top-0 z-50 bg-[var(--cyber-header-bg)] backdrop-blur-xl border-b border-[var(--cyber-border)] px-4 sm:px-8 lg:px-12 py-3.5 transition-colors duration-300">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          
          {/* Logo Brand */}
          <a href="#" className="flex items-center gap-3.5 group">
            <div className="relative flex items-center justify-center">
              <div 
                className="absolute -inset-1.5 rounded-2xl blur-md opacity-70 group-hover:opacity-100 transition-all duration-300"
                style={{ background: 'var(--cyber-glow-subtle)' }}
              />
              <img
                src="/logo.png"
                alt="Cyber Sentinals Logo"
                className="relative w-11 h-11 sm:w-12 sm:h-12 object-contain drop-shadow-[0_0_12px_var(--cyber-glow)] transition-transform duration-300 group-hover:scale-105"
              />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xl sm:text-2xl font-black chrome-text font-corptic tracking-wider block leading-none">
                  CYBER
                </span>
                <span className="text-xl sm:text-2xl font-black font-corptic tracking-wider block leading-none neon-accent-text">
                  SENTINALS
                </span>
              </div>
              <p className="text-[11px] text-[var(--cyber-text-muted)] font-sans tracking-wide mt-0.5">
                Cybersecurity Intelligence & Defense Platform
              </p>
            </div>
          </a>

          {/* Navigation Links + Theme Switcher */}
          <div className="flex flex-wrap items-center justify-between md:justify-end gap-3 sm:gap-6 text-sm">
            <nav className="flex flex-wrap items-center gap-4 sm:gap-6 text-xs sm:text-sm font-medium">
              <a href="#about" className="text-[var(--cyber-text-secondary)] hover:text-[var(--cyber-accent)] transition-colors">
                About
              </a>
              <a href="#cia-triad" className="text-[var(--cyber-text-secondary)] hover:text-[var(--cyber-accent)] transition-colors">
                CIA Triad
              </a>
              <a href="#threats" className="text-[var(--cyber-text-secondary)] hover:text-[var(--cyber-accent)] transition-colors">
                Threat Vectors
              </a>
              <a href="#defense" className="text-[var(--cyber-text-secondary)] hover:text-[var(--cyber-accent)] transition-colors">
                Defense Pillars
              </a>
              <a href="#best-practices" className="text-[var(--cyber-text-secondary)] hover:text-[var(--cyber-accent)] transition-colors">
                Best Practices
              </a>
            </nav>

            {/* DUAL THEME TOGGLE: Cyber Cyan & Quantum Light */}
            <div className="flex items-center rounded-xl p-1 bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] shadow-sm backdrop-blur-md">
              <button
                type="button"
                onClick={() => setTheme('cyber-blue')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                  theme === 'cyber-blue'
                    ? 'bg-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-sm font-bold'
                    : 'text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)]'
                }`}
                title="Cyber Cyan Theme (Signature Dark)"
                aria-pressed={theme === 'cyber-blue'}
              >
                <span 
                  className={`w-2 h-2 rounded-full ${theme === 'cyber-blue' ? 'bg-[#00F0FF] shadow-[0_0_8px_#00F0FF] animate-pulse' : 'bg-slate-500'}`}
                />
                <Sparkles className="w-3.5 h-3.5" />
                <span className="font-mono text-[11px] tracking-wider uppercase">
                  Cyber Cyan
                </span>
              </button>

              <button
                type="button"
                onClick={() => setTheme('quantum-light')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                  theme === 'quantum-light'
                    ? 'bg-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-sm font-bold'
                    : 'text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)]'
                }`}
                title="Quantum Light Theme (Light Mode)"
                aria-pressed={theme === 'quantum-light'}
              >
                <span 
                  className={`w-2 h-2 rounded-full ${theme === 'quantum-light' ? 'bg-[#0284C7] shadow-[0_0_8px_#0284C7] animate-pulse' : 'bg-slate-400'}`}
                />
                <Sun className="w-3.5 h-3.5" />
                <span className="font-mono text-[11px] tracking-wider uppercase">
                  Quantum Light
                </span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-8 lg:px-12 py-12 space-y-24 relative z-10">
        
        {/* HERO SECTION */}
        <section id="about" className="space-y-8 text-center max-w-4xl mx-auto pt-4 relative">
          
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] text-[var(--cyber-accent)] text-xs font-semibold shadow-sm backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-[var(--cyber-accent)] animate-ping" />
            <ShieldCheck className="w-4 h-4 text-[var(--cyber-accent)]" />
            <span className="tracking-wide">Cybersecurity Intelligence & Defense Infrastructure</span>
          </div>

          {/* Hero Logo Showcase (Directly matching user logo) */}
          <div className="flex justify-center pt-2 pb-2">
            <div className="relative group">
              <div 
                className="absolute -inset-6 rounded-full blur-3xl opacity-60 group-hover:opacity-80 transition-all duration-700 pointer-events-none"
                style={{ background: 'radial-gradient(circle, var(--cyber-glow) 0%, transparent 70%)' }}
              />
              <img
                src="/logo.png"
                alt="Cyber Sentinals Emblem"
                className="relative w-40 h-40 sm:w-52 sm:h-52 object-contain cyber-logo-float mx-auto transition-transform duration-500"
              />
            </div>
          </div>

          {/* Big Cyber Glitch Title with Chrome + Neon */}
          <div className="space-y-4">
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black font-corptic tracking-widest leading-none flex flex-wrap items-center justify-center gap-x-4 gap-y-2">
              <span className="chrome-text">CYBER</span>
              <span className="neon-accent-text">SENTINALS</span>
            </h1>
            <p className="text-lg sm:text-2xl font-bold text-[var(--cyber-accent)] font-sans tracking-wide">
              Defending the Modern Digital Ecosystem
            </p>
          </div>

          <p className="text-base sm:text-lg text-[var(--cyber-text-secondary)] leading-relaxed max-w-3xl mx-auto font-sans">
            Cybersecurity is the discipline and practice of protecting systems, networks, programs, devices, and sensitive data from digital attacks, unauthorized access, disruption, and destruction.
          </p>

          {/* Key Facts Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 text-left pt-6">
            <div className="cyber-panel p-6 rounded-2xl relative group overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-[var(--cyber-accent)] to-transparent opacity-60" />
              <div className="text-xs font-bold text-[var(--cyber-accent)] uppercase tracking-wider font-mono">
                [ 01 // SCOPE ]
              </div>
              <div className="text-xl font-bold text-[var(--cyber-text-primary)] mt-1">Global Scope</div>
              <p className="text-xs text-[var(--cyber-text-secondary)] leading-relaxed mt-2">
                Protecting critical infrastructure, financial institutions, healthcare data, and personal privacy across borders.
              </p>
            </div>

            <div className="cyber-panel p-6 rounded-2xl relative group overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-rose-500 to-transparent opacity-60" />
              <div className="text-xs font-bold text-rose-400 uppercase tracking-wider font-mono">
                [ 02 // THREATS ]
              </div>
              <div className="text-xl font-bold text-[var(--cyber-text-primary)] mt-1">Constant Evolution</div>
              <p className="text-xs text-[var(--cyber-text-secondary)] leading-relaxed mt-2">
                Adversaries continuously develop new exploitation techniques, AI automation, and evasive polymorphic payloads.
              </p>
            </div>

            <div className="cyber-panel p-6 rounded-2xl relative group overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-emerald-500 to-transparent opacity-60" />
              <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono">
                [ 03 // DEFENSE ]
              </div>
              <div className="text-xl font-bold text-[var(--cyber-text-primary)] mt-1">Defense in Depth</div>
              <p className="text-xs text-[var(--cyber-text-secondary)] leading-relaxed mt-2">
                Employing people, processes, and state-of-the-art telemetry across every layer of the digital infrastructure.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 1: THE CORE FOUNDATION - THE CIA TRIAD */}
        <section id="cia-triad" className="space-y-10 pt-10 border-t border-[var(--cyber-border)]">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <div className="text-xs font-mono font-bold tracking-widest text-[var(--cyber-accent)] uppercase">
              // FOUNDATIONAL ARCHITECTURE
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-[var(--cyber-text-primary)] font-corptic tracking-wider">
              The Core Foundation: The CIA Triad
            </h2>
            <p className="text-sm text-[var(--cyber-text-secondary)]">
              The CIA Triad is the foundational model guiding all information security policies, cryptographic primitives, and enterprise architectures.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Confidentiality */}
            <div className="cyber-panel p-7 rounded-2xl space-y-4 relative">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-[var(--cyber-border)] text-[var(--cyber-accent)] border border-[var(--cyber-border)] shadow-sm">
                <Lock className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-[var(--cyber-text-primary)] tracking-wide">
                Confidentiality
              </h3>
              <p className="text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Ensuring that sensitive information is accessible solely to authorized individuals, entities, and systems, preventing unauthorized disclosure.
              </p>
              <div className="space-y-2.5 text-xs text-[var(--cyber-text-secondary)] pt-4 border-t border-[var(--cyber-border)]">
                <div className="font-semibold text-[var(--cyber-text-primary)] font-mono text-[11px] uppercase tracking-wider">
                  Key Implementations:
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[var(--cyber-accent)] shrink-0" />
                  <span>Strong Data Encryption (AES-256)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[var(--cyber-accent)] shrink-0" />
                  <span>Multi-Factor Authentication (MFA)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[var(--cyber-accent)] shrink-0" />
                  <span>Role-Based Access Control (RBAC)</span>
                </div>
              </div>
            </div>

            {/* Integrity */}
            <div className="cyber-panel p-7 rounded-2xl space-y-4 relative">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-[var(--cyber-text-primary)] tracking-wide">
                Integrity
              </h3>
              <p className="text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Maintaining the accuracy, trustworthiness, and completeness of data over its entire lifecycle, ensuring it is not improperly altered or deleted.
              </p>
              <div className="space-y-2.5 text-xs text-[var(--cyber-text-secondary)] pt-4 border-t border-[var(--cyber-border)]">
                <div className="font-semibold text-[var(--cyber-text-primary)] font-mono text-[11px] uppercase tracking-wider">
                  Key Implementations:
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Cryptographic Hashes (SHA-256)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Digital Signatures & Certificates</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Immutable Audit Logging</span>
                </div>
              </div>
            </div>

            {/* Availability */}
            <div className="cyber-panel p-7 rounded-2xl space-y-4 relative">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/30 shadow-sm">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-[var(--cyber-text-primary)] tracking-wide">
                Availability
              </h3>
              <p className="text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Guaranteeing that systems, applications, and data are consistently accessible and operational for authorized users whenever needed.
              </p>
              <div className="space-y-2.5 text-xs text-[var(--cyber-text-secondary)] pt-4 border-t border-[var(--cyber-border)]">
                <div className="font-semibold text-[var(--cyber-text-primary)] font-mono text-[11px] uppercase tracking-wider">
                  Key Implementations:
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>Redundancy & Failover Systems</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>DDoS Mitigation & Rate Limiting</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>Disaster Recovery & Backup Archives</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 2: MAJOR CYBER THREAT VECTORS */}
        <section id="threats" className="space-y-10 pt-10 border-t border-[var(--cyber-border)]">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <div className="text-xs font-mono font-bold tracking-widest text-rose-400 uppercase">
              // THREAT INTELLIGENCE
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-[var(--cyber-text-primary)] font-corptic tracking-wider">
              Major Cyber Threat Vectors
            </h2>
            <p className="text-sm text-[var(--cyber-text-secondary)]">
              Understanding common attack mechanisms and persistent techniques used by threat syndicates worldwide.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Phishing */}
            <div className="cyber-panel p-6 rounded-2xl space-y-3 relative group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/30">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-[var(--cyber-text-primary)]">
                  Phishing & Social Engineering
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Deceptive communications (emails, SMS, fake portals) crafted to manipulate individuals into divulging sensitive credentials, financial details, or downloading malware.
              </p>
            </div>

            {/* Ransomware */}
            <div className="cyber-panel p-6 rounded-2xl space-y-3 relative group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/30">
                  <Flame className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-[var(--cyber-text-primary)]">
                  Malware & Ransomware
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Malicious software designed to infiltrate, damage, or take control of systems. Ransomware encrypts victim files and demands extortion payments for decryption keys.
              </p>
            </div>

            {/* DDoS */}
            <div className="cyber-panel p-6 rounded-2xl space-y-3 relative group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  <Activity className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-[var(--cyber-text-primary)]">
                  Distributed Denial of Service (DDoS)
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Overwhelming a targeted server, network, or service with massive waves of automated internet traffic from botnets, rendering it inaccessible to legitimate users.
              </p>
            </div>

            {/* SQL Injection */}
            <div className="cyber-panel p-6 rounded-2xl space-y-3 relative group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-[var(--cyber-border)] text-[var(--cyber-accent)] border border-[var(--cyber-border)]">
                  <Database className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-[var(--cyber-text-primary)]">
                  SQL Injection & Code Exploits
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Inserting malicious SQL commands into unprotected input fields to bypass authentication, extract complete database records, or modify server data.
              </p>
            </div>

            {/* Man in the Middle */}
            <div className="cyber-panel p-6 rounded-2xl space-y-3 relative group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                  <Wifi className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-[var(--cyber-text-primary)]">
                  Man-in-the-Middle (MitM)
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Eavesdropping on or intercepting communication sessions between two parties over insecure or rogue Wi-Fi networks to steal credentials and session tokens.
              </p>
            </div>

            {/* Zero Day */}
            <div className="cyber-panel p-6 rounded-2xl space-y-3 relative group">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/30">
                  <Cpu className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-[var(--cyber-text-primary)]">
                  Zero-Day Exploits
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Exploitation of previously unknown software or hardware security flaws before the developer or vendor has released a protective security patch.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 3: KEY PILLARS OF CYBER DEFENSE */}
        <section id="defense" className="space-y-10 pt-10 border-t border-[var(--cyber-border)]">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <div className="text-xs font-mono font-bold tracking-widest text-[var(--cyber-accent)] uppercase">
              // DEFENSE IN DEPTH
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-[var(--cyber-text-primary)] font-corptic tracking-wider">
              Pillars of Modern Cyber Defense
            </h2>
            <p className="text-sm text-[var(--cyber-text-secondary)]">
              A comprehensive multi-tiered security matrix safeguarding endpoints, perimeters, identities, and cloud infrastructures.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Network Security */}
            <div className="cyber-panel p-7 rounded-2xl space-y-3 relative">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-[var(--cyber-border)] text-[var(--cyber-accent)] border border-[var(--cyber-border)]">
                  <Globe className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-[var(--cyber-text-primary)]">Network Security</h3>
              </div>
              <p className="text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Securing network perimeters and internal topologies through Next-Generation Firewalls (NGFW), Intrusion Detection and Prevention Systems (IDS/IPS), micro-segmentation, and secure Zero-Trust Network Access (ZTNA).
              </p>
            </div>

            {/* Endpoint Security */}
            <div className="cyber-panel p-7 rounded-2xl space-y-3 relative">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  <Smartphone className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-[var(--cyber-text-primary)]">Endpoint Detection & Response (EDR)</h3>
              </div>
              <p className="text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Protecting individual user devices (workstations, mobile devices, servers) with continuous behavioral monitoring, automated threat isolation, and centralized forensic telemetry.
              </p>
            </div>

            {/* Identity & Access Management */}
            <div className="cyber-panel p-7 rounded-2xl space-y-3 relative">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                  <Key className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-[var(--cyber-text-primary)]">Identity & Access Management (IAM)</h3>
              </div>
              <p className="text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Enforcing the Principle of Least Privilege, robust passwordless or hardware-backed Multi-Factor Authentication (FIDO2/WebAuthn), and centralized single sign-on with adaptive risk scoring.
              </p>
            </div>

            {/* Cloud Security */}
            <div className="cyber-panel p-7 rounded-2xl space-y-3 relative">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/30">
                  <Cloud className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-[var(--cyber-text-primary)]">Cloud Infrastructure Security</h3>
              </div>
              <p className="text-sm text-[var(--cyber-text-secondary)] leading-relaxed">
                Securing cloud environments, serverless workloads, and containerized clusters through automated posture management (CSPM), immutable storage encryption, and CI/CD security scanning.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 4: ESSENTIAL BEST PRACTICES */}
        <section id="best-practices" className="space-y-10 pt-10 border-t border-[var(--cyber-border)]">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <div className="text-xs font-mono font-bold tracking-widest text-[var(--cyber-accent)] uppercase">
              // OPERATIONAL HYGIENE
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-[var(--cyber-text-primary)] font-corptic tracking-wider">
              Essential Cybersecurity Best Practices
            </h2>
            <p className="text-sm text-[var(--cyber-text-secondary)]">
              Crucial operational security measures for individuals and organizations to mitigate risk proactively.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <div className="cyber-panel p-6 rounded-2xl space-y-2 relative">
              <div className="text-[var(--cyber-accent)] font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Multi-Factor Authentication</span>
              </div>
              <p className="text-xs text-[var(--cyber-text-secondary)] leading-relaxed">
                Always enable 2FA/MFA across email, banking, cloud storage, and social accounts to block 99% of automated credential attacks.
              </p>
            </div>

            <div className="cyber-panel p-6 rounded-2xl space-y-2 relative">
              <div className="text-[var(--cyber-accent)] font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Prompt Patch Management</span>
              </div>
              <p className="text-xs text-[var(--cyber-text-secondary)] leading-relaxed">
                Consistently update operating systems, applications, routers, and firmware to remediate known software vulnerabilities.
              </p>
            </div>

            <div className="cyber-panel p-6 rounded-2xl space-y-2 relative">
              <div className="text-[var(--cyber-accent)] font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Immutable 3-2-1 Backups</span>
              </div>
              <p className="text-xs text-[var(--cyber-text-secondary)] leading-relaxed">
                Keep 3 copies of important data on 2 different media types, with 1 copy stored securely off-site or in air-gapped storage.
              </p>
            </div>

            <div className="cyber-panel p-6 rounded-2xl space-y-2 relative">
              <div className="text-[var(--cyber-accent)] font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Password Managers</span>
              </div>
              <p className="text-xs text-[var(--cyber-text-secondary)] leading-relaxed">
                Utilize reputable password managers to generate and store complex, unique, high-entropy passwords for each service.
              </p>
            </div>

            <div className="cyber-panel p-6 rounded-2xl space-y-2 relative">
              <div className="text-[var(--cyber-accent)] font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Phishing Vigilance</span>
              </div>
              <p className="text-xs text-[var(--cyber-text-secondary)] leading-relaxed">
                Inspect sender addresses, verify unexpected attachments, avoid clicking urgent links, and report suspicious messages.
              </p>
            </div>

            <div className="cyber-panel p-6 rounded-2xl space-y-2 relative">
              <div className="text-[var(--cyber-accent)] font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Zero Trust Architecture</span>
              </div>
              <p className="text-xs text-[var(--cyber-text-secondary)] leading-relaxed">
                Adopt the core security principle: &quot;Never trust, always verify&quot; for every request regardless of user location.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 5: THE FUTURE OF CYBERSECURITY */}
        <section className="cyber-panel p-8 sm:p-10 rounded-3xl space-y-4 text-center max-w-4xl mx-auto relative overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px] bg-gradient-to-r from-transparent via-[var(--cyber-accent)] to-transparent" />
          <h2 className="text-2xl sm:text-3xl font-black text-[var(--cyber-text-primary)] font-corptic tracking-wider">
            The Future of Cybersecurity: AI & Quantum Resistance
          </h2>
          <p className="text-sm text-[var(--cyber-text-secondary)] leading-relaxed max-w-2xl mx-auto">
            As computational power grows, cybersecurity is advancing towards predictive artificial intelligence for real-time anomaly detection, automated incident containment, and post-quantum cryptographic standards (NIST PQC) designed to withstand quantum computer decryption.
          </p>
        </section>
      </main>

      {/* Clean Cyber Footer */}
      <footer className="border-t border-[var(--cyber-border)] bg-[var(--cyber-footer-bg)] py-12 px-4 sm:px-8 lg:px-12 text-xs text-[var(--cyber-text-muted)] transition-colors duration-300 relative z-10">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <img
              src="/logo.png"
              alt="Cyber Sentinals"
              className="w-8 h-8 object-contain drop-shadow-[0_0_8px_var(--cyber-glow)]"
            />
            <div className="flex items-center gap-1.5 font-corptic tracking-wider font-bold">
              <span className="chrome-text text-sm">CYBER</span>
              <span className="neon-accent-text text-sm">SENTINALS</span>
            </div>
          </div>

          <div className="text-center sm:text-right text-[var(--cyber-text-muted)] font-sans">
            <p>© 2026 Cyber Sentinals. Informational & Educational Cybersecurity Resource.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

