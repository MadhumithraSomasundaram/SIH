/**
 * Phase 17 — Analyst Interface: Audit Log Logic
 * Requires SUPERVISOR or ADMIN role.
 */
'use strict';

const AuditState = {
  items: [],
  total: 0,
  skip: 0,
  limit: 100,
  filters: { action: '', resource_type: '', result: '' },
};

async function loadAuditLog() {
  if (!Auth.hasRole('SUPERVISOR', 'ADMIN')) {
    document.getElementById('audit-tbody').innerHTML =
      `<tr><td colspan="7"><div class="empty-state">Access denied. Requires SUPERVISOR or ADMIN role.</div></td></tr>`;
    return;
  }
  const tbody = document.getElementById('audit-tbody');
  if (tbody) tbody.innerHTML = `<tr><td colspan="7"><div class="loading-overlay"><div class="spinner"></div></div></td></tr>`;

  try {
    const params = {
      skip: AuditState.skip,
      limit: AuditState.limit,
      ...Object.fromEntries(Object.entries(AuditState.filters).filter(([,v]) => v)),
    };
    const data = await Http.get('/audit', params);
    AuditState.items = data.items || [];
    AuditState.total = data.total || 0;
    renderAuditTable();
    renderAuditPagination();
    const countEl = document.getElementById('audit-count');
    if (countEl) countEl.textContent = `${AuditState.total} events`;
  } catch (err) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">${err.message}</div></td></tr>`;
    Toast.error('Failed to load audit log: ' + err.message);
  }
}

function renderAuditTable() {
  const tbody = document.getElementById('audit-tbody');
  if (!tbody) return;
  if (!AuditState.items.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">📋</div>No audit events found.</div></td></tr>`;
    return;
  }
  tbody.innerHTML = AuditState.items.map(a => `
    <tr>
      <td style="font-size:0.73rem;color:var(--text-muted);font-family:var(--font-mono)">${Fmt.datetime(a.timestamp)}</td>
      <td><span class="mono" style="font-size:0.78rem">${a.action || '—'}</span></td>
      <td>${a.resource_type || '—'}</td>
      <td class="mono" style="font-size:0.75rem">${a.resource_id || '—'}</td>
      <td><span class="user-badge ${a.actor_role || ''}" style="font-size:0.65rem">${a.actor_role || '—'}</span></td>
      <td>${resultBadge(a.result)}</td>
      <td style="font-size:0.75rem;color:var(--text-muted);max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${a.detail || ''}">${a.detail || '—'}</td>
    </tr>
  `).join('');
}

function resultBadge(result) {
  const cls = result === 'SUCCESS' ? 'badge-resolved' : result === 'FAILURE' ? 'badge-critical' : 'badge-moderate';
  return `<span class="badge ${cls}">${result || '—'}</span>`;
}

function renderAuditPagination() {
  const infoEl = document.getElementById('audit-page-info');
  const prevBtn = document.getElementById('audit-btn-prev');
  const nextBtn = document.getElementById('audit-btn-next');
  const page = Math.floor(AuditState.skip / AuditState.limit) + 1;
  const totalPages = Math.ceil(AuditState.total / AuditState.limit);
  if (infoEl) infoEl.textContent = `Page ${page} of ${totalPages} (${AuditState.total} total)`;
  if (prevBtn) prevBtn.disabled = AuditState.skip === 0;
  if (nextBtn) nextBtn.disabled = AuditState.skip + AuditState.limit >= AuditState.total;
}

function auditPrevPage() { if (AuditState.skip > 0) { AuditState.skip -= AuditState.limit; loadAuditLog(); } }
function auditNextPage() { if (AuditState.skip + AuditState.limit < AuditState.total) { AuditState.skip += AuditState.limit; loadAuditLog(); } }

function applyAuditFilters() {
  AuditState.filters.action        = document.getElementById('filter-action')?.value        || '';
  AuditState.filters.resource_type = document.getElementById('filter-resource-type')?.value || '';
  AuditState.filters.result        = document.getElementById('filter-result')?.value        || '';
  AuditState.skip = 0;
  loadAuditLog();
}

function clearAuditFilters() {
  ['filter-action','filter-resource-type','filter-result'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  AuditState.filters = { action:'', resource_type:'', result:'' };
  AuditState.skip = 0;
  loadAuditLog();
}
