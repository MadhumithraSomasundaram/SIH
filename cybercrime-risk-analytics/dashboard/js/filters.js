/**
 * Phase 15 & SIH Polish — Filter Panel & Toolbar Module
 * Manages all dashboard filter interactions:
 * - Horizontal Toolbar (above map)
 * - Quick Time Presets (7d, 30d, 90d, All)
 * - Crime Category dropdown populated from /gis/filters
 * - Risk Category selection (All, LOW, MODERATE, HIGH, CRITICAL)
 * - Hotspots Only toggle
 * - Reset and Apply actions with debouncing and real backend calls
 */

'use strict';

const GISFilters = (() => {
  let _onApply = null;

  // ── Populate dropdowns from /gis/filters ─────────────────────────
  async function init(onApplyCallback) {
    _onApply = onApplyCallback;

    try {
      const res = await fetch('/gis/filters');
      if (!res.ok) throw new Error('Filter load failed');
      const data = await res.json();

      // Populate both toolbar and sidebar category dropdowns
      _populate('tb-filter-crime-category', data.crime_categories, 'All Crime Categories');
      _populate('filter-crime-category', data.crime_categories, 'All Categories');
      _populate('filter-crime-type', data.crime_types, 'All Types');
      _populateHotspots('tb-filter-hotspot-id', data.hotspot_ids);
      _populateHotspots('filter-hotspot-id', data.hotspot_ids);

      // Set date range bounds
      if (data.time_range?.earliest) {
        const minDate = data.time_range.earliest.slice(0, 10);
        const maxDate = data.time_range.latest ? data.time_range.latest.slice(0, 10) : '';

        const startInputs = ['tb-filter-start', 'filter-start'];
        const endInputs = ['tb-filter-end', 'filter-end'];

        startInputs.forEach(id => {
          const el = document.getElementById(id);
          if (el) el.min = minDate;
        });

        endInputs.forEach(id => {
          const el = document.getElementById(id);
          if (el) el.max = maxDate;
        });
      }
    } catch (e) {
      console.warn('Filter population failed:', e);
    }

    _bindEvents();
  }

  function _populate(id, values, placeholder) {
    const sel = document.getElementById(id);
    if (!sel || !values) return;
    sel.innerHTML = `<option value="">${placeholder}</option>`;
    values.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v.replace(/_/g, ' ');
      sel.appendChild(opt);
    });
  }

  function _populateHotspots(id, ids) {
    const sel = document.getElementById(id);
    if (!sel || !ids) return;
    sel.innerHTML = `<option value="">All Hotspots</option>`;
    ids.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = `Hotspot HS-${v}`;
      sel.appendChild(opt);
    });
  }

  // ── Read current filter values ────────────────────────────────────
  function getFilters() {
    const filters = {};

    // 1. Time Range: check toolbar first, then sidebar
    const tbStart = document.getElementById('tb-filter-start')?.value;
    const tbEnd   = document.getElementById('tb-filter-end')?.value;
    const sbStart = document.getElementById('filter-start')?.value;
    const sbEnd   = document.getElementById('filter-end')?.value;

    const start = tbStart || sbStart;
    const end   = tbEnd || sbEnd;
    if (start) filters.start_time = start;
    if (end)   filters.end_time   = end;

    // 2. Crime Category: check toolbar first, then sidebar
    const tbCat = document.getElementById('tb-filter-crime-category')?.value;
    const sbCat = document.getElementById('filter-crime-category')?.value;
    const cat = tbCat || sbCat;
    if (cat) filters.crime_category = cat;

    // 3. Crime Type: from sidebar
    const ctype = document.getElementById('filter-crime-type')?.value;
    if (ctype) filters.crime_type = ctype;

    // 4. Risk Category: toolbar select takes priority, or checkboxes
    const tbRisk = document.getElementById('tb-filter-risk-category')?.value;
    if (tbRisk && tbRisk !== '') {
      filters.risk_category = tbRisk;
    } else {
      const riskCbs = [...document.querySelectorAll('.risk-cb')];
      const checked = riskCbs.filter(cb => cb.checked).map(cb => cb.value);
      if (checked.length === 1) {
        filters.risk_category = checked[0];
      }
    }

    // 5. Risk Score Range: from sidebar inputs
    const minR = document.getElementById('filter-min-risk')?.value;
    const maxR = document.getElementById('filter-max-risk')?.value;
    if (minR !== undefined && minR !== '') filters.min_risk_score = parseInt(minR, 10);
    if (maxR !== undefined && maxR !== '') filters.max_risk_score = parseInt(maxR, 10);

    // 6. Hotspot ID: check toolbar first, then sidebar
    const tbHsId = document.getElementById('tb-filter-hotspot-id')?.value;
    const sbHsId = document.getElementById('filter-hotspot-id')?.value;
    const hsVal = (tbHsId !== undefined && tbHsId !== '') ? tbHsId : sbHsId;
    if (hsVal !== undefined && hsVal !== '') filters.hotspot_id = parseInt(hsVal, 10);

    // 7. Hotspots Only toggle
    const tbHsOnly = document.getElementById('tb-filter-hotspot-only')?.checked;
    if (tbHsOnly) {
      filters.hotspot_only = true;
    }

    return filters;
  }

  // ── Reset all filters ─────────────────────────────────────────────
  function reset() {
    // Toolbar inputs
    const tbStart = document.getElementById('tb-filter-start');
    const tbEnd = document.getElementById('tb-filter-end');
    const tbCat = document.getElementById('tb-filter-crime-category');
    const tbRisk = document.getElementById('tb-filter-risk-category');
    const tbHs = document.getElementById('tb-filter-hotspot-id');
    const tbHsOnly = document.getElementById('tb-filter-hotspot-only');

    if (tbStart) tbStart.value = '';
    if (tbEnd) tbEnd.value = '';
    if (tbCat) tbCat.value = '';
    if (tbRisk) tbRisk.value = '';
    if (tbHs) tbHs.value = '';
    if (tbHsOnly) tbHsOnly.checked = false;

    // Sidebar inputs
    const sbStart = document.getElementById('filter-start');
    const sbEnd = document.getElementById('filter-end');
    const sbCat = document.getElementById('filter-crime-category');
    const sbType = document.getElementById('filter-crime-type');
    const sbHsId = document.getElementById('filter-hotspot-id');
    const sbMinR = document.getElementById('filter-min-risk');
    const sbMaxR = document.getElementById('filter-max-risk');

    if (sbStart) sbStart.value = '';
    if (sbEnd) sbEnd.value = '';
    if (sbCat) sbCat.value = '';
    if (sbType) sbType.value = '';
    if (sbHsId) sbHsId.value = '';
    if (sbMinR) sbMinR.value = '';
    if (sbMaxR) sbMaxR.value = '';

    document.querySelectorAll('.risk-cb').forEach(cb => { cb.checked = true; });
    document.querySelectorAll('.btn-preset, .btn-tb-preset').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('[data-preset="all"]').forEach(b => b.classList.add('active'));

    if (_onApply) _onApply({});
  }

  // ── Time presets ──────────────────────────────────────────────────
  function _applyPreset(preset) {
    document.querySelectorAll('.btn-preset, .btn-tb-preset').forEach(b => {
      if (b.dataset.preset === preset) b.classList.add('active');
      else b.classList.remove('active');
    });

    const now = new Date();
    const fmt = d => d.toISOString().slice(0, 10);

    if (preset === 'all') {
      const elTbStart = document.getElementById('tb-filter-start');
      const elTbEnd = document.getElementById('tb-filter-end');
      const elSbStart = document.getElementById('filter-start');
      const elSbEnd = document.getElementById('filter-end');

      if (elTbStart) elTbStart.value = '';
      if (elTbEnd) elTbEnd.value = '';
      if (elSbStart) elSbStart.value = '';
      if (elSbEnd) elSbEnd.value = '';
      return;
    }

    const days = { '7d': 7, '30d': 30, '90d': 90 }[preset];
    if (days) {
      const start = new Date(now);
      start.setDate(start.getDate() - days);
      const startStr = fmt(start);
      const endStr = fmt(now);

      const elTbStart = document.getElementById('tb-filter-start');
      const elTbEnd = document.getElementById('tb-filter-end');
      const elSbStart = document.getElementById('filter-start');
      const elSbEnd = document.getElementById('filter-end');

      if (elTbStart) elTbStart.value = startStr;
      if (elTbEnd) elTbEnd.value = endStr;
      if (elSbStart) elSbStart.value = startStr;
      if (elSbEnd) elSbEnd.value = endStr;
    }
  }

  // ── Event bindings ────────────────────────────────────────────────
  function _bindEvents() {
    // Toolbar actions
    document.getElementById('btn-tb-apply')?.addEventListener('click', () => {
      if (_onApply) _onApply(getFilters());
    });

    document.getElementById('btn-tb-reset')?.addEventListener('click', reset);

    // Sidebar actions
    document.getElementById('btn-apply-filters')?.addEventListener('click', () => {
      if (_onApply) _onApply(getFilters());
    });

    document.getElementById('btn-reset-filters')?.addEventListener('click', reset);

    // Preset buttons (both toolbar and sidebar)
    document.querySelectorAll('.btn-preset, .btn-tb-preset').forEach(btn => {
      btn.addEventListener('click', () => {
        _applyPreset(btn.dataset.preset);
      });
    });

    // Sync dates when changed
    document.getElementById('tb-filter-start')?.addEventListener('change', e => {
      const sb = document.getElementById('filter-start');
      if (sb) sb.value = e.target.value;
    });
    document.getElementById('tb-filter-end')?.addEventListener('change', e => {
      const sb = document.getElementById('filter-end');
      if (sb) sb.value = e.target.value;
    });

    // Sync hotspot dropdowns
    document.getElementById('tb-filter-hotspot-id')?.addEventListener('change', e => {
      const sb = document.getElementById('filter-hotspot-id');
      if (sb) sb.value = e.target.value;
    });
    document.getElementById('filter-hotspot-id')?.addEventListener('change', e => {
      const tb = document.getElementById('tb-filter-hotspot-id');
      if (tb) tb.value = e.target.value;
    });

    // Auto-apply on Enter inside date fields
    ['tb-filter-start', 'tb-filter-end'].forEach(id => {
      document.getElementById(id)?.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
          if (_onApply) _onApply(getFilters());
        }
      });
    });
  }

  return { init, getFilters, reset };
})();
