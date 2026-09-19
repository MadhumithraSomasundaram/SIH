/**
 * Phase 15 — Charts Module
 * Chart.js bar/donut charts for risk distribution, crime categories,
 * hourly activity, and top districts. Uses /gis/statistics endpoint.
 */

'use strict';

const GISCharts = (() => {
  const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: '#94A3B8',
          font: { size: 10, family: "'Inter', sans-serif" },
          boxWidth: 10,
          padding: 8,
        },
      },
      tooltip: {
        backgroundColor: '#111827',
        titleColor: '#F1F5F9',
        bodyColor: '#94A3B8',
        borderColor: '#263247',
        borderWidth: 1,
        padding: 8,
        cornerRadius: 6,
      },
    },
  };

  const COLORS = {
    LOW:      '#22C55E',
    MODERATE: '#FACC15',
    HIGH:     '#FB923C',
    CRITICAL: '#EF4444',
    noData:   '#263247',
    blue:     '#3B82F6',
    cyan:     '#22D3EE',
    purple:   '#8B5CF6',
  };

  const PALETTE = [
    '#3B82F6','#8B5CF6','#22C55E','#FACC15','#FB923C','#EF4444',
    '#22D3EE','#60A5FA','#A78BFA','#FBBF24','#F87171','#34D399',
  ];

  let _charts = {};

  function _destroy(id) {
    if (_charts[id]) { _charts[id].destroy(); delete _charts[id]; }
  }

  // ── Risk Category Donut ───────────────────────────────────────────
  function renderRiskDist(data) {
    _destroy('chart-risk-dist');
    const ctx = document.getElementById('chart-risk-dist').getContext('2d');
    const d = data.risk_category_distribution || {};
    _charts['chart-risk-dist'] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['LOW', 'MODERATE', 'HIGH', 'CRITICAL', 'No Data'],
        datasets: [{
          data: [d.LOW||0, d.MODERATE||0, d.HIGH||0, d.CRITICAL||0, d.no_risk_data||0],
          backgroundColor: [COLORS.LOW, COLORS.MODERATE, COLORS.HIGH, COLORS.CRITICAL, COLORS.noData],
          borderColor: '#0d1117',
          borderWidth: 2,
          hoverOffset: 6,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: {
          ...CHART_DEFAULTS.plugins,
          legend: { position: 'right', labels: { color: '#8b949e', font: { size: 10 }, boxWidth: 10 } },
        },
        cutout: '65%',
      },
    });
  }

  // ── Crime Category Bar ────────────────────────────────────────────
  function renderCrimeCat(data) {
    _destroy('chart-crime-cat');
    const ctx = document.getElementById('chart-crime-cat').getContext('2d');
    const d = data.crime_category_distribution || {};
    const labels = Object.keys(d).map(k => k.replace(/_/g, ' '));
    const values = Object.values(d);
    _charts['chart-crime-cat'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Events',
          data: values,
          backgroundColor: PALETTE.slice(0, labels.length),
          borderRadius: 4,
          borderSkipped: false,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        indexAxis: 'y',
        plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } },
        scales: {
          x: { ticks: { color: '#94A3B8', font: { size: 9 } }, grid: { color: '#1c2637' } },
          y: { ticks: { color: '#94A3B8', font: { size: 9 } }, grid: { display: false } },
        },
      },
    });
  }

  // ── Hourly Activity Bar ───────────────────────────────────────────
  function renderHourly(data) {
    _destroy('chart-hourly');
    const ctx = document.getElementById('chart-hourly').getContext('2d');
    const d = data.hourly_activity_in_hotspots || {};
    const labels = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2,'0')}h`);
    const values = labels.map((_, i) => d[String(i)] || 0);

    _charts['chart-hourly'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Events',
          data: values,
          backgroundColor: values.map(v => {
            const max = Math.max(...values, 1);
            const intensity = v / max;
            return intensity > 0.75 ? COLORS.CRITICAL :
                   intensity > 0.5  ? COLORS.HIGH :
                   intensity > 0.25 ? COLORS.MODERATE : COLORS.cyan;
          }),
          borderRadius: 2,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } },
        scales: {
          x: { ticks: { color: '#64748B', font: { size: 8 }, maxRotation: 0 }, grid: { color: '#1c2637' } },
          y: { ticks: { color: '#64748B', font: { size: 9 } }, grid: { color: '#1c2637' } },
        },
      },
    });
  }

  // ── Top Districts Bar ─────────────────────────────────────────────
  function renderDistricts(data) {
    _destroy('chart-districts');
    const ctx = document.getElementById('chart-districts').getContext('2d');
    const d = data.top_districts_by_events || {};
    const entries = Object.entries(d).slice(0, 10);
    const labels = entries.map(([k]) => k);
    const values = entries.map(([, v]) => v);

    _charts['chart-districts'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Events',
          data: values,
          backgroundColor: COLORS.blue,
          borderRadius: 3,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        indexAxis: 'y',
        plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } },
        scales: {
          x: { ticks: { color: '#64748B', font: { size: 9 } }, grid: { color: '#1c2637' } },
          y: { ticks: { color: '#94A3B8', font: { size: 8.5 } }, grid: { display: false } },
        },
      },
    });
  }

  // ── Load all charts ───────────────────────────────────────────────
  async function loadAll() {
    try {
      const res = await fetch('/gis/statistics');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      renderRiskDist(data);
      renderCrimeCat(data);
      renderHourly(data);
      renderDistricts(data);
    } catch (e) {
      console.warn('Charts load failed:', e);
    }
  }

  return { loadAll };
})();
