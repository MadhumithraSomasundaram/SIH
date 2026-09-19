/**
 * Secure Banking Interface: Client-side Logic
 * Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
 *
 * PROTOTYPE READ-ONLY INTERFACE:
 * - Scoped strictly to bank physical ATM network and nearby predictive hotspots.
 * - Read-only analytical decision support.
 * - Reuses JWT authentication pattern.
 */
'use strict';

const API_BASE = window.location.origin;
const BANK_API = `${API_BASE}/bank`;

const BankAuth = {
  _key: 'bank_token',
  _roleKey: 'bank_role',
  _userKey: 'bank_user',
  _bankIdKey: 'bank_id',

  getToken() { return sessionStorage.getItem(this._key); },
  getRole()  { return sessionStorage.getItem(this._roleKey) || 'BANK_ANALYST'; },
  getUser()  { return sessionStorage.getItem(this._userKey) || 'demo_bank'; },
  getBankId(){ return sessionStorage.getItem(this._bankIdKey) || 'BANK001'; },

  setSession(token, role, displayName, bankId = 'BANK001') {
    sessionStorage.setItem(this._key, token);
    sessionStorage.setItem(this._roleKey, role);
    sessionStorage.setItem(this._userKey, displayName || role);
    sessionStorage.setItem(this._bankIdKey, bankId);
  },

  clearSession() {
    sessionStorage.removeItem(this._key);
    sessionStorage.removeItem(this._roleKey);
    sessionStorage.removeItem(this._userKey);
    sessionStorage.removeItem(this._bankIdKey);
  },

  isLoggedIn() { return !!this.getToken(); },

  authHeaders() {
    const token = this.getToken();
    return token
      ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      : { 'Content-Type': 'application/json' };
  }
};

let currentAlertsData = [];

document.addEventListener('DOMContentLoaded', () => {
  setupClock();
  setupLoginScreen();
  setupFilters();

  if (BankAuth.isLoggedIn()) {
    showAppShell();
    loadBankAlerts();
  } else {
    showLoginScreen();
  }
});

function setupClock() {
  const el = document.getElementById('hdr-time');
  if (!el) return;
  const tick = () => {
    el.textContent = new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
  };
  tick();
  setInterval(tick, 1000);
}

function showLoginScreen() {
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('app-shell').style.display = 'none';
}

function showAppShell() {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app-shell').style.display = 'flex';

  document.getElementById('hdr-user').textContent = BankAuth.getUser();
  document.getElementById('hdr-role').textContent = BankAuth.getRole();
  const bankSelect = document.getElementById('filter-bank-id');
  if (bankSelect) {
    bankSelect.value = BankAuth.getBankId();
  }
  const bankTag = document.getElementById('hdr-bank-tag');
  if (bankTag) {
    bankTag.textContent = BankAuth.getBankId();
  }
}

function setupLoginScreen() {
  const form = document.getElementById('login-form');
  const errorEl = document.getElementById('login-error');
  const demoBtn = document.getElementById('btn-demo-bank');
  const logoutBtn = document.getElementById('btn-logout');

  if (demoBtn) {
    demoBtn.addEventListener('click', () => {
      document.getElementById('username').value = 'demo_bank';
      document.getElementById('password').value = 'BankDemo2026!';
      if (errorEl) errorEl.classList.remove('visible');
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      BankAuth.clearSession();
      showLoginScreen();
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = (document.getElementById('username')?.value || '').trim();
      const password = document.getElementById('password')?.value || '';
      const btn = document.getElementById('btn-login-submit');

      if (!username || !password) {
        if (errorEl) {
          errorEl.textContent = 'Please provide both username and password.';
          errorEl.classList.add('visible');
        }
        return;
      }

      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Authenticating…';
      }
      if (errorEl) errorEl.classList.remove('visible');

      try {
        const res = await fetch(`${BANK_API}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });

        if (!res.ok) {
          let detail = `Authentication failed (${res.status})`;
          try {
            const errData = await res.json();
            detail = errData.detail || detail;
          } catch {}
          throw new Error(detail);
        }

        const data = await res.json();
        BankAuth.setSession(data.access_token, data.role, data.display_name, 'BANK001');
        showAppShell();
        loadBankAlerts();
      } catch (err) {
        if (errorEl) {
          errorEl.textContent = err.message || 'Login failed. Please check credentials.';
          errorEl.classList.add('visible');
        }
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.textContent = 'Sign In to Banking Portal';
        }
      }
    });
  }
}

function setupFilters() {
  const bankSelect = document.getElementById('filter-bank-id');
  const radiusSelect = document.getElementById('filter-radius');
  const severitySelect = document.getElementById('filter-severity');
  const applyBtn = document.getElementById('btn-apply-filters');

  if (bankSelect) {
    bankSelect.addEventListener('change', () => {
      BankAuth.setSession(BankAuth.getToken(), BankAuth.getRole(), BankAuth.getUser(), bankSelect.value);
      const bankTag = document.getElementById('hdr-bank-tag');
      if (bankTag) bankTag.textContent = bankSelect.value;
      loadBankAlerts();
    });
  }

  if (radiusSelect) {
    radiusSelect.addEventListener('change', () => loadBankAlerts());
  }
  if (severitySelect) {
    severitySelect.addEventListener('change', () => loadBankAlerts());
  }
  if (applyBtn) {
    applyBtn.addEventListener('click', () => loadBankAlerts());
  }
}

async function loadBankAlerts() {
  const bankId = document.getElementById('filter-bank-id')?.value || BankAuth.getBankId();
  const radiusKm = document.getElementById('filter-radius')?.value || '5.0';
  const severity = document.getElementById('filter-severity')?.value || '';

  const tableBody = document.getElementById('alerts-table-body');
  const loadingEl = document.getElementById('alerts-loading');
  const emptyEl = document.getElementById('alerts-empty');

  if (loadingEl) loadingEl.style.display = 'block';
  if (emptyEl) emptyEl.style.display = 'none';
  if (tableBody) tableBody.innerHTML = '';

  try {
    const params = new URLSearchParams({
      bank_id: bankId,
      radius_km: radiusKm,
      limit: '100',
    });
    if (severity) params.set('severity', severity);

    const res = await fetch(`${BANK_API}/alerts?${params.toString()}`, {
      headers: BankAuth.authHeaders(),
    });

    if (res.status === 401) {
      BankAuth.clearSession();
      showLoginScreen();
      return;
    }
    if (res.status === 403) {
      throw new Error('Access denied. BANK_ANALYST or ADMIN role required.');
    }
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    currentAlertsData = data.alerts || [];

    // Update KPI counters
    document.getElementById('kpi-bank-atms').textContent = data.total_bank_atms ?? 0;
    document.getElementById('kpi-matched-hotspots').textContent = data.total_matching_hotspots ?? 0;
    document.getElementById('kpi-total-alerts').textContent = data.total_alerts ?? 0;

    const highCritCount = currentAlertsData.filter(a => ['CRITICAL', 'HIGH'].includes((a.severity || '').toUpperCase())).length;
    document.getElementById('kpi-high-crit').textContent = highCritCount;

    document.getElementById('alerts-count-tag').textContent = `${data.total_alerts} alert(s) within ${radiusKm}km radius`;

    renderAlertsTable(currentAlertsData);
  } catch (err) {
    if (tableBody) {
      tableBody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--critical);padding:24px;">⚠ Error loading bank alerts: ${escapeHtml(err.message)}</td></tr>`;
    }
  } finally {
    if (loadingEl) loadingEl.style.display = 'none';
  }
}

function renderAlertsTable(alerts) {
  const tableBody = document.getElementById('alerts-table-body');
  const emptyEl = document.getElementById('alerts-empty');
  if (!tableBody) return;

  if (!alerts || alerts.length === 0) {
    if (emptyEl) emptyEl.style.display = 'block';
    return;
  }
  if (emptyEl) emptyEl.style.display = 'none';

  tableBody.innerHTML = alerts.map((a, idx) => {
    const sevClass = (a.severity || 'HIGH').toLowerCase();
    const riskScore = a.risk_score !== null && a.risk_score !== undefined ? `${a.risk_score}/100` : '—';
    const distText = a.distance_to_atm_km !== null && a.distance_to_atm_km !== undefined
      ? `${a.distance_to_atm_km} km`
      : '—';

    return `
      <tr>
        <td>
          <a href="#" onclick="viewAlertDetail(${idx}); return false;" style="font-family:var(--font-mono);font-weight:600;">
            ${escapeHtml(a.alert_id)}
          </a>
        </td>
        <td>
          <span class="badge badge-${sevClass}">${escapeHtml(a.severity)}</span>
        </td>
        <td>
          <div style="display:inline-flex;align-items:center;gap:6px;">
            <span class="risk-score-circle ${sevClass}" style="width:26px;height:26px;font-size:0.75rem;">${a.risk_score ?? '—'}</span>
            <span style="font-size:0.75rem;color:var(--text-muted);">${riskScore}</span>
          </div>
        </td>
        <td>
          <span class="atm-chip">${escapeHtml(a.hotspot_id || '—')}</span>
        </td>
        <td>
          <div style="display:flex;flex-direction:column;gap:2px;">
            <span class="atm-chip" style="color:#26c6da;border-color:rgba(38,198,218,0.35);">${escapeHtml(a.nearest_atm_id || '—')}</span>
            <span class="distance-pill">📍 ${distText}</span>
          </div>
        </td>
        <td>
          <span style="font-size:0.8rem;color:var(--text-secondary);">${escapeHtml(a.dominant_category || 'Clustered Incidents')}</span>
        </td>
        <td style="max-width:280px;">
          <div style="font-size:0.78rem;color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(a.operational_message || '')}">
            ${escapeHtml(a.operational_message || 'Predictive alert near ATM location.')}
          </div>
        </td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="viewAlertDetail(${idx})">
            Inspect
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function viewAlertDetail(index) {
  const alert = currentAlertsData[index];
  if (!alert) return;

  const modal = document.getElementById('detail-modal');
  const body = document.getElementById('detail-modal-content');
  if (!modal || !body) return;

  const sevClass = (alert.severity || 'HIGH').toLowerCase();
  const distText = alert.distance_to_atm_km !== null ? `${alert.distance_to_atm_km} km` : '—';
  const probText = alert.predicted_probability !== null ? `${(alert.predicted_probability * 100).toFixed(1)}%` : '—';

  body.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
      <div>
        <h3 style="font-size:1.1rem;font-weight:600;display:flex;align-items:center;gap:8px;">
          ${escapeHtml(alert.alert_id)}
          <span class="badge badge-${sevClass}">${escapeHtml(alert.severity)}</span>
        </h3>
        <p style="font-size:0.78rem;color:var(--text-muted);margin-top:2px;">
          Type: ${escapeHtml(alert.alert_type)} · Status: ${escapeHtml(alert.status)}
        </p>
      </div>
      <div class="readonly-watermark">
        🔒 Read-Only Banking Scope
      </div>
    </div>

    <!-- Mandatory Disclaimer -->
    <div class="disclaimer-banner" style="margin-bottom:16px;">
      <strong>Notice:</strong> ${escapeHtml(alert.disclaimer)}
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
      <div class="card" style="padding:12px;">
        <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;">Predictive Risk Assessment</div>
        <div style="font-size:1.2rem;font-weight:700;color:var(--text-primary);margin-top:4px;">
          ${alert.risk_score ?? '—'}/100
        </div>
        <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:2px;">
          Withdrawal Probability: <strong>${probText}</strong>
        </div>
      </div>

      <div class="card" style="padding:12px;">
        <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;">Bank ATM Proximity</div>
        <div style="font-size:1.2rem;font-weight:700;color:#26c6da;margin-top:4px;">
          ${escapeHtml(alert.nearest_atm_id || '—')}
        </div>
        <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:2px;">
          Proximity Distance: <strong>${distText}</strong> to hotspot ${escapeHtml(alert.hotspot_id || '')}
        </div>
      </div>
    </div>

    <div class="card" style="padding:14px;margin-bottom:14px;">
      <div style="font-size:0.75rem;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">
        Operational Assessment
      </div>
      <p style="font-size:0.82rem;line-height:1.5;color:var(--text-primary);">
        ${escapeHtml(alert.operational_message || 'No specific operational guidance text.')}
      </p>
    </div>

    <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:10px;font-size:0.75rem;color:var(--text-secondary);background:var(--bg-card);padding:12px;border-radius:var(--radius-sm);border:1px solid var(--border-dim);">
      <div>
        <span style="color:var(--text-muted);display:block;">Incident Category:</span>
        <strong style="color:var(--text-primary);">${escapeHtml(alert.dominant_category || '—')}</strong>
      </div>
      <div>
        <span style="color:var(--text-muted);display:block;">Coordinates (Lat/Lon):</span>
        <strong style="color:var(--text-primary);">${alert.latitude ?? '—'}, ${alert.longitude ?? '—'}</strong>
      </div>
      <div>
        <span style="color:var(--text-muted);display:block;">Time Window:</span>
        <strong style="color:var(--text-primary);">${escapeHtml(alert.time_window_start || '—')}</strong>
      </div>
    </div>

    <div style="margin-top:20px;display:flex;justify-content:flex-end;">
      <button class="btn btn-secondary" onclick="closeModal()">Close</button>
    </div>
  `;

  modal.style.display = 'flex';
}

function closeModal() {
  const modal = document.getElementById('detail-modal');
  if (modal) modal.style.display = 'none';
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
