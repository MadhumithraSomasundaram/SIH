import React from 'react';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Lock,
  Cpu,
  Globe,
  Server,
  FileCheck,
  Key,
  AlertTriangle,
  Flame,
  Activity,
  CheckCircle2,
  Layers,
  Database,
  Eye,
  Wifi,
  Terminal,
  Cloud,
  Smartphone
} from 'lucide-react';

export function App() {
  return (
    <div className="min-h-screen bg-[#0B1120] text-slate-200 font-sans">
      {/* Top Header / Navigation Bar */}
      <header className="sticky top-0 z-40 bg-[#0F172A]/95 backdrop-blur-md border-b border-slate-800 px-6 lg:px-12 py-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="flex items-center justify-center w-11 h-11 rounded-xl bg-sky-600 text-white shadow-md">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              {/* Big Glitch Brand Title */}
              <span className="text-2xl sm:text-3xl font-black text-white font-glitch glitch-title tracking-wider block">
                CYBER SENTINALS
              </span>
              <p className="text-xs text-slate-400 font-sans">
                Cybersecurity Intelligence & Defense Platform
              </p>
            </div>
          </div>

          <nav className="flex flex-wrap items-center gap-6 text-sm text-slate-300 font-sans">
            <a href="#about" className="hover:text-sky-400 transition-colors">
              About
            </a>
            <a href="#cia-triad" className="hover:text-sky-400 transition-colors">
              CIA Triad
            </a>
            <a href="#threats" className="hover:text-sky-400 transition-colors">
              Threat Vectors
            </a>
            <a href="#defense" className="hover:text-sky-400 transition-colors">
              Defense Pillars
            </a>
            <a href="#best-practices" className="hover:text-sky-400 transition-colors">
              Best Practices
            </a>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 lg:px-12 py-12 space-y-20">
        {/* HERO SECTION */}
        <section id="about" className="space-y-8 text-center max-w-4xl mx-auto pt-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-sky-950/80 border border-sky-800/60 text-sky-300 text-xs font-medium">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            <span>Cybersecurity Knowledge Base</span>
          </div>

          {/* Big Glitch Main Title */}
          <div className="space-y-3">
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black text-white font-glitch glitch-title tracking-widest leading-none">
              CYBER SENTINALS
            </h1>
            <p className="text-xl sm:text-2xl font-bold text-sky-400 font-sans">
              Defending the Modern Digital Ecosystem
            </p>
          </div>

          <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-3xl mx-auto font-sans">
            Cybersecurity is the discipline and practice of protecting systems, networks, programs, devices, and sensitive data from digital attacks, unauthorized access, disruption, and destruction.
          </p>

          {/* Key Facts Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left pt-6">
            <div className="p-5 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-1">
              <div className="text-xs font-semibold text-sky-400 uppercase tracking-wider">
                Critical Need
              </div>
              <div className="text-2xl font-bold text-white">Global Scope</div>
              <p className="text-xs text-slate-400 leading-relaxed mt-1">
                Protecting critical infrastructure, financial institutions, healthcare data, and personal privacy.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-1">
              <div className="text-xs font-semibold text-rose-400 uppercase tracking-wider">
                Evolving Threats
              </div>
              <div className="text-2xl font-bold text-white">Constant Evolution</div>
              <p className="text-xs text-slate-400 leading-relaxed mt-1">
                Adversaries continuously develop new exploitation techniques, automation, and social engineering.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-1">
              <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                Multi-Layered
              </div>
              <div className="text-2xl font-bold text-white">Defense in Depth</div>
              <p className="text-xs text-slate-400 leading-relaxed mt-1">
                Employing people, processes, and technology across every layer of the digital infrastructure.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 1: THE CORE FOUNDATION - THE CIA TRIAD */}
        <section id="cia-triad" className="space-y-8 pt-6 border-t border-slate-800/80">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              The Core Foundation: The CIA Triad
            </h2>
            <p className="text-sm text-slate-400">
              The CIA Triad is the foundational model guiding information security policies and architectures.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Confidentiality */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
                <Lock className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white">Confidentiality</h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                Ensuring that sensitive information is accessible solely to authorized individuals, entities, and systems, preventing unauthorized disclosure.
              </p>
              <div className="space-y-2 text-xs text-slate-400 pt-3 border-t border-slate-800">
                <div className="font-semibold text-slate-300">Key Implementations:</div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" />
                  <span>Strong Data Encryption (AES-256)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" />
                  <span>Multi-Factor Authentication (MFA)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" />
                  <span>Role-Based Access Control (RBAC)</span>
                </div>
              </div>
            </div>

            {/* Integrity */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white">Integrity</h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                Maintaining the accuracy, trustworthiness, and completeness of data over its entire lifecycle, ensuring it is not improperly altered or deleted.
              </p>
              <div className="space-y-2 text-xs text-slate-400 pt-3 border-t border-slate-800">
                <div className="font-semibold text-slate-300">Key Implementations:</div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Cryptographic Hashes (SHA-256)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Digital Signatures & Certificates</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Immutable Audit Logging</span>
                </div>
              </div>
            </div>

            {/* Availability */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white">Availability</h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                Guaranteeing that systems, applications, and data are consistently accessible and operational for authorized users whenever needed.
              </p>
              <div className="space-y-2 text-xs text-slate-400 pt-3 border-t border-slate-800">
                <div className="font-semibold text-slate-300">Key Implementations:</div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />
                  <span>Redundancy & Failover Systems</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />
                  <span>DDoS Mitigation & Rate Limiting</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />
                  <span>Disaster Recovery & Backup Archives</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 2: MAJOR CYBER THREAT VECTORS */}
        <section id="threats" className="space-y-8 pt-6 border-t border-slate-800/80">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Major Cyber Threat Vectors
            </h2>
            <p className="text-sm text-slate-400">
              Understanding common attack mechanisms used by threat actors and organized syndicates.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Phishing */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">
                  Phishing & Social Engineering
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Deceptive communications (emails, SMS, fake portals) crafted to manipulate individuals into divulging sensitive credentials, financial details, or downloading malware.
              </p>
            </div>

            {/* Ransomware */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <Flame className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">
                  Malware & Ransomware
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Malicious software designed to infiltrate, damage, or take control of systems. Ransomware encrypts victim files and demands extortion payments for decryption keys.
              </p>
            </div>

            {/* DDoS */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <Activity className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">
                  Distributed Denial of Service (DDoS)
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Overwhelming a targeted server, network, or service with massive waves of automated internet traffic from botnets, rendering it inaccessible to legitimate users.
              </p>
            </div>

            {/* SQL Injection */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  <Database className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">
                  SQL Injection & Code Exploits
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Inserting malicious SQL commands into unprotected input fields to bypass authentication, extract complete database records, or modify server data.
              </p>
            </div>

            {/* Man in the Middle */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Wifi className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">
                  Man-in-the-Middle (MitM)
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Eavesdropping on or intercepting communication sessions between two parties over insecure or rogue Wi-Fi networks to steal credentials and session tokens.
              </p>
            </div>

            {/* Zero Day */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Cpu className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">
                  Zero-Day Exploits
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Exploitation of previously unknown software or hardware security flaws before the developer or vendor has released a protective security patch.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 3: KEY PILLARS OF CYBER DEFENSE */}
        <section id="defense" className="space-y-8 pt-6 border-t border-slate-800/80">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Pillars of Modern Cyber Defense
            </h2>
            <p className="text-sm text-slate-400">
              A comprehensive Defense-in-Depth framework implemented across modern enterprise architectures.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Network Security */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
                  <Globe className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">Network Security</h3>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                Securing network perimeters and internal topologies through Next-Generation Firewalls (NGFW), Intrusion Detection and Prevention Systems (IDS/IPS), network segmentation, and secure Virtual Private Networks (VPNs).
              </p>
            </div>

            {/* Endpoint Security */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                  <Smartphone className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">Endpoint Detection & Response (EDR)</h3>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                Protecting individual user devices (workstations, mobile devices, servers) with continuous behavioral monitoring, automated threat isolation, and centralized telemetry.
              </p>
            </div>

            {/* Identity & Access Management */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                  <Key className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">Identity & Access Management (IAM)</h3>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                Enforcing the Principle of Least Privilege, robust passwordless or hardware-backed Multi-Factor Authentication (FIDO2), and centralized single sign-on with granular role permissions.
              </p>
            </div>

            {/* Cloud Security */}
            <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                  <Cloud className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">Cloud Infrastructure Security</h3>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                Securing cloud environments, microservices, and containerized workloads through strict configuration posture management (CSPM), encrypted storage buckets, and zero-trust networking.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 4: ESSENTIAL BEST PRACTICES */}
        <section id="best-practices" className="space-y-8 pt-6 border-t border-slate-800/80">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Essential Cybersecurity Best Practices
            </h2>
            <p className="text-sm text-slate-400">
              Crucial operational security measures for individuals and organizations.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-5 rounded-xl bg-[#0F172A] border border-slate-800 space-y-2">
              <div className="text-sky-400 font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>Multi-Factor Authentication</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Always enable 2FA/MFA across email, banking, cloud storage, and social accounts to block 99% of automated credential attacks.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0F172A] border border-slate-800 space-y-2">
              <div className="text-sky-400 font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>Prompt Patch Management</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Consistently update operating systems, applications, routers, and firmware to remediate known vulnerabilities.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0F172A] border border-slate-800 space-y-2">
              <div className="text-sky-400 font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>Immutable 3-2-1 Backups</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Keep 3 copies of important data on 2 different media types, with 1 copy stored securely off-site or in air-gapped storage.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0F172A] border border-slate-800 space-y-2">
              <div className="text-sky-400 font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>Password Managers</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Utilize reputable password managers to generate and store complex, unique, high-entropy passwords for each service.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0F172A] border border-slate-800 space-y-2">
              <div className="text-sky-400 font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phishing Vigilance</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Inspect sender addresses, verify unexpected attachments, avoid clicking urgent links, and report suspicious messages.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#0F172A] border border-slate-800 space-y-2">
              <div className="text-sky-400 font-bold text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>Zero Trust Architecture</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Adopt the core security principle: &quot;Never trust, always verify&quot; for every request regardless of origin.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 5: THE FUTURE OF CYBERSECURITY */}
        <section className="p-8 rounded-3xl bg-gradient-to-r from-slate-900 to-sky-950/40 border border-slate-800 space-y-4 text-center max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-white">
            The Future of Cybersecurity: AI & Quantum Resistance
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed max-w-2xl mx-auto">
            As computational power grows, cybersecurity is advancing towards predictive artificial intelligence for real-time anomaly detection, automated incident containment, and post-quantum cryptographic standards (NIST PQC) designed to withstand quantum computer decryption.
          </p>
        </section>
      </main>

      {/* Clean Footer (No Buttons) */}
      <footer className="border-t border-slate-800 bg-[#080D1A] py-12 px-6 lg:px-12 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-6 h-6 rounded bg-sky-600 text-white font-bold text-xs">
              <Shield className="w-3.5 h-3.5" />
            </div>
            <span className="font-bold text-white text-sm font-glitch tracking-wider">
              CYBER SENTINALS
            </span>
          </div>

          <div className="text-center sm:text-right text-slate-500 font-sans">
            <p>© 2026 Cyber Sentinals. Informational & Educational Cybersecurity Resource.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
