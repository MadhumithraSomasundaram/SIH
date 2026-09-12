import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Lock, 
  User, 
  Eye, 
  EyeOff, 
  AlertTriangle, 
  Loader2, 
  Sparkles, 
  Sun,
  ShieldCheck
} from 'lucide-react';
import { useAuth } from '../context/useAuth';

export function Login() {
  const [officerId, setOfficerId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, theme, setTheme } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!officerId.trim()) {
      setErrorMessage('Officer ID is required.');
      return;
    }

    if (!password.trim()) {
      setErrorMessage('Password is required.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(officerId, password);
      navigate(from, { replace: true });
    } catch (err) {
      setErrorMessage(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--cyber-bg)] text-[var(--cyber-text-secondary)] font-sans transition-colors duration-300 relative flex flex-col justify-between overflow-hidden">
      {/* Ambient Top Glow Orbs (matching existing design) */}
      <div 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] rounded-full blur-[140px] pointer-events-none transition-all duration-700 opacity-40 z-0"
        style={{ background: 'var(--cyber-accent)' }}
      />
      <div 
        className="fixed bottom-0 right-[-100px] w-[500px] h-[500px] rounded-full blur-[170px] pointer-events-none transition-all duration-700 opacity-20 z-0"
        style={{ background: 'var(--cyber-accent-secondary)' }}
      />

      {/* Top Header / Branding Bar */}
      <header className="relative z-10 px-6 py-4 flex items-center justify-between border-b border-[var(--cyber-border)] bg-[var(--cyber-header-bg)]/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <img
            src="/logo.png"
            alt="Cyber Sentinals Logo"
            className="w-9 h-9 object-contain drop-shadow-[0_0_10px_var(--cyber-glow)]"
          />
          <div className="flex items-center gap-1.5 leading-none">
            <span className="text-lg font-black chrome-text font-corptic tracking-wider">
              CYBER
            </span>
            <span className="text-lg font-black font-corptic tracking-wider neon-accent-text">
              SENTINELS
            </span>
          </div>
        </div>

        {/* Dual Theme Switcher */}
        <div className="flex items-center rounded-xl p-1 bg-[var(--cyber-bg-card)] border border-[var(--cyber-border)] shadow-sm">
          <button
            type="button"
            onClick={() => setTheme('cyber-blue')}
            className={`p-1.5 px-3 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 ${
              theme === 'cyber-blue'
                ? 'bg-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-sm font-bold'
                : 'text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)]'
            }`}
            title="Cyber Cyan Theme"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span className="font-mono text-[10px] uppercase">Cyan</span>
          </button>
          <button
            type="button"
            onClick={() => setTheme('quantum-light')}
            className={`p-1.5 px-3 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 ${
              theme === 'quantum-light'
                ? 'bg-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-sm font-bold'
                : 'text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)]'
            }`}
            title="Quantum Light Theme"
          >
            <Sun className="w-3.5 h-3.5" />
            <span className="font-mono text-[10px] uppercase">Light</span>
          </button>
        </div>
      </header>

      {/* Main Login Form Section */}
      <main className="relative z-10 flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-md space-y-6">
          
          {/* Card Container */}
          <div className="cyber-panel p-8 sm:p-10 rounded-3xl relative overflow-hidden shadow-2xl">
            <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-[var(--cyber-accent)] to-transparent opacity-80" />

            {/* Emblem & Title */}
            <div className="text-center space-y-3 pb-6 border-b border-[var(--cyber-border)]">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-accent)] shadow-[0_0_20px_var(--cyber-glow-subtle)] mb-1">
                <ShieldCheck className="w-8 h-8" />
              </div>
              
              <div>
                <h1 className="text-2xl sm:text-3xl font-black font-corptic tracking-wider text-[var(--cyber-text-primary)]">
                  CYBERGUARD LEA
                </h1>
                <p className="text-[11px] font-mono uppercase tracking-wider text-[var(--cyber-accent)] mt-1">
                  LAW ENFORCEMENT CYBER INTELLIGENCE & RESPONSE PLATFORM
                </p>
              </div>
            </div>

            {/* Error Message Banner */}
            {errorMessage && (
              <div className="mt-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-start gap-2.5 text-xs animate-in fade-in duration-200">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span className="leading-relaxed font-medium">{errorMessage}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="mt-6 space-y-5">
              {/* Officer ID Field */}
              <div className="space-y-2">
                <label 
                  htmlFor="officer-id" 
                  className="block text-xs font-mono font-bold tracking-wider text-[var(--cyber-text-primary)] uppercase"
                >
                  OFFICER ID
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[var(--cyber-text-muted)]">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    id="officer-id"
                    type="text"
                    value={officerId}
                    onChange={(e) => setOfficerId(e.target.value)}
                    placeholder="Enter assigned Officer ID"
                    autoComplete="username"
                    disabled={isSubmitting}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-text-primary)] text-sm placeholder-[var(--cyber-text-muted)] focus:outline-none focus:border-[var(--cyber-accent)] focus:ring-1 focus:ring-[var(--cyber-accent)] transition-all"
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <label 
                  htmlFor="officer-password" 
                  className="block text-xs font-mono font-bold tracking-wider text-[var(--cyber-text-primary)] uppercase"
                >
                  PASSWORD
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[var(--cyber-text-muted)]">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="officer-password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter secure password"
                    autoComplete="current-password"
                    disabled={isSubmitting}
                    className="w-full pl-10 pr-11 py-3 rounded-xl bg-[var(--cyber-bg-secondary)] border border-[var(--cyber-border)] text-[var(--cyber-text-primary)] text-sm placeholder-[var(--cyber-text-muted)] focus:outline-none focus:border-[var(--cyber-accent)] focus:ring-1 focus:ring-[var(--cyber-accent)] transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-[var(--cyber-text-muted)] hover:text-[var(--cyber-text-primary)] transition-colors"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Login Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3.5 px-4 rounded-xl bg-[var(--cyber-accent)] text-[#030714] font-bold text-sm font-corptic tracking-widest uppercase hover:opacity-90 active:scale-[0.99] transition-all duration-200 shadow-[0_0_20px_var(--cyber-glow)] flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>AUTHENTICATING...</span>
                  </>
                ) : (
                  <span>AUTHENTICATE OFFICER</span>
                )}
              </button>
            </form>

            {/* Secure Notice */}
            <div className="mt-6 pt-5 border-t border-[var(--cyber-border)] text-center">
              <p className="text-[10px] font-mono tracking-wider text-[var(--cyber-text-muted)] uppercase">
                Secure LEA Channel // Authorized Personnel Only
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-4 px-6 text-center text-xs text-[var(--cyber-text-muted)] font-mono border-t border-[var(--cyber-border)]">
        CYBER SENTINELS // LAW ENFORCEMENT CYBER DIVISION
      </footer>
    </div>
  );
}

export default Login;
