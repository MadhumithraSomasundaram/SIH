/**
 * Phase 17 — Analyst Interface: Alert Management Logic
 * Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
 *
 * DISCLAIMER: Analytical signals only — not proof of criminal activity.
 * All HIGH and CRITICAL alerts require authorized human review.
 */
'use strict';

// ─── State ────────────────────────────────────────────────────────────────────
const AlertsState = {
  alerts: [],
  total: 0,
  skip: 0,
  limit: 50,
  selectedAlert: null,
  filters: {
    severity: '',
    status: '',
    alert_type: '',
    hotspot_id: '',
  },
  sort: { field: 'created_at', asc: false },
};

// ─── Load Alerts ──────────────────────────────────────────────────────────────
async function loadAlerts() {
  const tbody = document.getElementById('alerts-tbody');
  const countEl = document.getElementById('alerts-count');
  if (tbody) tbody.innerHTML = `<tr><td colspan="8"><div class="loading-overlay"><div class="spinner"></div></div></td></tr>`;

  try {
    const params = {
      skip: AlertsState.skip,
      limit: AlertsState.limit,
      ...Object.fromEntries(Object.entries(AlertsState.filters).filter(([,v]) => v)),
    };
    const data = await Http.get('/alerts', params);
    AlertsState.alerts = data.items || [];
    AlertsState.total = data.total || 0;

    renderAlertsTable();
    renderPagination();
    if (countEl) countEl.textContent = `${AlertsState.total} alerts`;
  } catch (err) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">⚠</div>${err.message}</div></td></tr>`;
    Toast.error('Failed to load alerts: ' + err.message);
  }
}

// ─── Render Table ──────────────────────────────────────────────────────────────
function renderAlertsTable() {
  const tbody = document.getElementById('alerts-tbody');
  if (!tbody) return;

  if (!AlertsState.alerts.length) {
    tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">📭</div>No alerts match the current filters.</div></td></tr>`;
    return;
  }

  tbody.innerHTML = AlertsState.alerts.map(a => `
    <tr data-alert-id="${a.alert_id || ''}" onclick="selectAlert('${a.alert_id}')">
      <td class="mono">${a.alert_id || '—'}</td>
      <td>${a.alert_type ? a.alert_type.replace(/_/g,' ') : '—'}</td>
      <td>${Fmt.riskBadge(a.severity)}</td>
      <td class="mono">${a.risk_score != null && !isNaN(Number(a.risk_score)) ? Math.round(Number(a.risk_score)) + '/100' : '—'}</td>
      <td class="mono">${a.hotspot_id || '—'}</td>
      <td style="font-size:0.75rem;color:var(--text-muted)">${Fmt.datetime(a.created_at)}</td>
      <td>${Fmt.statusBadge(a.status)}</td>
      <td style="text-align:center">${a.human_review_required ? '✓' : ''}</td>
    </tr>
  `).join('');
}

// ─── Select Alert ──────────────────────────────────────────────────────────────
async function selectAlert(alertId) {
  // Highlight row
  document.querySelectorAll('#alerts-tbody tr').forEach(r => r.classList.remove('selected'));
  const row = document.querySelector(`#alerts-tbody tr[data-alert-id="${alertId}"]`);
  if (row) row.classList.add('selected');

  const panel = document.getElementById('alert-detail-panel');
  if (panel) panel.style.display = '';

  try {
    const alert = await Http.get(`/alerts/${alertId}`);
    AlertsState.selectedAlert = alert;
    renderAlertDetail(alert);
  } catch (err) {
    Toast.error('Failed to load alert detail: ' + err.message);
  }
}

// ─── Render Alert Detail ───────────────────────────────────────────────────────
function renderAlertDetail(a) {
  const panel = document.getElementById('alert-detail-body');
  if (!panel) return;

  const sev = (a.severity || '').toLowerCase();
  panel.innerHTML = `
    <!-- Risk Gauge -->
    <div class="risk-gauge" style="margin-bottom:16px">
      <div class="risk-score-circle ${sev}">${a.risk_score ?? '—'}</div>
      <div class="risk-info">
        <div class="risk-category">${Fmt.riskBadge(a.severity)}</div>
        <div class="risk-prob" style="margin-top:6px">
          Predicted probability: ${Fmt.percent(a.predicted_probability)}
        </div>
        <div class="risk-note">
          ⚠ Authorized human review required
        </div>
      </div>
    </div>

    <!-- Core Fields -->
    ${field('Alert ID', `<span class="mono">${a.alert_id}</span>`)}
    ${field('Alert Type', (a.alert_type || '—').replace(/_/g,' '))}
    ${field('Status', Fmt.statusBadge(a.status))}
    ${field('Hotspot', a.hotspot_id || '—')}
    ${field('Event Count', a.event_count || '—')}
    ${field('Dominant Category', a.dominant_category || '—')}
    ${field('Time Window Start', Fmt.datetime(a.time_window_start))}
    ${field('Time Window End', Fmt.datetime(a.time_window_end))}
    ${field('Model Version', `<span class="mono" style="font-size:0.72rem">${a.model_version || '—'}</span>`)}
    ${field('Created At', Fmt.datetime(a.created_at))}

    <!-- Operational Message -->
    <div class="detail-field" style="margin-top:12px">
      <div class="detail-field-label">Operational Interpretation</div>
      <div style="font-size:0.82rem;color:var(--text-secondary);padding:10px;background:rgba(74,144,255,0.05);border-radius:var(--radius-md);border:1px solid var(--border-dim);margin-top:4px;line-height:1.6">
        ${a.operational_message || '—'}
      </div>
    </div>

    <!-- Disclaimer -->
    <div class="disclaimer-banner" style="margin-top:14px;margin-bottom:0">
      <strong>Model Disclaimer:</strong>
      This is a model-derived analytical signal and does not establish criminal activity.
    </div>

    <!-- Workflow Actions -->
    <div class="detail-section">
      <div class="detail-section-title">Alert Workflow</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn btn-sm btn-secondary" onclick="transitionAlert('${a.alert_id}','acknowledge')" id="btn-ack-${a.alert_id}">Acknowledge</button>
        <button class="btn btn-sm btn-secondary" onclick="transitionAlert('${a.alert_id}','review')" id="btn-review-${a.alert_id}">Mark In Review</button>
        <button class="btn btn-sm btn-success" onclick="transitionAlert('${a.alert_id}','resolve')" id="btn-resolve-${a.alert_id}">Resolve</button>
        <button class="btn btn-sm btn-danger" onclick="transitionAlert('${a.alert_id}','dismiss')" id="btn-dismiss-${a.alert_id}">Dismiss</button>
      </div>
      <div style="margin-top:12px">
        <button class="btn btn-primary btn-sm" onclick="openCreateInvestigation('${a.alert_id}')">
          + Create Investigation
        </button>
      </div>
    </div>
  `;
}

function field(label, value) {
  return `<div class="detail-field">
    <div class="detail-field-label">${label}</div>
    <div class="detail-field-value" style="font-size:0.82rem">${value}</div>
  </div>`;
}

// ─── Alert Status Transitions ─────────────────────────────────────────────────
async function transitionAlert(alertId, action) {
  const noteMap = {
    acknowledge: 'Alert acknowledged by authorized analyst.',
    review: 'Alert assigned to analytical review.',
    resolve: 'Alert resolved after authorized analytical review.',
    dismiss: 'Alert dismissed by authorized analyst.',
  };
  try {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/${action}`, {
      method: 'PATCH',
      headers: Auth.authHeaders(),
      body: JSON.stringify({ notes: noteMap[action] || '', actor_type: Auth.getRole() }),
    });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const j = await res.json();
        detail = j.detail || detail;
      } catch {}
      throw new Error(detail);
    }
    Toast.success(`Alert ${action}d successfully.`);
    loadAlerts();
    if (AlertsState.selectedAlert?.alert_id === alertId) {
      selectAlert(alertId);
    }
  } catch (err) {
    Toast.error(`Failed to ${action} alert: ` + err.message);
  }
}

// ─── Create Investigation Modal ────────────────────────────────────────────────
function openCreateInvestigation(alertId) {
  const modal = document.getElementById('create-inv-modal');
  const alertIdEl = document.getElementById('inv-alert-id');
  if (alertIdEl) alertIdEl.value = alertId;
  if (modal) modal.classList.add('visible');

  // Pre-fill priority from alert severity
  const alert = AlertsState.selectedAlert;
  if (alert) {
    const priorityEl = document.getElementById('inv-priority');
    if (priorityEl && alert.severity) priorityEl.value = alert.severity;
  }
}

async function submitCreateInvestigation() {
  const alertId = document.getElementById('inv-alert-id')?.value;
  const priority = document.getElementById('inv-priority')?.value || 'MODERATE';
  const note = document.getElementById('inv-initial-note')?.value || '';
  const btn = document.getElementById('btn-create-inv');

  if (!alertId) return;
  if (btn) { btn.disabled = true; btn.textContent = 'Creating…'; }

  try {
    const inv = await Http.post('/investigations', {
      alert_id: alertId,
      priority: priority,
      initial_note: note || null,
    });
    Toast.success(`Investigation ${inv.investigation_id} created successfully.`);
    document.getElementById('create-inv-modal').classList.remove('visible');
    // Navigate to investigation
    window.location.href = `/analyst/investigation.html?inv=${inv.investigation_id}`;
  } catch (err) {
    Toast.error('Failed to create investigation: ' + err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Create Investigation'; }
  }
}

// ─── Filters ──────────────────────────────────────────────────────────────────
function applyFilters() {
  AlertsState.filters.severity  = document.getElementById('filter-severity')?.value  || '';
  AlertsState.filters.status    = document.getElementById('filter-status')?.value    || '';
  AlertsState.filters.alert_type = document.getElementById('filter-type')?.value     || '';
  AlertsState.filters.hotspot_id = document.getElementById('filter-hotspot')?.value  || '';
  AlertsState.skip = 0;
  loadAlerts();
}

function clearFilters() {
  ['filter-severity','filter-status','filter-type','filter-hotspot'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  AlertsState.filters = { severity:'', status:'', alert_type:'', hotspot_id:'' };
  AlertsState.skip = 0;
  loadAlerts();
}

// ─── Pagination ────────────────────────────────────────────────────────────────
function renderPagination() {
  const infoEl = document.getElementById('page-info');
  const prevBtn = document.getElementById('btn-prev');
  const nextBtn = document.getElementById('btn-next');

  const page = Math.floor(AlertsState.skip / AlertsState.limit) + 1;
  const totalPages = Math.ceil(AlertsState.total / AlertsState.limit);

  if (infoEl) infoEl.textContent = `Page ${page} of ${totalPages} (${AlertsState.total} total)`;
  if (prevBtn) prevBtn.disabled = AlertsState.skip === 0;
  if (nextBtn) nextBtn.disabled = AlertsState.skip + AlertsState.limit >= AlertsState.total;
}

function prevPage() {
  if (AlertsState.skip > 0) {
    AlertsState.skip = Math.max(0, AlertsState.skip - AlertsState.limit);
    loadAlerts();
  }
}

function nextPage() {
  if (AlertsState.skip + AlertsState.limit < AlertsState.total) {
    AlertsState.skip += AlertsState.limit;
    loadAlerts();
  }
}
