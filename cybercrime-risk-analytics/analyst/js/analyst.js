/**
 * Phase 17 — Analyst Interface: Shared Utilities, Auth & Navigation
 * Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
 *
 * PROTOTYPE AUTHENTICATION — NOT production government authentication.
 * SYNTHETIC DEMONSTRATION DATA — Not real banking or NCRP records.
 */

'use strict';

// ─── API Base URL ────────────────────────────────────────────────────────────
const API_BASE = window.location.origin;
const ANALYST_API = `${API_BASE}/analyst`;

// ─── Auth State ───────────────────────────────────────────────────────────────
const Auth = {
  _key: 'analyst_token',
  _roleKey: 'analyst_role',
  _userKey: 'analyst_user',

  getToken() { return sessionStorage.getItem(this._key); },
  getRole()  { return sessionStorage.getItem(this._roleKey) || 'ANALYST'; },
  getUser()  { return sessionStorage.getItem(this._userKey) || 'analyst'; },

  setSession(token, role, displayName) {
    sessionStorage.setItem(this._key, token);
    sessionStorage.setItem(this._roleKey, role);
    sessionStorage.setItem(this._userKey, displayName || role);
  },

  clearSession() {
    sessionStorage.removeItem(this._key);
    sessionStorage.removeItem(this._roleKey);
    sessionStorage.removeItem(this._userKey);
  },

  isLoggedIn() { return !!this.getToken(); },

  hasRole(...roles) { return roles.includes(this.getRole()); },

  authHeaders() {
    const token = this.getToken();
    return token
      ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      : { 'Content-Type': 'application/json' };
  }
};

// ─── HTTP Helper ──────────────────────────────────────────────────────────────
const Http = {
  async get(path, params = {}) {
    const url = new URL(`${ANALYST_API}${path}`);
    Object.entries(params).forEach(([k, v]) => { if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v); });
    const res = await fetch(url.toString(), { headers: Auth.authHeaders() });
    return this._handle(res);
  },

  async post(path, body = {}) {
    const res = await fetch(`${ANALYST_API}${path}`, {
      method: 'POST',
      headers: Auth.authHeaders(),
      body: JSON.stringify(body),
    });
    return this._handle(res);
  },

  async patch(path, body = {}) {
    const res = await fetch(`${ANALYST_API}${path}`, {
      method: 'PATCH',
      headers: Auth.authHeaders(),
      body: JSON.stringify(body),
    });
    return this._handle(res);
  },

  async _handle(res) {
    if (res.status === 401) {
      Auth.clearSession();
      window.location.href = '/analyst/index.html';
      throw new Error('Session expired. Please log in again.');
    }
    if (res.status === 403) {
      throw new Error('Access denied. Your role does not have permission for this action.');
    }
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const j = await res.json();
        detail = j.detail || detail;
      } catch {}
      throw new Error(detail);
    }
    try { return await res.json(); } catch { return {}; }
  }
};

// ─── Toast Notifications ──────────────────────────────────────────────────────
const Toast = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(message, type = 'info', duration = 4000) {
    this.init();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    this.container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  success(msg) { this.show(msg, 'success'); },
  error(msg)   { this.show(msg, 'error', 6000); },
  info(msg)    { this.show(msg, 'info'); },
};

// ─── Date / Format Utilities ──────────────────────────────────────────────────
const Fmt = {
  datetime(iso) {
    if (!iso || iso === 'nan' || iso === 'NaN') return '—';
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return '—';
      return d.toLocaleString('en-IN', {
        year: 'numeric', month: 'short', day: '2-digit',
        hour: '2-digit', minute: '2-digit', hour12: false,
        timeZone: 'Asia/Kolkata',
      });
    } catch { return '—'; }
  },

  date(iso) {
    if (!iso || iso === 'nan' || iso === 'NaN') return '—';
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return '—';
      return d.toLocaleDateString('en-IN');
    } catch { return '—'; }
  },

  riskBadge(severity) {
    if (!severity) return '<span class="badge">—</span>';
    const s = String(severity).toUpperCase();
    const cls = {
      CRITICAL: 'badge-critical', HIGH: 'badge-high',
      MODERATE: 'badge-moderate', LOW: 'badge-low'
    }[s] || '';
    return `<span class="badge ${cls}">${s}</span>`;
  },

  statusBadge(status) {
    if (!status) return '<span class="badge">—</span>';
    const s = String(status).toUpperCase();
    const cls = {
      NEW: 'badge-new',
      ACKNOWLEDGED: 'badge-ack',
      IN_REVIEW: 'badge-in-review',
      RESOLVED: 'badge-resolved',
      DISMISSED: 'badge-dismissed',
      OPEN: 'badge-open',
      UNDER_REVIEW: 'badge-under-review',
      PENDING_VALIDATION: 'badge-pending-validation',
      CLOSED: 'badge-closed',
    }[s] || '';
    return `<span class="badge ${cls}">${s.replace(/_/g, ' ')}</span>`;
  },

  riskCircle(score, category) {
    const cls = (category || '').toLowerCase();
    const val = (score !== null && score !== undefined && !isNaN(Number(score))) ? Math.round(Number(score)) : '—';
    return `<div class="risk-score-circle ${cls}">${val}</div>`;
  },

  number(n) {
    if (n === null || n === undefined || n === '') return '—';
    const num = Number(n);
    return isNaN(num) ? '—' : num.toLocaleString();
  },

  percent(p) {
    if (p === null || p === undefined || p === '') return '—';
    const num = parseFloat(p);
    return isNaN(num) ? '—' : `${(num * 100).toFixed(1)}%`;
  },

  score(s) {
    if (s === null || s === undefined || s === '') return '—';
    const num = parseFloat(s);
    return isNaN(num) ? '—' : `${Math.round(num)}/100`;
  },
};

// ─── Navigation ───────────────────────────────────────────────────────────────
const Nav = {
  pages: [
    { id: 'overview',        icon: '⬡',  label: 'Overview',        href: '/analyst/index.html' },
    { id: 'alerts',          icon: '⚠',  label: 'Alerts',          href: '/analyst/alerts.html' },
    { id: 'investigations',  icon: '🔍', label: 'Investigations',   href: '/analyst/investigation.html' },
    { id: 'audit',           icon: '📋', label: 'Audit Log',        href: '/analyst/audit.html',
      roles: ['SUPERVISOR', 'ADMIN'] },
  ],

  render(containerId, activePage) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const role = Auth.getRole();
    el.innerHTML = this.pages
      .filter(p => !p.roles || p.roles.includes(role))
      .map(p => `
        <a class="nav-item ${p.id === activePage ? 'active' : ''}"
           href="${p.href}" id="nav-${p.id}">
          <span class="nav-icon">${p.icon}</span>
          <span>${p.label}</span>
        </a>
      `).join('');
  },

  renderExternalLinks(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = `
      <a class="nav-item" href="/dashboard" target="_blank">
        <span class="nav-icon">🗺</span>
        <span>GIS Dashboard</span>
      </a>
      <a class="nav-item" href="/docs" target="_blank">
        <span class="nav-icon">📖</span>
        <span>API Docs</span>
      </a>
    `;
  }
};

// ─── Login Logic ──────────────────────────────────────────────────────────────
const Login = {
  async init(onLoginSuccess) {
    const form = document.getElementById('login-form');
    const errorEl = document.getElementById('login-error');
    const shell = document.getElementById('app-shell');
    const loginScreen = document.getElementById('login-screen');

    if (!form) return;

    // Demo credential auto-fill buttons
    const bindDemoBtn = (btnId, user, pass) => {
      const btn = document.getElementById(btnId);
      if (btn) {
        btn.addEventListener('click', () => {
          const uEl = document.getElementById('username');
          const pEl = document.getElementById('password');
          if (uEl) uEl.value = user;
          if (pEl) pEl.value = pass;
          if (errorEl) errorEl.classList.remove('visible');
        });
      }
    };

    bindDemoBtn('btn-demo-analyst', 'demo_analyst', 'AnalystDemo2026!');
    bindDemoBtn('btn-demo-supervisor', 'demo_supervisor', 'SupervisorDemo2026!');
    bindDemoBtn('btn-demo-admin', 'demo_admin', 'AdminDemo2026!');

    // Support code elements if present
    document.querySelectorAll('.demo-cred-row code[data-user]').forEach(el => {
      el.addEventListener('click', () => {
        const user = el.getAttribute('data-user');
        const pass = el.getAttribute('data-pass');
        const uEl = document.getElementById('username');
        const pEl = document.getElementById('password');
        if (uEl) uEl.value = user;
        if (pEl) pEl.value = pass;
        if (errorEl) errorEl.classList.remove('visible');
      });
    });

    // Check existing session
    if (Auth.isLoggedIn()) {
      this._showApp(loginScreen, shell);
      return;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = (document.getElementById('username')?.value || '').trim();
      const password = document.getElementById('password')?.value || '';
      const btn = form.querySelector('button[type="submit"]');

      if (!username || !password) {
        if (errorEl) {
          errorEl.textContent = 'Invalid username or password.';
          errorEl.classList.add('visible');
        }
        return;
      }
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Authenticating…';
      }
      if (errorEl) { errorEl.classList.remove('visible'); }

      try {
        const data = await fetch(`${ANALYST_API}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });
        const res = await data.json().catch(() => ({}));
        if (!data.ok) {
          throw new Error('Invalid username or password.');
        }

        Auth.setSession(res.access_token, res.role, res.display_name);
        this._showApp(loginScreen, shell);
        if (typeof onLoginSuccess === 'function') {
          onLoginSuccess();
        }
      } catch (err) {
        if (errorEl) {
          errorEl.textContent = 'Invalid username or password.';
          errorEl.classList.add('visible');
        }
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.textContent = 'Log In';
        }
      }
    });
  },

  _showApp(loginScreen, shell) {
    if (loginScreen) loginScreen.style.display = 'none';
    if (shell) {
      shell.classList.add('visible');
      this._updateUserDisplay();
    }
  },

  _updateUserDisplay() {
    const userEl = document.getElementById('hdr-user');
    const roleBadge = document.getElementById('hdr-role');
    if (userEl) userEl.textContent = Auth.getUser();
    if (roleBadge) {
      const role = Auth.getRole();
      roleBadge.textContent = role;
      roleBadge.className = `user-badge ${role}`;
    }
  },

  logout() {
    Auth.clearSession();
    window.location.href = '/analyst/index.html';
    if (window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/analyst/')) {
      window.location.reload();
    }
  }
};

// ─── Shared Page Init ─────────────────────────────────────────────────────────
function initPageShell(activePage) {
  // Ensure app shell is visible
  const shell = document.getElementById('app-shell');
  if (shell) shell.classList.add('visible');

  // Render navigation
  Nav.render('sidebar-nav', activePage);
  Nav.renderExternalLinks('sidebar-external');

  // Update header
  const userEl = document.getElementById('hdr-user');
  const roleBadge = document.getElementById('hdr-role');
  if (userEl) userEl.textContent = Auth.getUser();
  if (roleBadge) {
    const role = Auth.getRole();
    roleBadge.textContent = role;
    roleBadge.className = `user-badge ${role}`;
  }

  // Logout button
  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) logoutBtn.onclick = () => Login.logout();

  // Clock
  const clockEl = document.getElementById('hdr-time');
  if (clockEl) {
    const tick = () => {
      clockEl.textContent = new Date().toLocaleTimeString('en-IN', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false, timeZone: 'Asia/Kolkata'
      }) + ' IST';
    };
    tick();
    if (!window._clockTimer) {
      window._clockTimer = setInterval(tick, 1000);
    }
  }

  // Guard role for audit page
  if (activePage === 'audit' && !Auth.hasRole('SUPERVISOR', 'ADMIN')) {
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
      mainContent.innerHTML = `
        <div class="disclaimer-banner disclaimer-critical" style="margin-top:48px;max-width:500px">
          <strong>Access Denied</strong><br>
          The Audit Log requires SUPERVISOR or ADMIN role.<br>
          Your role: <strong>${Auth.getRole()}</strong>
        </div>`;
    }
  }
}

// ─── Guarded Page Entry ───────────────────────────────────────────────────────
function requireAuth(activePage, onReady) {
  if (!Auth.isLoggedIn()) {
    window.location.href = '/analyst/index.html';
    return;
  }
  const run = () => {
    initPageShell(activePage);
    if (onReady) onReady();
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
}
