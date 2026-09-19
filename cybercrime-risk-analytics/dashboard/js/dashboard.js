/**
 * Phase 15 & SIH Polish — Dashboard Main Controller
 * Orchestrates: Top Navigation, KPI Loading, System Status Health Checks,
 * Model Intelligence Modal & Live SHAP Probe, Priority Areas, Map Init,
 * and Error Shielding.
 */

'use strict';

(async () => {
  const API = '';

  // ── 1. Live Clock ──────────────────────────────────────────────────
  function updateClock() {
    const el = document.getElementById('hdr-time');
    if (el) el.textContent = new Date().toLocaleTimeString('en-IN', { hour12: false });
  }
  updateClock();
  setInterval(updateClock, 1000);

  // ── 2. Top Navigation Bar Wiring ───────────────────────────────────
  function setupNavigation() {
    const tabs = document.querySelectorAll('.nav-tab[data-nav]');
    const mobileBtn = document.getElementById('btn-mobile-nav');
    const topNav = document.getElementById('top-nav');

    if (mobileBtn && topNav) {
      mobileBtn.addEventListener('click', () => {
        topNav.classList.toggle('open');
        mobileBtn.textContent = topNav.classList.contains('open') ? '✕' : '☰';
      });
    }

    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        if (topNav && topNav.classList.contains('open')) {
          topNav.classList.remove('open');
          if (mobileBtn) mobileBtn.textContent = '☰';
        }

        const navTarget = tab.dataset.nav;
        handleNavigation(navTarget);
      });
    });
  }

  function handleNavigation(target) {
    switch (target) {
      case 'overview':
        window.scrollTo({ top: 0, behavior: 'smooth' });
        break;

      case 'map': {
        const mapSec = document.getElementById('section-map');
        if (mapSec) {
          mapSec.scrollIntoView({ behavior: 'smooth' });
        }
        if (window.mapInstance) {
          window.mapInstance.fitBounds([[8.5, 74.4], [17.7, 83.3]]);
        }
        break;
      }

      case 'alerts': {
        const alertSec = document.getElementById('alerts-section');
        if (alertSec) {
          alertSec.scrollIntoView({ behavior: 'smooth' });
        }
        break;
      }

      case 'hotspots': {
        const hsSec = document.getElementById('section-hotspots');
        if (hsSec) {
          hsSec.scrollIntoView({ behavior: 'smooth' });
        }
        break;
      }

      case 'mule-patterns': {
        const muleSec = document.getElementById('section-mule-patterns');
        if (muleSec) {
          muleSec.scrollIntoView({ behavior: 'smooth' });
        }
        break;
      }

      case 'investigations': {
        const invSec = document.getElementById('section-investigations');
        if (invSec) {
          invSec.scrollIntoView({ behavior: 'smooth' });
        }
        break;
      }

      case 'model-intel':
        openModelIntelligenceModal();
        break;

      default:
        break;
    }
  }

  // ── 3. Dedicated Model Intelligence Modal ──────────────────────────
  function openModelIntelligenceModal() {
    const modal = document.getElementById('model-intelligence-modal');
    if (modal) {
      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModelIntelligenceModal() {
    const modal = document.getElementById('model-intelligence-modal');
    if (modal) {
      modal.style.display = 'none';
      document.body.style.overflow = '';
      // Reset active tab in nav back to overview or previous
      const activeNav = document.querySelector('.nav-tab[data-nav="overview"]');
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      activeNav?.classList.add('active');
    }
  }

  function setupModelIntelligenceModal() {
    document.getElementById('btn-close-model-modal')?.addEventListener('click', closeModelIntelligenceModal);
    document.getElementById('btn-open-model-modal-top')?.addEventListener('click', openModelIntelligenceModal);

    const modal = document.getElementById('model-intelligence-modal');
    modal?.addEventListener('click', e => {
      if (e.target === modal) closeModelIntelligenceModal();
    });

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
        closeModelIntelligenceModal();
      }
    });

    // Wire live SHAP Probe button
    document.getElementById('btn-trigger-sample-explain')?.addEventListener('click', runSampleShapExplanation);
  }

  // ── 3b. Subsystem Health Status Modal ──────────────────────────────
  function openSystemStatusModal() {
    const modal = document.getElementById('system-status-modal');
    if (modal) {
      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }
  }

  function closeSystemStatusModal() {
    const modal = document.getElementById('system-status-modal');
    if (modal) {
      modal.style.display = 'none';
      document.body.style.overflow = '';
    }
  }

  function setupSystemStatusModal() {
    document.getElementById('hdr-system-badge')?.addEventListener('click', openSystemStatusModal);
    document.getElementById('btn-open-sys-health')?.addEventListener('click', openSystemStatusModal);
    document.getElementById('btn-close-sys-modal')?.addEventListener('click', closeSystemStatusModal);

    const modal = document.getElementById('system-status-modal');
    modal?.addEventListener('click', e => {
      if (e.target === modal) closeSystemStatusModal();
    });

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
        closeSystemStatusModal();
      }
    });
  }

  // ── 3c. Dynamic Complaint Intake Modal ──────────────────────────────
  function openComplaintIntakeModal() {
    const modal = document.getElementById('complaint-intake-modal');
    if (modal) {
      modal.style.display = 'flex';
      const tsEl = document.getElementById('cmp-timestamp');
      if (tsEl && !tsEl.value) {
        tsEl.value = new Date().toISOString().replace(/\.\d{3}/, '');
      }
    }
  }

  function closeComplaintIntakeModal() {
    const modal = document.getElementById('complaint-intake-modal');
    if (modal) modal.style.display = 'none';
  }

  function setupComplaintIntakeModal() {
    document.getElementById('btn-open-complaint-modal')?.addEventListener('click', openComplaintIntakeModal);
    document.getElementById('btn-close-complaint-modal')?.addEventListener('click', closeComplaintIntakeModal);

    const modal = document.getElementById('complaint-intake-modal');
    modal?.addEventListener('click', e => {
      if (e.target === modal) closeComplaintIntakeModal();
    });

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
        closeComplaintIntakeModal();
      }
    });

    // Set current time helper
    document.getElementById('btn-set-current-time')?.addEventListener('click', () => {
      const tsEl = document.getElementById('cmp-timestamp');
      if (tsEl) tsEl.value = new Date().toISOString().replace(/\.\d{3}/, '');
    });

    // Preset Demonstrators
    document.getElementById('btn-preset-upi-high')?.addEventListener('click', () => {
      document.getElementById('cmp-id').value = '';
      document.getElementById('cmp-timestamp').value = new Date().toISOString().replace(/\.\d{3}/, '');
      document.getElementById('cmp-amount').value = 75000;
      document.getElementById('cmp-channel').value = 'UPI';
      document.getElementById('cmp-category').value = 'UPI_FRAUD';
      document.getElementById('cmp-sender-acc').value = 'ACC000001';
      document.getElementById('cmp-receiver-acc').value = 'ACC000888';
      document.getElementById('cmp-state').value = 'Tamil Nadu';
      document.getElementById('cmp-district').value = 'Chennai';
      document.getElementById('cmp-city').value = 'T Nagar';
      document.getElementById('cmp-lat').value = 13.04;
      document.getElementById('cmp-lon').value = 80.23;
      document.getElementById('cmp-desc').value = 'Victim reported unauthorized UPI transfer following fraudulent electricity bill link.';
    });

    document.getElementById('btn-preset-inv-crit')?.addEventListener('click', () => {
      document.getElementById('cmp-id').value = '';
      document.getElementById('cmp-timestamp').value = new Date().toISOString().replace(/\.\d{3}/, '');
      document.getElementById('cmp-amount').value = 250000;
      document.getElementById('cmp-channel').value = 'IMPS';
      document.getElementById('cmp-category').value = 'INVESTMENT_SCAM';
      document.getElementById('cmp-sender-acc').value = 'ACC000002';
      document.getElementById('cmp-receiver-acc').value = 'ACC000999';
      document.getElementById('cmp-state').value = 'Karnataka';
      document.getElementById('cmp-district').value = 'Bengaluru Urban';
      document.getElementById('cmp-city').value = 'Indiranagar';
      document.getElementById('cmp-lat').value = 12.97;
      document.getElementById('cmp-lon').value = 77.59;
      document.getElementById('cmp-desc').value = 'High-value fraudulent crypto trading scheme promising guaranteed 200% daily returns.';
    });

    document.getElementById('btn-preset-dispute-low')?.addEventListener('click', () => {
      document.getElementById('cmp-id').value = '';
      document.getElementById('cmp-timestamp').value = new Date().toISOString().replace(/\.\d{3}/, '');
      document.getElementById('cmp-amount').value = 3500;
      document.getElementById('cmp-channel').value = 'NET_BANKING';
      document.getElementById('cmp-category').value = 'Online Financial Fraud';
      document.getElementById('cmp-sender-acc').value = 'ACC000003';
      document.getElementById('cmp-receiver-acc').value = 'ACC000777';
      document.getElementById('cmp-state').value = 'Andhra Pradesh';
      document.getElementById('cmp-district').value = 'Chittoor';
      document.getElementById('cmp-city').value = 'Tirupati';
      document.getElementById('cmp-lat').value = 13.63;
      document.getElementById('cmp-lon').value = 79.42;
      document.getElementById('cmp-desc').value = 'Small dispute regarding delayed shipment of mobile accessories from online seller.';
    });

    // Form Submission
    const form = document.getElementById('form-complaint-intake');
    form?.addEventListener('submit', async e => {
      e.preventDefault();
      const statusEl = document.getElementById('cmp-submit-status');
      const btnSubmit = document.getElementById('btn-submit-complaint');
      const resultsCard = document.getElementById('cmp-results-card');

      const amountVal = parseFloat(document.getElementById('cmp-amount')?.value);
      if (isNaN(amountVal) || amountVal <= 0) {
        if (statusEl) statusEl.innerHTML = '<span style="color:#ef4444;">⚠ Fraud loss amount must be greater than zero.</span>';
        return;
      }

      const payload = {
        complaint_id: document.getElementById('cmp-id')?.value.trim() || null,
        complaint_timestamp: document.getElementById('cmp-timestamp')?.value.trim(),
        fraud_amount: amountVal,
        transaction_channel: document.getElementById('cmp-channel')?.value || 'UPI',
        complaint_category: document.getElementById('cmp-category')?.value || 'Online Financial Fraud',
        sender_account_reference: document.getElementById('cmp-sender-acc')?.value.trim() || null,
        receiver_account_reference: document.getElementById('cmp-receiver-acc')?.value.trim() || null,
        state: document.getElementById('cmp-state')?.value.trim(),
        district: document.getElementById('cmp-district')?.value.trim(),
        city: document.getElementById('cmp-city')?.value.trim() || null,
        latitude: document.getElementById('cmp-lat')?.value ? parseFloat(document.getElementById('cmp-lat').value) : null,
        longitude: document.getElementById('cmp-lon')?.value ? parseFloat(document.getElementById('cmp-lon').value) : null,
        description: document.getElementById('cmp-desc')?.value.trim() || null,
      };

      if (btnSubmit) btnSubmit.disabled = true;
      if (statusEl) statusEl.innerHTML = '<span style="color:var(--accent-blue);">⏳ Running dynamic 64-feature extraction and XGBoost inference…</span>';

      try {
        const token = sessionStorage.getItem('analyst_token') || sessionStorage.getItem('auth_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch('/complaints', {
          method: 'POST',
          headers: headers,
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          let errDetail = `HTTP ${res.status}`;
          try {
            const errJson = await res.json();
            errDetail = errJson.message || errJson.detail || errDetail;
          } catch {}
          throw new Error(errDetail);
        }

        const data = await res.json();
        if (statusEl) statusEl.innerHTML = '<span style="color:#22c55e;">✔ Complaint processed and evaluated successfully.</span>';

        // Display results
        if (resultsCard) resultsCard.style.display = 'block';
        document.getElementById('cmp-res-id').textContent = `${data.complaint_id} (${data.prediction_id})`;
        document.getElementById('cmp-res-storage').textContent = data.storage_mode || 'CSV_FALLBACK_DEV';

        const scoreEl = document.getElementById('cmp-res-score');
        const tierBadge = document.getElementById('cmp-res-tier-badge');
        scoreEl.textContent = `${data.risk_score}/100`;

        const tierColors = {
          CRITICAL: { bg: '#ef4444', text: '#fff' },
          HIGH: { bg: '#f97316', text: '#fff' },
          MODERATE: { bg: '#eab308', text: '#000' },
          LOW: { bg: '#22c55e', text: '#fff' },
        };
        const color = tierColors[data.risk_level] || { bg: '#6b7280', text: '#fff' };
        tierBadge.textContent = data.risk_level;
        tierBadge.style.background = color.bg;
        tierBadge.style.color = color.text;

        document.getElementById('cmp-res-prob').textContent = `${(data.withdrawal_probability * 100).toFixed(1)}%`;

        const alertStatusEl = document.getElementById('cmp-res-alert-status');
        const alertMsgEl = document.getElementById('cmp-res-alert-msg');
        if (data.alert && data.alert.created) {
          alertStatusEl.innerHTML = `<span style="color:#ef4444;">🚨 ALERT DISPATCHED: ${data.alert.alert_id}</span>`;
          alertMsgEl.textContent = data.alert.operational_message || 'Human review prioritized.';
        } else {
          alertStatusEl.innerHTML = '<span style="color:var(--text-secondary);">💤 Alert Suppressed</span>';
          alertMsgEl.textContent = 'Risk score below threshold (<60) or suppressed by active 60m cooldown.';
        }

        // Render SHAP
        const shapList = document.getElementById('cmp-res-shap-list');
        if (shapList) {
          if (data.top_risk_drivers && data.top_risk_drivers.length) {
            shapList.innerHTML = data.top_risk_drivers.map(d => `
              <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                <span style="font-family:var(--font-mono);font-size:10px;">${d.feature}</span>
                <span style="font-size:10px;font-weight:700;color:${d.shap_value >= 0 ? '#f87171' : '#4ade80'};">
                  ${d.shap_value >= 0 ? '+' : ''}${d.shap_value.toFixed(4)} (${d.direction})
                </span>
              </div>
            `).join('');
          } else {
            shapList.innerHTML = '<span style="color:var(--text-secondary);">No individual SHAP drivers computed.</span>';
          }
        }

        // Render Corridors
        const corridorsList = document.getElementById('cmp-res-corridors-list');
        if (corridorsList) {
          if (data.predicted_locations && data.predicted_locations.length) {
            corridorsList.innerHTML = data.predicted_locations.slice(0, 3).map((loc, idx) => `
              <div style="padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                <div style="font-weight:700;color:var(--accent-blue);">#${idx + 1} Cluster ${loc.cluster_id} (${loc.district})</div>
                <div style="font-size:10px;color:var(--text-secondary);">
                  Nearest ATM: <strong>${loc.nearest_atm_id || 'N/A'}</strong> (${loc.nearest_atm_bank || 'Bank'}) · ${loc.nearest_atm_distance_km ? loc.nearest_atm_distance_km.toFixed(2) + ' km' : '—'}
                </div>
              </div>
            `).join('');
          } else {
            corridorsList.innerHTML = '<span style="color:var(--text-secondary);">No correlated cashout corridors identified.</span>';
          }
        }

        resultsCard.scrollIntoView({ behavior: 'smooth' });

      } catch (err) {
        if (statusEl) statusEl.innerHTML = `<span style="color:#ef4444;">❌ Submission failed: ${err.message}</span>`;
      } finally {
        if (btnSubmit) btnSubmit.disabled = false;
      }
    });
  }

  async function runSampleShapExplanation() {
    const outBox = document.getElementById('sample-explain-result');
    if (!outBox) return;

    outBox.innerHTML = '<span class="loading-text">Computing TreeExplainer marginal contributions…</span>';

    // Synthetic complaint feature payload (64 features)
    const samplePayload = {
      crime_type: "Online Financial Fraud",
      fraud_amount: 15000.0,
      reported_by_authority: 0.0,
      victim_state: "Andhra Pradesh",
      victim_district: "Chittoor",
      victim_area: "Tirupati",
      victim_area_id: "AP_CHT_001",
      latitude: 13.63,
      longitude: 79.42,
      event_year: 2026,
      event_month: 3,
      event_day: 75,
      event_day_of_month: 15,
      event_day_of_week: 2,
      event_hour: 14,
      event_minute: 30,
      is_weekend: 0.0,
      is_month_start: 0.0,
      is_month_end: 0.0,
      is_quarter_start: 0.0,
      is_quarter_end: 0.0,
      hour_group: "afternoon",
      time_period: "business_hours",
      latitude_rounded: 13.63,
      longitude_rounded: 79.42,
      location_grid: "13.63_79.42",
      coordinate_precision: "high",
      geographic_region: "South",
      crime_category_group: "Financial",
      amount_bracket: "medium",
      amount_log1p: 9.6158,
      is_round_amount: 1.0,
      high_risk_amount: 0.0,
      critical_risk_amount: 0.0,
      events_in_previous_1_day: 4.0,
      events_in_previous_7_days: 18.0,
      events_in_previous_30_days: 42.0,
      previous_event_count: 5.0,
      time_since_previous_event_hours: 3.5,
      rolling_event_count_1h: 2.0,
      rolling_event_count_6h: 5.0,
      rolling_event_count_24h: 12.0,
      rolling_crime_event_count_7d: 14.0,
      district_previous_7d_events: 22.0,
      location_previous_7d_events: 18.0,
      district_previous_30d_events: 65.0,
      location_previous_30d_events: 45.0,
      district_high_risk_event_count: 3.0,
      location_high_risk_event_count: 2.0,
      crime_category_risk_ratio: 0.28,
      district_crime_density: 0.35,
      previous_activity_by_crime_category: 120.0,
      previous_activity_by_location: 85.0,
      previous_activity_by_district: 140.0,
      previous_activity_by_month: 210.0,
      previous_activity_by_day_of_week: 95.0,
      previous_activity_by_hour: 40.0,
      previous_activity_by_hour_group: 80.0,
      previous_activity_by_time_period: 110.0,
      previous_activity_by_amount_bracket: 90.0,
      previous_activity_by_geographic_region: 350.0,
      previous_activity_by_location_grid: 75.0,
      previous_activity_by_coordinate_precision: 400.0,
    };

    try {
      const res = await fetch('/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(samplePayload),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      let contribsHtml = '';
      if (data.shap_contributions && data.shap_contributions.length > 0) {
        const topContribs = data.shap_contributions.slice(0, 6);
        contribsHtml = `
          <div style="margin-top:8px;">
            <div style="font-weight:600;font-size:11px;color:var(--text-primary);margin-bottom:4px;">Top Model Attributions for Record:</div>
            ${topContribs.map(c => {
              const val = Number(c.shap_value);
              const isPos = val >= 0;
              const color = isPos ? '#388bfd' : '#f0883e';
              const sign = isPos ? '+' : '';
              return `
                <div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--border-subtle);font-size:10px;">
                  <span class="font-mono">${c.feature_name}</span>
                  <span class="font-mono" style="color:${color};font-weight:700;">${sign}${val.toFixed(4)}</span>
                </div>
              `;
            }).join('')}
          </div>
        `;
      }

      outBox.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
          <div>
            <strong>Predicted Probability:</strong> <span class="font-mono" style="color:#79c0ff;">${Number(data.predicted_probability).toFixed(4)}</span>
            &nbsp;·&nbsp;
            <strong>Risk Score:</strong> <span class="font-mono font-bold" style="color:${data.risk_score >= 60 ? '#f0883e' : '#3fb950'};">${data.risk_score} / 100</span>
            &nbsp;·&nbsp;
            <strong>Tier:</strong> <span class="risk-chip ${data.risk_category}">${data.risk_category}</span>
          </div>
        </div>
        <div style="font-size:11px;color:var(--text-secondary);line-height:1.4;">
          ${data.operational_interpretation || 'Model evaluated. These features contributed toward the model prediction.'}
        </div>
        ${contribsHtml}
      `;
    } catch (err) {
      console.warn('SHAP explain query error:', err);
      outBox.innerHTML = '<div class="error-text">Model explanation unavailable</div>';
    }
  }

  // ── 4. System Status Health Check ─────────────────────────────────
  async function checkSystemStatus() {
    // 1. ML Model & Prediction API (/health)
    try {
      const res = await fetch('/health');
      if (res.ok) {
        const data = await res.json();
        const mlOk = data.model_loaded === true;
        _setStatus('status-ml-model', mlOk ? 'ONLINE' : 'OFFLINE', mlOk ? 'online' : 'offline');
        _setStatus('status-pred-api', 'ONLINE', 'online');
      } else {
        _setStatus('status-ml-model', 'OFFLINE', 'offline');
        _setStatus('status-pred-api', 'OFFLINE', 'offline');
      }
    } catch (e) {
      _setStatus('status-ml-model', 'OFFLINE', 'offline');
      _setStatus('status-pred-api', 'OFFLINE', 'offline');
    }

    // 2. PostgreSQL & PostGIS (/database/health)
    try {
      const res = await fetch('/database/health');
      if (res.ok) {
        const data = await res.json();
        const dbOk = data.status === 'healthy';
        _setStatus('status-postgres', dbOk ? 'ONLINE' : 'NOT CONFIGURED', dbOk ? 'online' : 'warning');
        _setStatus('status-postgis', (dbOk && data.postgis_available) ? 'ONLINE' : 'NOT CONFIGURED', (dbOk && data.postgis_available) ? 'online' : 'warning');
      } else {
        _setStatus('status-postgres', 'NOT CONFIGURED', 'warning');
        _setStatus('status-postgis', 'NOT CONFIGURED', 'warning');
      }
    } catch (e) {
      _setStatus('status-postgres', 'NOT CONFIGURED', 'warning');
      _setStatus('status-postgis', 'NOT CONFIGURED', 'warning');
    }

    // 3. Hotspot Engine (/gis/hotspots?limit=1)
    try {
      const res = await fetch('/gis/hotspots?limit=1');
      _setStatus('status-hotspots', res.ok ? 'ONLINE' : 'OFFLINE', res.ok ? 'online' : 'offline');
    } catch (e) {
      _setStatus('status-hotspots', 'OFFLINE', 'offline');
    }

    // 4. Alert Engine (/alerts/statistics)
    try {
      const res = await fetch('/alerts/statistics');
      _setStatus('status-alerts', res.ok ? 'ONLINE' : 'OFFLINE', res.ok ? 'online' : 'offline');
    } catch (e) {
      _setStatus('status-alerts', 'OFFLINE', 'offline');
    }

    // 5. Dashboard API (/gis/summary)
    try {
      const res = await fetch('/gis/summary');
      _setStatus('status-dashboard', res.ok ? 'ONLINE' : 'OFFLINE', res.ok ? 'online' : 'offline');
    } catch (e) {
      _setStatus('status-dashboard', 'OFFLINE', 'offline');
    }

    // Update Header Pulse Badge
    const headerStatusText = document.getElementById('hdr-status-text');
    const headerPulseDot = document.getElementById('hdr-pulse-dot');
    if (headerStatusText && headerPulseDot) {
      const dbBadge = document.getElementById('status-postgres')?.textContent;
      if (dbBadge === 'NOT CONFIGURED') {
        headerStatusText.textContent = 'SYSTEM ACTIVE (FALLBACK)';
        headerPulseDot.className = 'status-pulse-dot warning';
      } else {
        headerStatusText.textContent = 'SYSTEM ONLINE';
        headerPulseDot.className = 'status-pulse-dot online';
      }
    }
  }

  function _setStatus(id, text, stateClass) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    el.className = `status-badge ${stateClass}`;
    if (text === 'NOT CONFIGURED') {
      el.title = 'Local DB daemon inactive — Resilient Dual-Mode GeoJSON Fallback Active';
    }
  }

  // ── 5. KPI Cards ──────────────────────────────────────────────────
  function _safeNum(val, fallback = 'Data unavailable') {
    if (val === null || val === undefined || isNaN(Number(val))) return fallback;
    return Number(val).toLocaleString();
  }

  function _safeRisk(val, fallback = 'Data unavailable') {
    if (val === null || val === undefined || isNaN(Number(val))) return fallback;
    return Number(val).toFixed(1);
  }

  function _safeStr(val, fallback = 'Data unavailable') {
    if (!val || typeof val !== 'string' || val.trim() === '' || val.trim() === 'N/A') return fallback;
    return val.trim();
  }

  async function loadKPIs(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.start_time) params.set('start_time', filters.start_time);
      if (filters.end_time) params.set('end_time', filters.end_time);
      if (filters.crime_category) params.set('crime_category', filters.crime_category);
      if (filters.crime_type) params.set('crime_type', filters.crime_type);
      if (filters.risk_category) params.set('risk_category', filters.risk_category);
      if (filters.min_risk_score !== undefined && filters.min_risk_score !== '') params.set('min_risk_score', filters.min_risk_score);
      if (filters.max_risk_score !== undefined && filters.max_risk_score !== '') params.set('max_risk_score', filters.max_risk_score);
      if (filters.hotspot_id !== undefined && filters.hotspot_id !== '') params.set('hotspot_id', filters.hotspot_id);
      if (filters.hotspot_only) params.set('hotspot_only', 'true');

      const qs = params.toString();
      const url = qs ? `${API}/gis/summary?${qs}` : `${API}/gis/summary`;

      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const d = await res.json();
      if (!d || typeof d !== 'object') throw new Error('Invalid JSON payload for summary KPIs');

      // Safe schema resolution supporting primary & alternative naming
      const total = d.total_analytical_records ?? d.total ?? d.count ?? d.records ?? null;
      const high = d.high_risk_records ?? d.high_risk_count ?? d.high_risk ?? null;
      const critical = d.critical_risk_records ?? d.critical_risk_count ?? d.critical_risk ?? null;
      const hotspots = d.hotspot_count ?? d.hotspots ?? d.total_hotspots ?? null;
      const avgRisk = d.average_risk_score ?? d.average_risk ?? d.avg_risk ?? d.risk_score ?? null;
      const topArea = d.highest_risk_area ?? d.top_risk_area ?? d.area ?? d.highest_area ?? null;

      _kpi('kpi-total-val',    _safeNum(total));
      _kpi('kpi-high-val',     _safeNum(high));
      _kpi('kpi-critical-val', _safeNum(critical));
      _kpi('kpi-hotspot-val',  _safeNum(hotspots));
      _kpi('kpi-avg-risk-val', _safeRisk(avgRisk));
      _kpi('kpi-area-val',     _safeStr(topArea));
    } catch (e) {
      console.error('[Dashboard] KPI load failed:', e);
      ['kpi-total-val', 'kpi-high-val', 'kpi-critical-val', 'kpi-hotspot-val', 'kpi-avg-risk-val', 'kpi-area-val'].forEach(id => {
        _kpi(id, 'Data unavailable');
      });
    }
  }

  function _kpi(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  // ── 6. Priority Analytical Areas ─────────────────────────────────
  async function loadPriorityList() {
    const list = document.getElementById('priority-list');
    if (!list) return;

    try {
      const res = await fetch(`${API}/gis/hotspots?limit=10`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (!data.features || data.features.length === 0) {
        list.innerHTML = '<div class="loading-text">No hotspot data available.</div>';
        return;
      }

      const sorted = [...data.features].sort((a, b) =>
        (a.properties.hotspot_rank || 999) - (b.properties.hotspot_rank || 999)
      );

      list.innerHTML = sorted.map(f => {
        const p = f.properties;
        const [lon, lat] = f.geometry.coordinates;
        return `
          <div class="priority-item" onclick="GISMap.showHotspotDetail(${p.hotspot_id}); GISMap.getMap().setView([${lat},${lon}], 11);">
            <div class="priority-rank">#${p.hotspot_rank}</div>
            <div class="priority-info">
              <div class="priority-name">HS-${p.hotspot_id} · ${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E</div>
              <div class="priority-meta">${p.event_count} events · Risk ${p.average_risk_score?.toFixed(1) || '—'}</div>
            </div>
            <span class="priority-badge badge-${p.hotspot_status}">${(p.hotspot_status||'').replace('_ACTIVITY','')}</span>
          </div>
        `;
      }).join('');
    } catch (e) {
      list.innerHTML = '<div class="error-text">Priority list unavailable.</div>';
    }
  }

  // ── 6b. Mule Pattern Accounts (Heuristic Fan-In Analysis) ────────
  async function loadMulePatternAccounts() {
    const tbody = document.getElementById('mule-patterns-tbody');
    const badge = document.getElementById('mule-count-badge');
    if (!tbody) return;

    try {
      const res = await fetch(`${API}/gis/mule-pattern-accounts?limit=15&flagged_only=true`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const items = data.items || [];
      if (badge) {
        badge.textContent = `${data.flagged_count || items.length} Flagged Indicators`;
      }

      if (items.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" class="loading-text" style="text-align:center;padding:24px;">No accounts currently flagged by fan-in heuristic.</td>
          </tr>`;
        return;
      }

      tbody.innerHTML = items.map(acc => {
        const score = acc.mule_pattern_score || 0;
        const scoreBadgeStyle = score >= 85
          ? 'background:var(--risk-critical-bg);color:var(--risk-critical);border:1px solid var(--risk-critical-border);'
          : (score >= 70
            ? 'background:var(--risk-high-bg);color:var(--risk-high);border:1px solid var(--risk-high-border);'
            : 'background:var(--risk-moderate-bg);color:var(--risk-moderate);border:1px solid var(--risk-moderate-border);');
        const gapStr = acc.avg_incoming_gap_hours != null ? `${acc.avg_incoming_gap_hours.toFixed(2)}h` : '—';

        return `
          <tr class="alert-table-row">
            <td class="font-mono" style="color:var(--text-primary); font-weight:600;">${acc.account_id}</td>
            <td style="color:var(--text-primary);"><span style="font-weight:700; color:var(--text-primary);">${acc.distinct_source_count_72h}</span> distinct sources</td>
            <td style="color:var(--text-secondary);">${acc.distinct_source_count_total} total sources</td>
            <td class="font-mono" style="color:var(--text-secondary);">${gapStr}</td>
            <td>
              <span class="badge" style="font-weight:700; font-size:11px; padding:3px 8px; ${scoreBadgeStyle}">
                Score ${score}
              </span>
            </td>
            <td>
              <span class="priority-badge" style="background:rgba(251,146,60,0.15); color:var(--risk-high); border:1px solid rgba(251,146,60,0.35); font-size:10px; padding:3px 8px; border-radius:4px; font-weight:700;">
                ELEVATED FAN-IN
              </span>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.warn('Failed to load mule pattern accounts:', err);
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="error-text" style="text-align:center;padding:20px;">
            Mule pattern indicator service unavailable.
          </td>
        </tr>`;
    }
  }

  // ── 7. UI Controls & Listeners ───────────────────────────────────
  // Detail Panel Close Listeners
  document.getElementById('detail-close')?.addEventListener('click', () => {
    const p = document.getElementById('detail-panel');
    p?.classList.remove('open');
    p?.classList.remove('active');
  });

  document.getElementById('alert-detail-close')?.addEventListener('click', () => {
    const p = document.getElementById('alert-detail-panel');
    p?.classList.remove('open');
    p?.classList.remove('active');
  });

  // Map Controls
  document.getElementById('btn-reset-map-view')?.addEventListener('click', () => {
    if (window.mapInstance) {
      window.mapInstance.fitBounds([[8.5, 74.4], [17.7, 83.3]]);
    }
  });

  // Collapsible Map Legend Toggle
  const legendToggle = document.getElementById('legend-toggle');
  const mapLegend = document.getElementById('map-legend');
  if (legendToggle && mapLegend) {
    legendToggle.addEventListener('click', () => {
      mapLegend.classList.toggle('collapsed');
      legendToggle.textContent = mapLegend.classList.contains('collapsed') ? '+' : '−';
      legendToggle.title = mapLegend.classList.contains('collapsed') ? 'Expand Legend' : 'Collapse Legend';
    });
  }

  document.getElementById('btn-recheck-status')?.addEventListener('click', () => {
    checkSystemStatus();
  });

  // ── 8. Apply filters callback ─────────────────────────────────────
  async function onFiltersApply(filters) {
    const metric = document.getElementById('heatmap-metric-select')?.value || 'risk';
    await Promise.all([
      loadKPIs(filters),
      GISMap.loadHeatmap(filters, metric),
      GISMap.loadEvents(filters),
    ]);
  }

  // ── 9. Global Refresh Action ──────────────────────────────────────
  document.getElementById('btn-refresh')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-refresh');
    if (btn) {
      btn.disabled = true;
      btn.textContent = '⟳ Refreshing…';
    }

    try {
      await Promise.all([
        loadKPIs(),
        checkSystemStatus(),
        GISMap.loadHeatmap(),
        GISMap.loadHotspots(),
        GISMap.loadEvents({}),
        GISCharts.loadAll(),
        loadPriorityList(),
        loadMulePatternAccounts(),
      ]);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = '⟳ Refresh';
      }
    }
  });

  // ── 9b. User Profile Dropdown ────────────────────────────────────
  function setupUserProfileMenu() {
    const btn = document.getElementById('btn-user-profile');
    const menu = document.getElementById('user-dropdown-menu');
    const btnLogout = document.getElementById('btn-user-logout');

    if (btn && menu) {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        menu.style.display = menu.style.display === 'none' ? 'flex' : 'none';
      });

      document.addEventListener('click', (e) => {
        if (!menu.contains(e.target) && e.target !== btn) {
          menu.style.display = 'none';
        }
      });
    }

    if (btnLogout) {
      btnLogout.addEventListener('click', () => {
        localStorage.removeItem('analyst_token');
        sessionStorage.removeItem('analyst_token');
        window.location.href = '/analyst/index.html';
      });
    }
  }

  // ── 10. Bootstrap ─────────────────────────────────────────────────
  async function bootstrap() {
    setupNavigation();
    setupUserProfileMenu();
    setupModelIntelligenceModal();
    setupSystemStatusModal();
    setupComplaintIntakeModal();

    // Initialize Map and Layer Toggles
    GISMap.init();
    GISMap.setupLayerToggles();

    // Initialize Filters Toolbar & Sidebar
    await GISFilters.init(onFiltersApply);

    // Initial Parallel Loading
    await Promise.all([
      loadKPIs(),
      checkSystemStatus(),
      GISMap.loadHeatmap(),
      GISMap.loadHotspots(),
      GISCharts.loadAll(),
      loadPriorityList(),
      loadMulePatternAccounts(),
    ]);
  }

  bootstrap().catch(e => console.error('Dashboard bootstrap error:', e));
})();

