/**
 * Phase 16 & SIH Polish — Alerts Subsystem Frontend Controller
 * Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
 *
 * Implements real-time alert triage, detail inspection, human review enforcement,
 * lifecycle state transitions (Acknowledge, Start Investigation, Dismiss),
 * and dynamic workflow stepper synchronization.
 */

'use strict';

let alertsData = [];
let alertLayerGroup = null;

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  initAlertsSystem();
});

function initAlertsSystem() {
  loadAlertStatistics();
  loadRecentAlerts();

  const btnGen = document.getElementById("btn-generate-alerts");
  if (btnGen) {
    btnGen.addEventListener("click", () => triggerAlertGeneration());
  }

  const btnClose = document.getElementById("alert-detail-close");
  if (btnClose) {
    btnClose.addEventListener("click", () => closeAlertDetail());
  }

  // Setup layer toggle
  const layerToggle = document.getElementById("layer-alerts");
  if (layerToggle) {
    layerToggle.addEventListener("change", (e) => {
      toggleAlertLayer(e.target.checked);
    });
  }
}

async function loadAlertStatistics() {
  try {
    const res = await fetch("/alerts/statistics");
    if (!res.ok) return;
    const stats = await res.json();

    const totalEl = document.getElementById("alert-total-cnt");
    const critEl = document.getElementById("alert-crit-cnt");
    const highEl = document.getElementById("alert-high-cnt");
    const modEl  = document.getElementById("alert-mod-cnt");
    const newEl  = document.getElementById("alert-new-cnt");
    const revEl  = document.getElementById("alert-rev-cnt");

    if (totalEl) totalEl.textContent = stats.total_alerts || 0;
    if (critEl) critEl.textContent = stats.critical_alerts || 0;
    if (highEl) highEl.textContent = stats.high_alerts || 0;
    if (modEl)  modEl.textContent  = (stats.total_alerts - stats.critical_alerts - stats.high_alerts) || 0;
    if (newEl)  newEl.textContent  = stats.new_alerts || 0;
    if (revEl)  revEl.textContent  = stats.in_review_alerts || 0;
  } catch (err) {
    console.warn("Failed to load alert statistics:", err);
  }
}

async function loadRecentAlerts() {
  const feed = document.getElementById("alerts-feed");
  if (!feed) return;

  try {
    const res = await fetch("/alerts?limit=30");
    if (!res.ok) {
      feed.innerHTML = `<div class="error-text">Data service unavailable.</div>`;
      return;
    }
    const data = await res.json();
    alertsData = data.items || [];

    if (alertsData.length === 0) {
      feed.innerHTML = `<div class="loading-text">No records match the selected filters. Click "Generate Alerts" to evaluate.</div>`;
      return;
    }

    feed.innerHTML = `
      <div class="table-responsive">
        <table class="alerts-table">
          <thead>
            <tr>
              <th>Alert ID</th>
              <th>Type</th>
              <th>Severity</th>
              <th>Risk Score</th>
              <th>Hotspot ID</th>
              <th>Created Time</th>
              <th>Status</th>
              <th style="text-align:right;">Actions</th>
            </tr>
          </thead>
          <tbody id="alerts-table-body"></tbody>
        </table>
      </div>
    `;

    const tbody = feed.querySelector("#alerts-table-body");
    alertsData.forEach((a) => {
      const row = createAlertTableRow(a);
      tbody.appendChild(row);
    });

    renderAlertMapLayer(alertsData);
  } catch (err) {
    feed.innerHTML = `<div class="error-text">Data service unavailable.</div>`;
    console.warn("Failed to load alerts feed:", err);
  }
}

function createAlertTableRow(a) {
  const tr = document.createElement("tr");
  const sev = (a.severity || "MODERATE").toUpperCase();
  const sevClass = (a.severity || "low").toLowerCase();
  tr.className = `alert-table-row sev-${sevClass}`;

  const createdTime = a.created_at ? a.created_at.replace("T", " ").slice(0, 16) : "Recent";
  const riskScore = a.risk_score !== null && a.risk_score !== undefined ? `${a.risk_score}` : "—";
  const badgeClass = sev === "CRITICAL" ? "badge-crit" : (sev === "HIGH" ? "badge-high" : (sev === "MODERATE" ? "badge-mod" : "badge-low"));
  const hotspotIdText = a.hotspot_id ? `HS-${a.hotspot_id}` : (a.latitude ? `${a.latitude.toFixed(2)}°N` : 'Unassigned');

  function getRiskColor(score) {
    if (score === null || score === undefined) return "#94A3B8";
    if (score >= 80) return "#EF4444";
    if (score >= 60) return "#FB923C";
    if (score >= 40) return "#FACC15";
    return "#22C55E";
  }

  tr.innerHTML = `
    <td><span class="font-mono alert-table-id">${a.alert_id}</span></td>
    <td><span class="alert-table-type">${formatAlertType(a.alert_type)}</span></td>
    <td><span class="alert-badge ${badgeClass}">${sev}</span></td>
    <td><span class="font-mono font-bold" style="color:${getRiskColor(a.risk_score)}">${riskScore} <small style="color:var(--text-dim)">/ 100</small></span></td>
    <td><span class="font-mono alert-hs-cell">${hotspotIdText}</span></td>
    <td><span class="alert-table-time">${createdTime}</span></td>
    <td><span class="status-chip ${a.status}">${a.status}</span></td>
    <td style="text-align:right;">
      <button class="btn btn-sm btn-outline btn-inspect-alert" title="View details and operational triage actions">View Alert →</button>
    </td>
  `;

  tr.querySelector(".btn-inspect-alert")?.addEventListener("click", (e) => {
    e.stopPropagation();
    openAlertDetail(a.alert_id);
  });
  tr.addEventListener("click", () => openAlertDetail(a.alert_id));

  return tr;
}

function formatAlertType(typeStr) {
  if (!typeStr) return "ANALYTICAL ALERT";
  return typeStr.replace(/_/g, " ");
}

function updateWorkflowStepper(status) {
  const stepMap = {
    NEW: "wf-step-new",
    ACKNOWLEDGED: "wf-step-ack",
    IN_REVIEW: "wf-step-rev",
    UNDER_REVIEW: "wf-step-rev",
    PENDING_VALIDATION: "wf-step-val",
    RESOLVED: "wf-step-res",
    DISMISSED: "wf-step-res",
  };

  document.querySelectorAll(".wf-step").forEach(el => el.classList.remove("active"));
  const targetId = stepMap[status] || "wf-step-new";
  const targetEl = document.getElementById(targetId);
  if (targetEl) targetEl.classList.add("active");
}

async function openAlertDetail(alertId) {
  const panel = document.getElementById("alert-detail-panel");
  const body = document.getElementById("alert-detail-body");
  if (!panel || !body) return;

  const titleEl = document.getElementById("alert-detail-title");
  if (titleEl) titleEl.textContent = `ALERT DETAILS · ${alertId}`;
  body.innerHTML = `<div class="loading-text">Loading alert ${alertId}…</div>`;
  panel.classList.add("active");

  try {
    const res = await fetch(`/alerts/${alertId}`);
    if (!res.ok) throw new Error("Alert not found");
    const a = await res.json();

    updateWorkflowStepper(a.status);

    const sevClass = (a.severity || "low").toLowerCase();
    const badgeClass = a.severity === "CRITICAL" ? "badge-crit" : (a.severity === "HIGH" ? "badge-high" : "badge-mod");

    body.innerHTML = `
      <div class="alert-callout-banner">
        <span>⚠</span>
        <div><strong>Analytical Alert — Authorized Human Review Required</strong><br>
        This signal is model-derived and requires operational validation before any intervention.</div>
      </div>

      <div class="detail-row"><span class="detail-k">Alert ID:</span><span class="detail-v font-mono">${a.alert_id || 'Not available'}</span></div>
      <div class="detail-row"><span class="detail-k">Alert Type:</span><span class="detail-v">${formatAlertType(a.alert_type)}</span></div>
      <div class="detail-row"><span class="detail-k">Severity:</span><span class="detail-v"><span class="alert-badge ${badgeClass}">${a.severity || 'Not available'}</span></span></div>
      <div class="detail-row"><span class="detail-k">Status:</span><span class="detail-v font-mono">${a.status || 'Not available'}</span></div>
      <div class="detail-row"><span class="detail-k">Risk Score:</span><span class="detail-v font-mono font-bold">${a.risk_score !== null && a.risk_score !== undefined ? `${a.risk_score} / 100` : 'Not available'}</span></div>
      <div class="detail-row"><span class="detail-k">Predicted Probability:</span><span class="detail-v font-mono">${a.predicted_probability !== null && a.predicted_probability !== undefined ? Number(a.predicted_probability).toFixed(4) : "Not available"}</span></div>
      <div class="detail-row"><span class="detail-k">Hotspot ID:</span><span class="detail-v font-mono">${a.hotspot_id ? 'HS-' + a.hotspot_id : "Not available"}</span></div>
      <div class="detail-row"><span class="detail-k">Event Count:</span><span class="detail-v">${a.event_count || 1}</span></div>
      <div class="detail-row"><span class="detail-k">Dominant Category:</span><span class="detail-v">${a.dominant_category || "Not available"}</span></div>
      <div class="detail-row"><span class="detail-k">Created Time:</span><span class="detail-v">${a.created_at ? a.created_at.replace("T", " ").slice(0, 19) : "Not available"}</span></div>
      <div class="detail-row"><span class="detail-k">Human Review Required:</span><span class="detail-v" style="color:#ff7b72;font-weight:600;">Yes — Mandatory Human Review</span></div>

      <div style="margin-top:10px;">
        <div class="detail-k" style="margin-bottom:3px;">Operational Interpretation:</div>
        <div style="font-size:11px; color:var(--text-primary); background:var(--bg-card); padding:8px 10px; border-radius:4px; border:1px solid var(--border-subtle); line-height:1.4;">
          ${a.operational_message || "Model-derived risk signal indicating elevated future cash withdrawal likelihood. Review local patterns and verify corroborating evidence."}
        </div>
      </div>

      <div class="alert-action-btn-group">
        ${a.status === "NEW" ? `<button class="btn btn-xs btn-ack" onclick="transitionAlert('${a.alert_id}', 'acknowledge')">ACKNOWLEDGE</button>` : ""}
        ${(a.status === "NEW" || a.status === "ACKNOWLEDGED") ? `<button class="btn btn-xs btn-rev" onclick="startAlertInvestigation('${a.alert_id}')">START INVESTIGATION ↗</button>` : ""}
        ${a.status === "IN_REVIEW" ? `<button class="btn btn-xs btn-res" onclick="transitionAlert('${a.alert_id}', 'resolve')">RESOLVE</button>` : ""}
        ${a.status !== "RESOLVED" && a.status !== "DISMISSED" ? `<button class="btn btn-xs btn-dis" onclick="transitionAlert('${a.alert_id}', 'dismiss')">DISMISS</button>` : ""}
      </div>
    `;

    // Highlight on map if coordinates exist
    if (a.latitude && a.longitude && window.mapInstance) {
      window.mapInstance.flyTo([a.latitude, a.longitude], 12, { duration: 1.2 });
    }
  } catch (err) {
    body.innerHTML = `<div class="error-text">Error: ${err.message}</div>`;
  }
}

function closeAlertDetail() {
  const panel = document.getElementById("alert-detail-panel");
  if (panel) panel.classList.remove("active");
}

async function transitionAlert(alertId, actionName) {
  try {
    const res = await fetch(`/alerts/${alertId}/${actionName}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor_type: "AUTHORIZED_USER", notes: `Action ${actionName} applied via Dashboard` }),
    });

    if (!res.ok) {
      const err = await res.json();
      alert(`Transition error: ${err.detail || "Action disallowed"}`);
      return;
    }

    loadAlertStatistics();
    loadRecentAlerts();
    openAlertDetail(alertId);
  } catch (err) {
    alert("Network error updating alert status.");
  }
}

async function startAlertInvestigation(alertId) {
  try {
    // 1. Move to IN_REVIEW status
    await fetch(`/alerts/${alertId}/review`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor_type: "AUTHORIZED_ANALYST", notes: `Investigation initiated via Dashboard` }),
    });

    // 2. Open Investigation Workspace in new window with alert pre-filled
    window.open(`/analyst/investigation.html?alert_id=${encodeURIComponent(alertId)}`, "_blank");

    loadAlertStatistics();
    loadRecentAlerts();
    openAlertDetail(alertId);
  } catch (err) {
    window.open(`/analyst/investigation.html?alert_id=${encodeURIComponent(alertId)}`, "_blank");
  }
}

async function triggerAlertGeneration() {
  const btn = document.getElementById("btn-generate-alerts");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Running…";
  }

  try {
    const res = await fetch("/alerts/generate?dry_run=true", { method: "POST" });
    if (res.ok) {
      const sum = await res.json();
      alert(`Alert Generation Complete:\n• Generated: ${sum.generated}\n• Critical: ${sum.critical}\n• High: ${sum.high}\n• Duplicates/Cooldown Skipped: ${sum.duplicates_skipped + sum.cooldown_skipped}`);
      loadAlertStatistics();
      loadRecentAlerts();
    } else {
      alert("Alert generation failed.");
    }
  } catch (err) {
    alert("Error calling alert generation endpoint.");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "⟳ Generate";
    }
  }
}

// ─── Leaflet Map Layer Integration ──────────────────────────────────────────
function renderAlertMapLayer(alerts) {
  if (typeof L === "undefined") return;

  const map = window.mapInstance || (window.dashboardMap && window.dashboardMap.map);
  if (!map) return;

  if (!alertLayerGroup) {
    alertLayerGroup = L.layerGroup();
    map.addLayer(alertLayerGroup);
  } else {
    alertLayerGroup.clearLayers();
  }

  alerts.forEach((a) => {
    if (!a.latitude || !a.longitude) return;

    const isCrit = a.severity === "CRITICAL";
    const color = isCrit ? "#f85149" : "#f0883e";
    const label = isCrit ? "CRITICAL ANALYTICAL ALERT" : "HIGH ANALYTICAL ALERT";

    const marker = L.circleMarker([a.latitude, a.longitude], {
      radius: isCrit ? 10 : 8,
      fillColor: color,
      color: "#ffffff",
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.75,
    });

    marker.bindPopup(`
      <div style="font-family:sans-serif; min-width:180px;">
        <div style="font-weight:700; color:${color}; margin-bottom:4px; font-size:12px;">${label}</div>
        <div style="font-size:11px; margin-bottom:2px;"><strong>ID:</strong> ${a.alert_id}</div>
        <div style="font-size:11px; margin-bottom:2px;"><strong>Type:</strong> ${formatAlertType(a.alert_type)}</div>
        <div style="font-size:11px; margin-bottom:2px;"><strong>Risk Score:</strong> ${a.risk_score} / 100</div>
        <div style="font-size:11px; margin-bottom:4px;"><strong>Status:</strong> ${a.status}</div>
        <div style="font-size:10px; color:#8b949e; border-top:1px solid #30363d; padding-top:4px;">
          Analytical signal for authorized human review.
        </div>
      </div>
    `);

    marker.on("click", () => {
      openAlertDetail(a.alert_id);
    });

    alertLayerGroup.addLayer(marker);
  });
}

function toggleAlertLayer(visible) {
  const map = window.mapInstance || (window.dashboardMap && window.dashboardMap.map);
  if (!map || !alertLayerGroup) return;

  if (visible) {
    if (!map.hasLayer(alertLayerGroup)) map.addLayer(alertLayerGroup);
  } else {
    if (map.hasLayer(alertLayerGroup)) map.removeLayer(alertLayerGroup);
  }
}

window.transitionAlert = transitionAlert;
window.startAlertInvestigation = startAlertInvestigation;
