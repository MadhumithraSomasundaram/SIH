/**
 * Phase 17 — Analyst Interface: Investigation Workspace Logic
 * Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
 */
'use strict';

// ─── State ────────────────────────────────────────────────────────────────────
const InvState = {
  investigations: [],
  total: 0,
  skip: 0,
  limit: 20,
  selected: null,
  filters: { status: '', priority: '' },
};

// ─── Load Investigations ───────────────────────────────────────────────────────
async function loadInvestigations() {
  const tbody = document.getElementById('inv-tbody');
  if (tbody) tbody.innerHTML = `<tr><td colspan="7"><div class="loading-overlay"><div class="spinner"></div></div></td></tr>`;

  try {
    const params = {
      skip: InvState.skip,
      limit: InvState.limit,
      ...Object.fromEntries(Object.entries(InvState.filters).filter(([,v]) => v)),
    };
    const data = await Http.get('/investigations', params);
    InvState.investigations = data.items || [];
    InvState.total = data.total || 0;
    renderInvTable();
    renderInvPagination();

    // Auto-select from URL param
    const urlParams = new URLSearchParams(window.location.search);
    const invId = urlParams.get('inv');
    if (invId) openInvestigation(invId);
  } catch (err) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">${err.message}</div></td></tr>`;
    Toast.error('Failed to load investigations: ' + err.message);
  }
}

function renderInvTable() {
  const tbody = document.getElementById('inv-tbody');
  if (!tbody) return;
  if (!InvState.investigations.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">📂</div>No investigations found. Create one from an alert.</div></td></tr>`;
    return;
  }
  tbody.innerHTML = InvState.investigations.map(inv => `
    <tr onclick="openInvestigation('${inv.investigation_id}')" data-inv-id="${inv.investigation_id}">
      <td class="mono" style="font-size:0.75rem">${inv.investigation_id}</td>
      <td class="mono">${inv.alert_id}</td>
      <td>${Fmt.statusBadge(inv.status)}</td>
      <td>${Fmt.riskBadge(inv.priority)}</td>
      <td>${Fmt.riskBadge(inv.severity)}</td>
      <td class="mono">${inv.risk_score != null ? inv.risk_score + '/100' : '—'}</td>
      <td style="font-size:0.75rem;color:var(--text-muted)">${Fmt.datetime(inv.created_at)}</td>
    </tr>
  `).join('');
}

function renderInvPagination() {
  const infoEl = document.getElementById('inv-page-info');
  const prevBtn = document.getElementById('inv-btn-prev');
  const nextBtn = document.getElementById('inv-btn-next');
  const page = Math.floor(InvState.skip / InvState.limit) + 1;
  const totalPages = Math.ceil(InvState.total / InvState.limit);
  if (infoEl) infoEl.textContent = `Page ${page} of ${totalPages} (${InvState.total} total)`;
  if (prevBtn) prevBtn.disabled = InvState.skip === 0;
  if (nextBtn) nextBtn.disabled = InvState.skip + InvState.limit >= InvState.total;
}

function invPrevPage() { if (InvState.skip > 0) { InvState.skip -= InvState.limit; loadInvestigations(); } }
function invNextPage() { if (InvState.skip + InvState.limit < InvState.total) { InvState.skip += InvState.limit; loadInvestigations(); } }

// ─── Open Investigation Detail ─────────────────────────────────────────────────
async function openInvestigation(invId) {
  document.querySelectorAll('#inv-tbody tr').forEach(r => r.classList.remove('selected'));
  const row = document.querySelector(`#inv-tbody tr[data-inv-id="${invId}"]`);
  if (row) row.classList.add('selected');

  const workspace = document.getElementById('workspace');
  if (workspace) workspace.style.display = '';
  const loadEl = document.getElementById('workspace-loading');
  if (loadEl) loadEl.style.display = '';
  const contentEl = document.getElementById('workspace-content');
  if (contentEl) contentEl.style.display = 'none';

  try {
    const detail = await Http.get(`/investigations/${invId}`);
    InvState.selected = detail;
    renderWorkspace(detail);
    if (loadEl) loadEl.style.display = 'none';
    if (contentEl) contentEl.style.display = '';
    // Update URL
    history.replaceState(null, '', `?inv=${invId}`);
  } catch (err) {
    if (loadEl) loadEl.innerHTML = `<div class="empty-state">${err.message}</div>`;
    Toast.error('Failed to load investigation: ' + err.message);
  }
}

// ─── Render Workspace ─────────────────────────────────────────────────────────
function renderWorkspace(d) {
  const inv = d.investigation || {};
  const notes = d.notes || [];
  const evidence = d.evidence || [];
  const timeline = d.timeline || [];
  const explanation = d.explanation || null;

  // Header
  const hdr = document.getElementById('ws-header');
  if (hdr) hdr.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
      <div>
        <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:4px">${inv.investigation_id || '—'}</h2>
        <div style="font-size:0.78rem;color:var(--text-muted)">Alert: <span class="mono">${inv.alert_id || '—'}</span> · Hotspot: ${inv.hotspot_id || '—'}</div>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        ${Fmt.statusBadge(inv.status)}
        ${Fmt.riskBadge(inv.priority)}
        <span style="font-size:0.72rem;color:var(--text-muted)">Created: ${Fmt.datetime(inv.created_at)}</span>
      </div>
    </div>
  `;

  // Risk Gauge
  const riskEl = document.getElementById('ws-risk');
  if (riskEl) {
    const sev = (inv.severity || '').toLowerCase();
    const prob = explanation?.predicted_probability;
    riskEl.innerHTML = `
      <div class="risk-gauge">
        <div class="risk-score-circle ${sev}">${inv.risk_score ?? '—'}</div>
        <div class="risk-info">
          <div class="risk-category">${Fmt.riskBadge(inv.severity || inv.priority)}</div>
          <div class="risk-prob">Predicted probability: ${prob != null ? Fmt.percent(prob) : '—'}</div>
          <div class="risk-note">Model Risk ≠ Investigation Priority. All signals require human review.</div>
        </div>
      </div>
    `;
  }

  // Update Status Controls
  const statusEl = document.getElementById('ws-status-controls');
  if (statusEl) {
    const current = inv.status;
    const transitions = {
      OPEN: ['UNDER_REVIEW','DISMISSED'],
      UNDER_REVIEW: ['PENDING_VALIDATION','DISMISSED'],
      PENDING_VALIDATION: ['CLOSED','DISMISSED','UNDER_REVIEW'],
    };
    const allowed = transitions[current] || [];
    const supervisorOnly = ['CLOSED','DISMISSED'];
    const role = Auth.getRole();
    statusEl.innerHTML = allowed.map(s => {
      const needsRole = supervisorOnly.includes(s);
      const disabled = needsRole && !Auth.hasRole('SUPERVISOR','ADMIN');
      const cls = s === 'DISMISSED' ? 'btn-danger' : s === 'CLOSED' ? 'btn-success' : 'btn-secondary';
      return `<button class="btn btn-sm ${cls}" ${disabled ? 'disabled title="Requires SUPERVISOR role"' : ''}
                onclick="updateInvStatus('${inv.investigation_id}','${s}')">
                → ${s.replace(/_/g,' ')}${needsRole ? ' (Supervisor)' : ''}
              </button>`;
    }).join('') || `<span style="font-size:0.78rem;color:var(--text-muted)">No further transitions available.</span>`;
  }

  // Notes
  renderNotes(notes);

  // Evidence
  renderEvidence(evidence);

  // Timeline
  renderTimeline(timeline);

  // SHAP Explanation
  renderExplanation(explanation);
}

// ─── Notes ────────────────────────────────────────────────────────────────────
function renderNotes(notes) {
  const el = document.getElementById('ws-notes');
  if (!el) return;
  if (!notes.length) {
    el.innerHTML = '<div style="font-size:0.82rem;color:var(--text-muted);">No notes recorded yet.</div>';
    return;
  }
  el.innerHTML = notes.map(n => `
    <div class="note-item fade-in">
      <div class="note-meta">
        <span>${Fmt.datetime(n.created_at)}</span>
        <span>${n.actor_role}</span>
      </div>
      <div class="note-text">${escHtml(n.note)}</div>
    </div>
  `).join('');
}

async function addNote() {
  const inv = InvState.selected?.investigation;
  if (!inv) return;
  const text = document.getElementById('note-text')?.value?.trim();
  if (!text) { Toast.error('Note text is required.'); return; }
  const btn = document.getElementById('btn-add-note');
  if (btn) { btn.disabled = true; btn.textContent = 'Adding…'; }
  try {
    await Http.post(`/investigations/${inv.investigation_id}/notes`, { note: text });
    document.getElementById('note-text').value = '';
    Toast.success('Note added.');
    const detail = await Http.get(`/investigations/${inv.investigation_id}`);
    InvState.selected = detail;
    renderNotes(detail.notes || []);
    renderTimeline(detail.timeline || []);
  } catch (err) {
    Toast.error('Failed to add note: ' + err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Add Note'; }
  }
}

// ─── Evidence ──────────────────────────────────────────────────────────────────
function renderEvidence(evidence) {
  const el = document.getElementById('ws-evidence');
  if (!el) return;
  if (!evidence.length) {
    el.innerHTML = '<div style="font-size:0.82rem;color:var(--text-muted);">No evidence references recorded yet.</div>';
    return;
  }
  el.innerHTML = evidence.map(e => `
    <div class="evidence-item fade-in">
      <div class="evidence-type">${e.evidence_type}</div>
      <div class="evidence-ref">${escHtml(e.reference)}</div>
      ${e.description ? `<div class="evidence-desc">${escHtml(e.description)}</div>` : ''}
      ${e.integrity_hash ? `<div class="evidence-hash">Integrity ref: ${escHtml(e.integrity_hash)}</div>` : ''}
      <div style="font-size:0.65rem;color:var(--text-dim);margin-top:6px">${Fmt.datetime(e.created_at)} · ${e.created_by_role}</div>
    </div>
  `).join('');
}

async function addEvidence() {
  const inv = InvState.selected?.investigation;
  if (!inv) return;
  const type = document.getElementById('ev-type')?.value;
  const ref = document.getElementById('ev-reference')?.value?.trim();
  const desc = document.getElementById('ev-description')?.value?.trim();
  const hash = document.getElementById('ev-hash')?.value?.trim();

  if (!type || !ref) { Toast.error('Evidence type and reference are required.'); return; }
  const btn = document.getElementById('btn-add-evidence');
  if (btn) { btn.disabled = true; btn.textContent = 'Adding…'; }
  try {
    await Http.post(`/investigations/${inv.investigation_id}/evidence`, {
      evidence_type: type,
      reference: ref,
      description: desc || null,
      integrity_hash: hash || null,
    });
    ['ev-reference','ev-description','ev-hash'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    Toast.success('Evidence reference added. (Integrity verification reference only — does not prove authenticity.)');
    const detail = await Http.get(`/investigations/${inv.investigation_id}`);
    InvState.selected = detail;
    renderEvidence(detail.evidence || []);
    renderTimeline(detail.timeline || []);
  } catch (err) {
    Toast.error('Failed to add evidence: ' + err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Add Reference'; }
  }
}

// ─── Timeline ──────────────────────────────────────────────────────────────────
function renderTimeline(timeline) {
  const el = document.getElementById('ws-timeline');
  if (!el) return;
  if (!timeline.length) {
    el.innerHTML = '<div style="font-size:0.82rem;color:var(--text-muted);">No timeline events yet.</div>';
    return;
  }
  const roleClass = r => r === 'SYSTEM' ? 'system' : r === 'SUPERVISOR' ? 'supervisor' : '';
  el.innerHTML = `<div class="timeline">` + timeline.map(t => `
    <div class="timeline-item">
      <div class="timeline-dot ${roleClass(t.actor_role)}"></div>
      <div class="timeline-time">${Fmt.datetime(t.timestamp)}</div>
      <div class="timeline-event">${t.event_type.replace(/_/g,' ')}</div>
      <div class="timeline-desc">${escHtml(t.description)}</div>
      <span class="timeline-role">${t.actor_role}</span>
    </div>
  `).join('') + `</div>`;
}

// ─── SHAP Explanation ──────────────────────────────────────────────────────────
function renderExplanation(exp) {
  const el = document.getElementById('ws-explanation');
  if (!el) return;
  if (!exp || !exp.top_features || !exp.top_features.length) {
    el.innerHTML = '<div style="font-size:0.82rem;color:var(--text-muted);">SHAP explanation data not available.</div>';
    return;
  }
  const maxVal = Math.max(...exp.top_features.map(f => f.mean_abs_shap_value));
  el.innerHTML = `
    <div class="disclaimer-banner" style="margin-bottom:14px">
      <strong>Model Explanation Disclaimer:</strong>
      Model explanations describe factors contributing to the model's prediction.
      They do not establish causality or criminal responsibility.
    </div>
    ${exp.top_features.map(f => {
      const pct = maxVal > 0 ? (f.mean_abs_shap_value / maxVal * 100) : 0;
      const isPos = f.direction.includes('higher');
      return `
        <div class="shap-feature">
          <div class="shap-feature-header">
            <span class="shap-feature-name">${f.rank}. ${f.human_label}</span>
            <span class="shap-feature-value">${f.mean_abs_shap_value.toFixed(4)}</span>
          </div>
          <div class="shap-bar-track">
            <div class="shap-bar-fill ${isPos ? 'positive' : 'negative'}" style="width:${pct.toFixed(1)}%"></div>
          </div>
          <div class="shap-direction ${isPos ? 'positive' : 'negative'}">${f.direction}</div>
        </div>
      `;
    }).join('')}
  `;
}

// ─── Status Update ─────────────────────────────────────────────────────────────
async function updateInvStatus(invId, newStatus) {
  const btn = event.target;
  if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; }
  try {
    await Http.patch(`/investigations/${invId}`, { status: newStatus });
    Toast.success(`Investigation status updated to ${newStatus}.`);
    const detail = await Http.get(`/investigations/${invId}`);
    InvState.selected = detail;
    renderWorkspace(detail);
    loadInvestigations(); // refresh list
  } catch (err) {
    Toast.error('Failed to update status: ' + err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = `→ ${newStatus}`; }
  }
}

// ─── Filters ───────────────────────────────────────────────────────────────────
function applyInvFilters() {
  InvState.filters.status   = document.getElementById('inv-filter-status')?.value   || '';
  InvState.filters.priority = document.getElementById('inv-filter-priority')?.value || '';
  InvState.skip = 0;
  loadInvestigations();
}
function clearInvFilters() {
  ['inv-filter-status','inv-filter-priority'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  InvState.filters = { status:'', priority:'' };
  InvState.skip = 0;
  loadInvestigations();
}

// ─── Summary / Export ──────────────────────────────────────────────────────────
function showSummary() {
  const d = InvState.selected;
  if (!d) { Toast.info('Select an investigation first.'); return; }
  const inv = d.investigation || {};
  const notes = d.notes || [];
  const evidence = d.evidence || [];
  const exp = d.explanation || null;

  const modal = document.getElementById('summary-modal');
  const body = document.getElementById('summary-body');
  if (!modal || !body) return;

  body.innerHTML = `
    <div class="disclaimer-banner disclaimer-warning" style="margin-bottom:16px">
      <strong>SYNTHETIC DEMONSTRATION DATA</strong> — Not real banking or NCRP records.
    </div>
    <div class="summary-section">
      <h4>Investigation Information</h4>
      <ul class="summary-list">
        <li><strong>ID:</strong> ${inv.investigation_id}</li>
        <li><strong>Alert ID:</strong> ${inv.alert_id}</li>
        <li><strong>Status:</strong> ${inv.status}</li>
        <li><strong>Priority:</strong> ${inv.priority}</li>
        <li><strong>Created:</strong> ${Fmt.datetime(inv.created_at)}</li>
      </ul>
    </div>
    <div class="summary-section">
      <h4>Analytical Findings</h4>
      <ul class="summary-list">
        <li><strong>Model Risk Score:</strong> ${inv.risk_score ?? '—'}/100</li>
        <li><strong>Alert Severity:</strong> ${inv.severity ?? '—'}</li>
        <li><strong>Dominant Category:</strong> ${inv.dominant_category ?? '—'}</li>
        <li><strong>Hotspot ID:</strong> ${inv.hotspot_id ?? 'N/A'}</li>
      </ul>
    </div>
    ${exp ? `<div class="summary-section">
      <h4>Model Explanation (Top Features)</h4>
      <ul class="summary-list">
        ${exp.top_features.slice(0,5).map(f => `<li>${f.human_label}: ${f.direction}</li>`).join('')}
      </ul>
    </div>` : ''}
    <div class="summary-section">
      <h4>Recorded Review</h4>
      <ul class="summary-list">
        <li>${notes.length} analyst note(s) recorded.</li>
        <li>${evidence.length} evidence reference(s) recorded.</li>
        ${inv.review_summary ? `<li>Review summary: ${escHtml(inv.review_summary)}</li>` : ''}
        ${inv.recommended_next_step ? `<li>Next step: ${escHtml(inv.recommended_next_step)}</li>` : ''}
      </ul>
    </div>
    <div class="summary-section">
      <h4>Conclusion</h4>
      <p style="font-size:0.82rem;color:var(--text-muted);">Analytical review completed.</p>
      <div class="disclaimer-banner" style="margin-top:10px">
        This analytical review does not automatically establish criminal activity.
        Operational decisions require authorized human review, supporting evidence,
        and applicable governance procedures.
      </div>
    </div>
  `;
  modal.classList.add('visible');
}

function exportSummaryJSON() {
  const d = InvState.selected;
  if (!d) return;
  const safe = {
    investigation_id: d.investigation?.investigation_id,
    alert_id: d.investigation?.alert_id,
    status: d.investigation?.status,
    priority: d.investigation?.priority,
    risk_score: d.investigation?.risk_score,
    severity: d.investigation?.severity,
    dominant_category: d.investigation?.dominant_category,
    notes_count: (d.notes || []).length,
    evidence_count: (d.evidence || []).length,
    disclaimer: 'SYNTHETIC DEMONSTRATION DATA. Analytical review only — not proof of criminal activity.',
    exported_at: new Date().toISOString(),
  };
  const blob = new Blob([JSON.stringify(safe, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url;
  a.download = `investigation_${safe.investigation_id}_summary.json`;
  a.click(); URL.revokeObjectURL(url);
  Toast.success('Investigation summary exported (safe analytical data only).');
}

// ─── Intelligence Brief (Phase 6) ─────────────────────────────────────────────
let _currentBriefData = null;

async function loadIntelligenceBrief(force = false) {
  const inv = InvState.selected?.investigation;
  if (!inv) return;
  const container = document.getElementById('ws-brief-content');
  if (!container) return;

  if (!force && _currentBriefData && _currentBriefData.investigation_id === inv.investigation_id) {
    renderBriefContent(_currentBriefData);
    return;
  }

  container.innerHTML = '<div style="padding:20px;text-align:center"><div class="spinner"></div><span style="font-size:0.8rem;color:var(--text-muted);margin-left:8px">Compiling official intelligence brief…</span></div>';

  try {
    const brief = await Http.get(`/investigations/${inv.investigation_id}/intelligence-brief`);
    _currentBriefData = brief;
    renderBriefContent(brief);
  } catch (err) {
    container.innerHTML = `<div class="disclaimer-banner" style="border-color:var(--accent-red);color:var(--accent-red)">Failed compiling intelligence brief: ${escHtml(err.message)}</div>`;
  }
}

function renderBriefContent(b) {
  const container = document.getElementById('ws-brief-content');
  if (!container) return;
  const sp = b.spatial_intelligence || {};
  const atms = sp.top_nearby_atms || [];
  const shaps = b.shap_explainability || [];

  container.innerHTML = `
    <div style="background:var(--bg-card);border:1px solid var(--border-dim);border-radius:8px;padding:16px;margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid var(--border-dim);padding-bottom:10px;margin-bottom:12px">
        <div>
          <div style="font-size:0.75rem;color:var(--text-dim);letter-spacing:1px;text-transform:uppercase">Intelligence Dossier Ref</div>
          <div style="font-size:1.1rem;font-weight:700;color:var(--accent-blue)">${escHtml(b.brief_reference)}</div>
        </div>
        <div style="text-align:right">
          <span class="badge badge-${(b.status || '').toLowerCase()}">${b.status}</span>
          <span class="badge badge-${(b.priority || '').toLowerCase()}">${b.priority} Priority</span>
          <div style="font-size:0.7rem;color:var(--text-dim);margin-top:4px">${Fmt.datetime(b.generated_at)}</div>
        </div>
      </div>

      <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(160px, 1fr));gap:10px;margin-bottom:16px">
        <div class="kpi-card" style="padding:10px">
          <div class="kpi-label">Predicted Risk Score</div>
          <div class="kpi-val" style="color:var(--accent-red)">${b.risk_score ?? '—'}<span style="font-size:0.8rem;color:var(--text-muted)">/100</span></div>
          <div style="font-size:0.65rem;color:var(--text-muted)">Prob: ${b.predicted_probability ? (b.predicted_probability * 100).toFixed(1) + '%' : '—'}</div>
        </div>
        <div class="kpi-card" style="padding:10px">
          <div class="kpi-label">Hotspot Spatial Cluster</div>
          <div class="kpi-val" style="color:var(--accent-cyan)">${escHtml(sp.hotspot_id || 'N/A')}</div>
          <div style="font-size:0.65rem;color:var(--text-muted)">${escHtml(sp.assigned_district || 'Regional')}</div>
        </div>
        <div class="kpi-card" style="padding:10px">
          <div class="kpi-label">Physical ATMs (5 km)</div>
          <div class="kpi-val" style="color:var(--accent-amber)">${sp.atms_within_5km ?? 0}</div>
          <div style="font-size:0.65rem;color:var(--text-muted)">Nearest: ${sp.nearest_atm_distance_km ? sp.nearest_atm_distance_km + ' km' : '—'}</div>
        </div>
        <div class="kpi-card" style="padding:10px">
          <div class="kpi-label">Loss Amount</div>
          <div class="kpi-val" style="color:var(--text-primary)">${b.fraud_amount ? '₹' + Number(b.fraud_amount).toLocaleString('en-IN') : '—'}</div>
          <div style="font-size:0.65rem;color:var(--text-muted)">${escHtml(b.crime_category || 'FRAUD')}</div>
        </div>
      </div>

      <!-- Spatial & ATM Proximity -->
      <div style="margin-bottom:16px">
        <div style="font-size:0.8rem;font-weight:600;color:var(--text-primary);margin-bottom:8px">📍 Estimated High-Risk Cashout Corridor & Physical ATM Proximity</div>
        <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:8px">
          Cluster Centroid: <strong>${sp.centroid_latitude ?? '—'}°N, ${sp.centroid_longitude ?? '—'}°E</strong> | 
          Nearest ATM: <strong>${escHtml(sp.nearest_atm_id || 'N/A')}</strong> (${escHtml(sp.nearest_atm_bank || 'Bank')}, ${sp.nearest_atm_distance_km ? sp.nearest_atm_distance_km + ' km' : '—'})
        </div>
        <div style="font-size:0.72rem;color:var(--text-dim);background:rgba(255,255,255,0.02);padding:6px 8px;border-radius:4px;border:1px solid var(--border-dim);margin-bottom:8px">
          ⚠️ <strong>Analytical Notice:</strong> Cashout corridors and ATM proximity represent estimated spatial risk areas derived from historical DBSCAN clustering and model risk scores. They do NOT predict exact criminal whereabouts or guarantee cashout occurrence.
        </div>
        ${atms.length ? `
          <div class="table-wrapper">
            <table>
              <thead><tr><th>ATM ID</th><th>Bank Network</th><th>Proximity (km)</th><th>Type</th><th>24x7</th></tr></thead>
              <tbody>
                ${atms.map(a => `<tr>
                  <td><code>${escHtml(a.atm_id)}</code></td>
                  <td>${escHtml(a.bank_id)}</td>
                  <td><strong>${a.distance_km} km</strong></td>
                  <td>${escHtml(a.atm_type)}</td>
                  <td>${a.is_24x7 ? '✅ Yes' : '❌ No'}</td>
                </tr>`).join('')}
              </tbody>
            </table>
          </div>
        ` : '<div style="font-size:0.75rem;color:var(--text-muted)">No ATM records within threshold range.</div>'}
      </div>

      <!-- Top Model Explanations (SHAP) -->
      <div style="margin-bottom:16px">
        <div style="font-size:0.8rem;font-weight:600;color:var(--text-primary);margin-bottom:8px">🧠 Primary Predictive Model Drivers (SHAP)</div>
        ${shaps.length ? `
          <div class="table-wrapper">
            <table>
              <thead><tr><th>Feature</th><th>Human Label</th><th>Contribution</th><th>Impact</th></tr></thead>
              <tbody>
                ${shaps.slice(0, 5).map(f => `<tr>
                  <td><code>${escHtml(f.feature)}</code></td>
                  <td>${escHtml(f.human_label || f.feature)}</td>
                  <td><span class="badge badge-${String(f.contribution).includes('higher') ? 'critical' : 'low'}">${escHtml(f.contribution)}</span></td>
                  <td>${Number(f.impact_score).toFixed(4)}</td>
                </tr>`).join('')}
              </tbody>
            </table>
          </div>
        ` : '<div style="font-size:0.75rem;color:var(--text-muted)">Model explanations pending review.</div>'}
      </div>

      <!-- Evidence & Audit -->
      <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--border-dim);padding-top:10px;font-size:0.7rem;color:var(--text-dim)">
        <div>Audit Trail Ref: <code>${escHtml(b.audit_trail_reference)}</code> | Notes: ${b.analyst_notes_count} recorded</div>
        <div>Authorized Officer Role: <strong>${escHtml(b.generated_by_role)}</strong></div>
      </div>
    </div>
  `;
}

function exportIntelligenceBriefJSON() {
  if (!_currentBriefData) {
    Toast.error('Please generate/load the intelligence brief first.');
    return;
  }
  const blob = new Blob([JSON.stringify(_currentBriefData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url;
  a.download = `${_currentBriefData.brief_reference}.json`;
  a.click(); URL.revokeObjectURL(url);
  Toast.success('Intelligence brief exported as JSON.');
}

// ─── Outcome Feedback (Phase 11) ─────────────────────────────────────────────
async function loadOutcomesTab() {
  const inv = InvState.selected?.investigation;
  if (!inv) return;
  const listEl = document.getElementById('ws-outcomes-list');
  if (!listEl) return;
  listEl.innerHTML = '<div style="font-size:0.82rem;color:var(--text-muted);">Loading field outcomes…</div>';

  try {
    const outcomes = await Http.get(`/investigations/${inv.investigation_id}/outcomes`);
    renderOutcomesList(outcomes);
  } catch (err) {
    listEl.innerHTML = `<div style="font-size:0.82rem;color:var(--text-muted);">Failed to load outcomes: ${escHtml(err.message)}</div>`;
  }
}

function renderOutcomesList(outcomes) {
  const listEl = document.getElementById('ws-outcomes-list');
  if (!listEl) return;
  if (!outcomes || !outcomes.length) {
    listEl.innerHTML = '<div style="font-size:0.82rem;color:var(--text-muted);">No outcome feedback recorded yet for this investigation.</div>';
    return;
  }
  listEl.innerHTML = outcomes.map(o => {
    const isThwarted = o.outcome_category === 'THWARTED_CASHOUT';
    const isConfirmed = o.outcome_category === 'CONFIRMED_CASHOUT';
    const badgeClass = isThwarted ? 'badge-low' : (isConfirmed ? 'badge-critical' : 'badge-moderate');
    
    return `
      <div class="note-item fade-in" style="margin-bottom:10px;padding:12px;background:var(--bg-card);border:1px solid var(--border-dim);border-radius:6px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <div style="display:flex;align-items:center;gap:8px;">
            <span class="badge ${badgeClass}">${escHtml(o.outcome_category)}</span>
            <span style="font-size:0.75rem;color:var(--text-muted);">${Fmt.datetime(o.created_at)}</span>
          </div>
          <div style="font-size:0.75rem;color:var(--text-dim);">
            Officer: <strong>${escHtml(o.reported_by_role)}</strong>
            ${o.verified_by_supervisor ? ' · <span style="color:var(--accent-green);">✔ Verified</span>' : ''}
          </div>
        </div>
        <div style="font-size:0.82rem;margin-bottom:6px;">${escHtml(o.notes)}</div>
        <div style="font-size:0.75rem;color:var(--text-muted);display:flex;gap:16px;">
          ${o.amount_prevented ? `<span>💰 Prevented: <strong style="color:var(--accent-green)">₹${Number(o.amount_prevented).toLocaleString('en-IN')}</strong></span>` : ''}
          ${o.actual_amount_lost ? `<span>⚠ Actual Loss: <strong style="color:var(--accent-red)">₹${Number(o.actual_amount_lost).toLocaleString('en-IN')}</strong></span>` : ''}
          ${o.atm_id_actual ? `<span>📍 ATM: <code>${escHtml(o.atm_id_actual)}</code></span>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

async function submitOutcomeFeedback() {
  const inv = InvState.selected?.investigation;
  if (!inv) {
    Toast.error('No investigation selected.');
    return;
  }
  const category = document.getElementById('outcome-category')?.value;
  const notes = document.getElementById('outcome-notes')?.value?.trim();
  const preventedStr = document.getElementById('outcome-prevented')?.value;
  const lostStr = document.getElementById('outcome-lost')?.value;
  const atm = document.getElementById('outcome-atm')?.value?.trim();

  if (!notes || notes.length < 5) {
    Toast.error('Please enter detailed patrol/intervention notes (minimum 5 characters).');
    return;
  }

  const payload = {
    outcome_category: category,
    notes: notes,
    amount_prevented: preventedStr ? parseFloat(preventedStr) : null,
    actual_amount_lost: lostStr ? parseFloat(lostStr) : null,
    atm_id_actual: atm || null,
  };

  const btn = document.getElementById('btn-add-outcome');
  if (btn) { btn.disabled = true; btn.textContent = 'Recording…'; }

  try {
    await Http.post(`/investigations/${inv.investigation_id}/outcomes`, payload);
    Toast.success('Operational outcome successfully recorded.');
    
    // Clear form
    document.getElementById('outcome-notes').value = '';
    document.getElementById('outcome-prevented').value = '';
    document.getElementById('outcome-lost').value = '';
    document.getElementById('outcome-atm').value = '';

    // Reload outcomes and investigation timeline
    await loadOutcomesTab();
    const detail = await Http.get(`/investigations/${inv.investigation_id}`);
    InvState.selected = detail;
    renderTimeline(detail.timeline || []);
  } catch (err) {
    Toast.error('Failed to record outcome: ' + err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🎯 Record Operational Outcome'; }
  }
}

// ─── Utility ──────────────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

