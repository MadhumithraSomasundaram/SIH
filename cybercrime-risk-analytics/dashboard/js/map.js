/**
 * Phase 15 & SIH Polish — GIS Map Module
 * Manages Leaflet map: basemap, heatmap, hotspot markers, event clusters, layer control,
 * floating legend, and comprehensive hotspot detail panel.
 *
 * DBSCAN hotspots are ANALYTICAL SPATIAL CLUSTERS — not proven criminal zones.
 * Predictive risk heatmap uses Phase 9 XGBoost risk aggregation.
 * Frontend marker clustering is visual performance, NOT statistical analysis.
 */

'use strict';

const GISMap = (() => {
  const API = '';  // same-origin — served from FastAPI

  let _map = null;
  let _heatLayer = null;
  let _hotspotLayer = null;
  let _eventsLayer = null;
  let _highRiskLayer = null;
  let _predictedLayer = null;
  let _catchmentLayer = null;
  let _atmLayer = null;
  let _heatData = [];
  let _hotspotsGeoJSON = null;
  let _predictedDataCache = null;
  let _isLoadingPredicted = false;
  let _currentFilters = {};

  function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Exact Professional GIS Density Gradient (Prompt Specification):
  // 0.0 -> Dark blue (near-transparent), 0.2 -> Blue, 0.4 -> Cyan, 0.6 -> Green, 0.75 -> Yellow, 0.85 -> Orange, 1.0 -> Red
  const PROFESSIONAL_HEAT_GRADIENT = {
    0.00: '#03045e',   // Dark blue (near-transparent at lowest end)
    0.20: '#0077b6',   // Blue
    0.40: '#00b4d8',   // Cyan
    0.60: '#2ecc71',   // Green
    0.75: '#f1c40f',   // Yellow
    0.85: '#e67e22',   // Orange
    1.00: '#e74c3c',   // Red
  };

  function riskColor(score) {
    if (score === null || score === undefined) return '#64748B';
    if (score >= 80) return '#EF4444';
    if (score >= 60) return '#FB923C';
    if (score >= 40) return '#FACC15';
    return '#22C55E';
  }

  function riskChip(cat) {
    return `<span class="risk-chip ${cat || ''}">${cat || 'N/A'}</span>`;
  }

  function fmt(v, suffix = '') {
    if (v === null || v === undefined || v === '') return 'Not available';
    return `${v}${suffix}`;
  }

  // Zoom-aware radius (~25-35px) and blur (~15-25px) for smooth spatial transitions
  function _getHeatmapParams(zoom) {
    if (zoom <= 6) return { radius: 25, blur: 16 };
    if (zoom <= 7) return { radius: 30, blur: 20 };
    if (zoom <= 8) return { radius: 34, blur: 22 };
    if (zoom <= 10) return { radius: 40, blur: 24 };
    return { radius: 48, blur: 25 };
  }

  function _updateHeatmapForZoom() {
    if (!_map || !_heatLayer) return;
    const currentZoom = _map.getZoom();
    const p = _getHeatmapParams(currentZoom);
    if (typeof _heatLayer.setOptions === 'function') {
      _heatLayer.setOptions({
        radius: p.radius,
        blur: p.blur,
      });
    }
  }

  // ── Initialise map ────────────────────────────────────────────────
  function init() {
    _map = L.map('map', {
      center: [13.5, 79.0],  // South India
      zoom: 7,
      zoomControl: false,    // Placed at bottomleft below
      attributionControl: true,
    });

    // High-Contrast Key-Less ESRI Dark Gray Canvas (Zero Watermarks, 100% Reliable)
    const baseTile = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 16,
      attribution: '&copy; <a href="https://www.esri.com/">Esri</a> &mdash; Esri, DeLorme, NAVTEQ',
    }).addTo(_map);

    let _tileErrors = 0;
    baseTile.on('tileerror', () => {
      _tileErrors++;
      if (_tileErrors >= 6) {
        const banner = document.getElementById('map-notification-banner');
        if (banner) {
          banner.textContent = 'Map tiles unavailable. Geospatial records could not be displayed.';
          banner.style.display = 'block';
        }
      }
    });

    // High-Contrast Reference Overlay for Crisp Labels & Boundaries
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 16,
      attribution: '',
    }).addTo(_map);

    // Zoom Controls at bottom-left as requested
    L.control.zoom({ position: 'bottomleft' }).addTo(_map);

    // Recenter Control at bottom-left
    const RecenterControl = L.Control.extend({
      options: { position: 'bottomleft' },
      onAdd: function() {
        const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-recenter');
        const btn = L.DomUtil.create('a', 'leaflet-recenter-btn', container);
        btn.href = '#';
        btn.title = 'Recenter to South India Jurisdiction';
        btn.innerHTML = '⟲';
        btn.setAttribute('role', 'button');
        btn.setAttribute('aria-label', 'Recenter Map');
        L.DomEvent.disableClickPropagation(container);
        L.DomEvent.on(btn, 'click', function(e) {
          L.DomEvent.preventDefault(e);
          _map.fitBounds([[8.5, 74.4], [17.7, 83.3]]);
        });
        return container;
      }
    });
    new RecenterControl().addTo(_map);

    // Scale Bar at bottom-left as requested
    L.control.scale({ position: 'bottomleft', metric: true, imperial: false }).addTo(_map);

    // Fit to dataset bounding box (South India)
    _map.fitBounds([[8.5, 74.4], [17.7, 83.3]]);
    window.mapInstance = _map;

    // Listen to zoom changes for zoom-aware heatmap rendering
    _map.on('zoomend', _updateHeatmapForZoom);

    // Initialize layer groups for Predicted Cashout Corridors
    _predictedLayer = L.layerGroup();
    _catchmentLayer = L.layerGroup();
    _atmLayer = L.layerGroup();

    // Invalidate size on window resize and after initial layout
    window.addEventListener('resize', () => {
      if (_map) _map.invalidateSize();
    });
    setTimeout(() => {
      if (_map) _map.invalidateSize();
    }, 250);

    // Setup Fullscreen map button
    const btnFullscreen = document.getElementById('btn-fullscreen-map');
    if (btnFullscreen) {
      btnFullscreen.addEventListener('click', () => {
        const wrap = document.getElementById('map-wrap');
        if (!wrap) return;
        if (!document.fullscreenElement) {
          wrap.requestFullscreen().catch(err => {
            console.warn('Fullscreen error:', err);
          });
        } else {
          document.exitFullscreen();
        }
      });
    }

    document.addEventListener('fullscreenchange', () => {
      const isFull = !!document.fullscreenElement;
      const btn = document.getElementById('btn-fullscreen-map');
      if (btn) {
        btn.textContent = isFull ? '✕ Exit Fullscreen' : '⛶ Fullscreen';
      }
      setTimeout(() => {
        if (_map) _map.invalidateSize();
      }, 150);
    });
  }

  // ── Heatmap layer ─────────────────────────────────────────────────
  async function loadHeatmap(filters = {}, metric = 'risk') {
    _currentFilters = filters;
    const bannerEl = document.getElementById('map-notification-banner');

    try {
      const params = new URLSearchParams();
      if (filters.start_time)     params.set('start_time', filters.start_time);
      if (filters.end_time)       params.set('end_time', filters.end_time);
      if (filters.crime_category) params.set('crime_category', filters.crime_category);
      if (filters.crime_type)     params.set('crime_type', filters.crime_type);
      if (filters.risk_category)  params.set('risk_category', filters.risk_category);
      if (filters.min_risk_score !== undefined && filters.min_risk_score !== '') params.set('min_risk_score', filters.min_risk_score);
      if (filters.max_risk_score !== undefined && filters.max_risk_score !== '') params.set('max_risk_score', filters.max_risk_score);
      if (filters.hotspot_id !== undefined && filters.hotspot_id !== '') params.set('hotspot_id', filters.hotspot_id);
      if (filters.hotspot_only)   params.set('hotspot_only', 'true');
      if (metric)                 params.set('metric', metric);

      const qs = params.toString();
      const url = qs ? `${API}/gis/risk-heatmap?${qs}` : `${API}/gis/risk-heatmap`;

      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      _heatData = [];
      if (data.features && data.features.length > 0) {
        // Collect raw metric values for dynamic normalization across the filtered dataset
        const rawPoints = [];
        data.features.forEach(f => {
          if (!f.geometry || !f.geometry.coordinates) return;
          const [lon, lat] = f.geometry.coordinates;
          if (lat === null || lon === null || (lat === 0 && lon === 0)) return;

          let rawVal;
          if (metric === 'density') {
            rawVal = (f.properties && f.properties.event_count !== undefined && f.properties.event_count !== null)
              ? Number(f.properties.event_count)
              : Number(f.properties && f.properties.heatmap_weight ? f.properties.heatmap_weight : 0.15);
          } else {
            rawVal = (f.properties && f.properties.average_risk_score !== undefined && f.properties.average_risk_score !== null)
              ? Number(f.properties.average_risk_score)
              : (f.properties && f.properties.heatmap_weight ? Number(f.properties.heatmap_weight) * 100 : 30);
          }
          rawPoints.push({ lat, lon, val: rawVal });
        });

        if (rawPoints.length > 0) {
          const vals = rawPoints.map(p => p.val);
          const minVal = Math.min(...vals);
          const maxVal = Math.max(...vals);
          const valRange = maxVal - minVal;

          rawPoints.forEach(p => {
            let normalized;
            if (valRange > 0.001) {
              // Normalize dataset to [0.05, 1.0] so top clusters reach vivid red/orange/yellow
              // and lowest-risk areas fade into near-transparent dark blue
              const ratio = (p.val - minVal) / valRange;
              normalized = Math.min(1.0, Math.max(0.05, 0.05 + ratio * 0.95));
            } else {
              normalized = 0.55;
            }
            _heatData.push([p.lat, p.lon, Number(normalized.toFixed(4))]);
          });
        }
        if (bannerEl) bannerEl.style.display = 'none';
      } else {
        if (bannerEl) {
          bannerEl.textContent = 'No geospatial records available for the selected filters';
          bannerEl.style.display = 'block';
        }
      }

      if (_heatLayer) { _map.removeLayer(_heatLayer); }

      const zParams = _getHeatmapParams(_map ? _map.getZoom() : 7);

      _heatLayer = L.heatLayer(_heatData, {
        radius: zParams.radius,
        blur: zParams.blur,
        maxZoom: 6,
        gradient: PROFESSIONAL_HEAT_GRADIENT,
        minOpacity: 0.05,
        max: 1.0,
      });

      if (document.getElementById('layer-heatmap')?.checked) {
        _heatLayer.addTo(_map);
      }

      return data.total_districts !== undefined ? data.total_districts : _heatData.length;
    } catch (e) {
      console.warn('Heatmap load failed:', e);
      if (bannerEl) {
        bannerEl.textContent = 'Heatmap data unavailable.';
        bannerEl.style.display = 'block';
      }
      return 0;
    }
  }

  // ── Hotspot layer ─────────────────────────────────────────────────
  async function loadHotspots() {
    try {
      const res = await fetch(`${API}/gis/hotspots`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      _hotspotsGeoJSON = data;

      if (_hotspotLayer) { _map.removeLayer(_hotspotLayer); }
      _hotspotLayer = L.layerGroup();

      data.features.forEach(feat => {
        const p = feat.properties;
        const [lon, lat] = feat.geometry.coordinates;

        const el = document.createElement('div');
        el.className = 'hotspot-marker';
        const inner = document.createElement('div');
        inner.className = `hs-circle ${p.hotspot_status || ''}`;
        inner.innerHTML = `<span class="hs-lbl">H${p.hotspot_id}</span>`;
        el.appendChild(inner);

        const icon = L.divIcon({
          html: el.outerHTML,
          className: 'custom-hs-div-icon',
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([lat, lon], { icon });

        const popup = `
          <div class="popup-title">⬡ Analytical Hotspot HS-${p.hotspot_id}</div>
          <div class="popup-row"><span class="popup-key">Rank</span><span class="popup-val">#${fmt(p.hotspot_rank)}</span></div>
          <div class="popup-row"><span class="popup-key">Status</span><span class="popup-val">${(p.hotspot_status||'').replace('_',' ')}</span></div>
          <div class="popup-row"><span class="popup-key">Event Count</span><span class="popup-val">${fmt(p.event_count)}</span></div>
          <div class="popup-row"><span class="popup-key">Avg Risk Score</span><span class="popup-val" style="color:${riskColor(p.average_risk_score)}">${fmt(p.average_risk_score)}</span></div>
          <div class="popup-row"><span class="popup-key">Dominant Crime</span><span class="popup-val">${fmt(p.dominant_crime_type)}</span></div>
          <div class="popup-row"><span class="popup-key">Withdrawal Events</span><span class="popup-val">${fmt(p.withdrawal_event_count)}</span></div>
          <div class="popup-row"><span class="popup-key">Time Range</span><span class="popup-val">${(p.time_range_start||'').slice(0,10)}</span></div>
          <button class="popup-btn" onclick="GISMap.showHotspotDetail(${p.hotspot_id})">View Analytical Hotspot Detail →</button>
          <div class="popup-disc">DBSCAN analytical spatial cluster — not proof of criminal activity.</div>
        `;
        marker.bindPopup(popup, { maxWidth: 260 });
        marker.on('click', () => GISMap.showHotspotDetail(p.hotspot_id));
        _hotspotLayer.addLayer(marker);
      });

      if (document.getElementById('layer-hotspots')?.checked) {
        _hotspotLayer.addTo(_map);
      }

      const clusterCountEl = document.getElementById('map-cluster-count');
      if (clusterCountEl) clusterCountEl.textContent = `${data.total} hotspots`;
      return data.total;
    } catch (e) {
      console.warn('Hotspot load failed:', e);
      return 0;
    }
  }

  // ── Event points layer ────────────────────────────────────────────
  async function loadEvents(filters = {}) {
    try {
      const params = new URLSearchParams({ limit: 2000 });
      if (filters.start_time)     params.set('start_time', filters.start_time);
      if (filters.end_time)       params.set('end_time', filters.end_time);
      if (filters.crime_category) params.set('crime_category', filters.crime_category);
      if (filters.crime_type)     params.set('crime_type', filters.crime_type);
      if (filters.risk_category)  params.set('risk_category', filters.risk_category);
      if (filters.min_risk_score !== undefined) params.set('min_risk_score', filters.min_risk_score);
      if (filters.max_risk_score !== undefined) params.set('max_risk_score', filters.max_risk_score);
      if (filters.hotspot_id !== undefined && filters.hotspot_id !== '') params.set('hotspot_id', filters.hotspot_id);
      if (filters.hotspot_only)   params.set('hotspot_only', 'true');

      const res = await fetch(`${API}/gis/events?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // Remove old event layers
      if (_eventsLayer)   { _map.removeLayer(_eventsLayer); }
      if (_highRiskLayer) { _map.removeLayer(_highRiskLayer); }

      // MarkerCluster for all events
      _eventsLayer = L.markerClusterGroup({
        maxClusterRadius: 50,
        disableClusteringAtZoom: 12,
        iconCreateFunction: cluster => {
          const n = cluster.getChildCount();
          return L.divIcon({
            html: `<div style="background:rgba(56,139,253,0.8);color:#fff;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;border:2px solid rgba(56,139,253,1)">${n}</div>`,
            className: '',
            iconSize: [34, 34],
            iconAnchor: [17, 17],
          });
        },
      });

      // Layer for HIGH/CRITICAL only
      _highRiskLayer = L.layerGroup();

      data.features.forEach(feat => {
        const p = feat.properties;
        const [lon, lat] = feat.geometry.coordinates;
        const rc = p.risk_category || '';
        const score = p.risk_score;

        const color = riskColor(score);
        const sz = (rc === 'CRITICAL' || rc === 'HIGH') ? 10 : 7;

        const icon = L.circleMarker([lat, lon], {
          radius: sz,
          fillColor: color,
          color: color,
          weight: 1,
          fillOpacity: 0.75,
          opacity: 0.9,
        });

        const popupHtml = `
          <div class="popup-title" style="color:${color}">Predictive Risk Record</div>
          <div class="popup-row"><span class="popup-key">Crime Type</span><span class="popup-val">${fmt(p.crime_type)}</span></div>
          <div class="popup-row"><span class="popup-key">Category</span><span class="popup-val">${fmt(p.crime_category_group)}</span></div>
          <div class="popup-row"><span class="popup-key">District</span><span class="popup-val">${fmt(p.victim_district)}</span></div>
          <div class="popup-row"><span class="popup-key">Predictive Risk Score</span><span class="popup-val" style="color:${color}">${fmt(score)} / 100</span></div>
          <div class="popup-row"><span class="popup-key">Risk Category</span><span class="popup-val">${riskChip(rc)}</span></div>
          <div class="popup-row"><span class="popup-key">Analytical Hotspot</span><span class="popup-val">${p.cluster_id !== null ? 'HS-'+p.cluster_id : 'Unassigned'}</span></div>
          <div class="popup-row"><span class="popup-key">Timestamp</span><span class="popup-val">${(p.complaint_timestamp||'').slice(0,16)}</span></div>
          <div class="popup-disc">Model-derived analytical signal — not proof of criminal activity.</div>
        `;
        icon.bindPopup(popupHtml, { maxWidth: 250 });

        _eventsLayer.addLayer(icon);

        if (rc === 'HIGH' || rc === 'CRITICAL') {
          const hIcon = L.circleMarker([lat, lon], {
            radius: 9,
            fillColor: color,
            color: '#fff',
            weight: 1.5,
            fillOpacity: 0.85,
          });
          hIcon.bindPopup(popupHtml, { maxWidth: 250 });
          _highRiskLayer.addLayer(hIcon);
        }
      });

      const eventsChk = document.getElementById('layer-events');
      const highChk   = document.getElementById('layer-high-risk');
      if (eventsChk?.checked) _eventsLayer.addTo(_map);
      if (highChk?.checked)   _highRiskLayer.addTo(_map);

      const eventCountEl = document.getElementById('map-event-count');
      if (eventCountEl) {
        eventCountEl.textContent = `${data.total_matching?.toLocaleString() || data.records_returned} events`;
      }
      return data.records_returned;
    } catch (e) {
      console.warn('Events load failed:', e);
      const eventCountEl = document.getElementById('map-event-count');
      if (eventCountEl) eventCountEl.textContent = 'events unavailable';
      return 0;
    }
  }

  // ── Predicted Cashout Corridors layer (Phase 7) ───────────────────
  async function loadPredictedLocations(force = false) {
    if (_isLoadingPredicted) return;
    const badge = document.getElementById('corridor-status-badge');
    const loadingEl = document.getElementById('corridor-loading');
    const emptyEl = document.getElementById('corridor-empty');
    const errorEl = document.getElementById('corridor-error');

    if (!force && _predictedDataCache && _predictedDataCache.features) {
      renderPredictedLocations();
      if (badge) badge.textContent = `Active (${_predictedDataCache.features.length})`;
      return;
    }

    _isLoadingPredicted = true;
    if (loadingEl) loadingEl.style.display = 'block';
    if (emptyEl) emptyEl.style.display = 'none';
    if (errorEl) errorEl.style.display = 'none';
    if (badge) badge.textContent = 'Loading...';

    try {
      const res = await fetch(`${API}/gis/predicted-locations?radius_km=5.0&limit=50`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: Failed to fetch predicted locations`);
      }
      const data = await res.json();
      _predictedDataCache = data;

      if (loadingEl) loadingEl.style.display = 'none';

      if (!data.features || data.features.length === 0) {
        if (emptyEl) emptyEl.style.display = 'block';
        if (badge) badge.textContent = '0 Corridors';
        clearPredictedLayers();
        return;
      }

      if (badge) badge.textContent = `Active (${data.features.length})`;
      renderPredictedLocations();
    } catch (err) {
      console.warn('Predicted locations load error:', err.message);
      if (loadingEl) loadingEl.style.display = 'none';
      if (errorEl) errorEl.style.display = 'block';
      if (badge) badge.textContent = 'Error';
      clearPredictedLayers();
    } finally {
      _isLoadingPredicted = false;
    }
  }

  function clearPredictedLayers() {
    if (_predictedLayer) _predictedLayer.clearLayers();
    if (_catchmentLayer) _catchmentLayer.clearLayers();
    if (_atmLayer) _atmLayer.clearLayers();
  }

  function renderPredictedLocations() {
    if (!_map || !_predictedDataCache || !_predictedDataCache.features) return;

    clearPredictedLayers();

    const minRisk = document.getElementById('filter-corridor-risk')?.value || 'ALL';
    const limitK = parseInt(document.getElementById('filter-corridor-limit')?.value || '50', 10);
    const showCatchments = document.getElementById('toggle-catchment-circles')?.checked !== false;
    const showATMs = document.getElementById('toggle-atm-markers')?.checked !== false;
    const isLayerActive = document.getElementById('layer-predicted-locations')?.checked ||
                          document.getElementById('toggle-predicted-layer')?.checked;

    let displayedCount = 0;
    const emptyEl = document.getElementById('corridor-empty');

    let rejectedCount = 0;
    const features = _predictedDataCache.features;
    for (let i = 0; i < features.length; i++) {
      if (displayedCount >= limitK) break;

      const feat = features[i];
      if (!feat.geometry || !feat.geometry.coordinates) {
        rejectedCount++;
        continue;
      }
      const [lon, lat] = feat.geometry.coordinates;

      // Coordinate validation: must be finite numbers within WGS 84 bounds
      if (typeof lat !== 'number' || typeof lon !== 'number' ||
          !Number.isFinite(lat) || !Number.isFinite(lon) ||
          lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        rejectedCount++;
        continue;
      }

      const p = feat.properties || {};
      const avgScore = Number(p.average_risk_score ?? 50);
      const cat = (p.risk_category || '').toUpperCase();

      // Filter by minRisk
      if (minRisk === 'CRITICAL' && avgScore < 75 && cat !== 'CRITICAL') continue;
      if (minRisk === 'HIGH' && avgScore < 50 && cat !== 'HIGH' && cat !== 'CRITICAL') continue;
      if (minRisk === 'MODERATE' && avgScore < 30) continue;

      displayedCount++;
      const rank = p.rank || displayedCount;
      const rankColor = riskColor(avgScore);
      const rankLabel = p.ranking_label ? p.ranking_label.replace(/_/g, ' ') : 'HIGH PRIORITY CANDIDATE';

      // 1. Centroid Pin Marker
      const pinHtml = `
        <div class="predicted-corridor-marker" title="Predicted Cashout Corridor #${rank} (${esc(p.district)})">
          <div class="predicted-pin" style="border-color:${rankColor};">
            #${rank}
          </div>
        </div>
      `;
      const icon = L.divIcon({
        html: pinHtml,
        className: 'custom-predicted-div-icon',
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14],
      });

      const marker = L.marker([lat, lon], { icon });

      // Build Safe, Structured Popup
      const popupContent = `
        <div class="corridor-popup-wrap">
          <div class="corridor-popup-header">
            <div class="corridor-popup-title">
              <span>🟣 Predicted Corridor #${rank}</span>
            </div>
            <div class="corridor-popup-subtitle">
              ${esc(p.district || 'Regional Center')} · Cluster HS-${esc(p.cluster_id ?? 'N/A')}
            </div>
          </div>
          <div class="corridor-popup-grid">
            <div class="corridor-popup-row">
              <span class="corridor-popup-key">Risk Tier:</span>
              <span class="corridor-popup-val">${riskChip(p.risk_category || 'MODERATE')}</span>
            </div>
            <div class="corridor-popup-row">
              <span class="corridor-popup-key">Model Risk Score:</span>
              <span class="corridor-popup-val" style="color:${rankColor}">${avgScore.toFixed(1)} / 100</span>
            </div>
            <div class="corridor-popup-row">
              <span class="corridor-popup-key">Withdrawal Prob:</span>
              <span class="corridor-popup-val">${p.predicted_probability != null ? (Number(p.predicted_probability) * 100).toFixed(1) + '%' : 'N/A'}</span>
            </div>
            <div class="corridor-popup-row">
              <span class="corridor-popup-key">Priority Status:</span>
              <span class="corridor-popup-val" style="font-size:10.5px;color:${rankColor}">${esc(rankLabel)}</span>
            </div>
            <div class="corridor-popup-row">
              <span class="corridor-popup-key">Nearest ATM:</span>
              <span class="corridor-popup-val" style="font-family:var(--font-mono)">${esc(p.nearest_atm_id || 'Not recorded')}</span>
            </div>
            <div class="corridor-popup-row">
              <span class="corridor-popup-key">ATM Proximity:</span>
              <span class="corridor-popup-val">${p.nearest_atm_distance_km != null ? p.nearest_atm_distance_km + ' km' : 'N/A'}</span>
            </div>
            <div class="corridor-popup-row">
              <span class="corridor-popup-key">ATMs in 5 km:</span>
              <span class="corridor-popup-val">${p.catchment_5_0km_atm_count ?? p.atm_count_in_radius ?? 0} ATMs</span>
            </div>
            <div class="corridor-popup-row">
              <span class="corridor-popup-key">Est. Centroid:</span>
              <span class="corridor-popup-val" style="font-size:10px;">[${lat.toFixed(4)}, ${lon.toFixed(4)}]</span>
            </div>
            <div class="corridor-popup-row">
              <span class="corridor-popup-key">Data Source:</span>
              <span class="corridor-popup-val" style="font-size:10px;">${esc(p.location_source || 'historical_dbscan')}</span>
            </div>
          </div>
          <div class="corridor-popup-warning">
            ⚠️ <strong>NOTICE:</strong> This location is an estimated risk area based on historical
            patterns and model results. It is NOT a confirmed criminal location or guaranteed withdrawal.
          </div>
        </div>
      `;
      marker.bindPopup(popupContent, { maxWidth: 300 });
      _predictedLayer.addLayer(marker);

      // 2. 5 km Catchment Circle (if enabled)
      if (showCatchments) {
        const circle = L.circle([lat, lon], {
          radius: 5000,
          color: '#a855f7',
          weight: 1.5,
          opacity: 0.7,
          fillColor: '#a855f7',
          fillOpacity: 0.07,
          dashArray: '4, 4',
        });
        circle.bindTooltip(`Corridor #${rank} Catchment (5 km)`, { sticky: true });
        _catchmentLayer.addLayer(circle);
      }

      // 3. Nearby Physical ATMs (if enabled)
      if (showATMs && Array.isArray(p.nearby_atms)) {
        p.nearby_atms.forEach(atm => {
          const aLat = Number(atm.latitude);
          const aLon = Number(atm.longitude);
          if (!Number.isFinite(aLat) || !Number.isFinite(aLon) || aLat < -90 || aLat > 90 || aLon < -180 || aLon > 180) return;

          const atmHtml = `
            <div class="atm-marker-node" title="ATM ${esc(atm.atm_id)} (${esc(atm.bank_id)})">
              <div class="atm-pin">🏧</div>
            </div>
          `;
          const atmIcon = L.divIcon({
            html: atmHtml,
            className: 'custom-atm-div-icon',
            iconSize: [22, 22],
            iconAnchor: [11, 11],
            popupAnchor: [0, -11],
          });

          const atmMarker = L.marker([aLat, aLon], { icon: atmIcon });
          const atmPopup = `
            <div style="font-size:12px;min-width:180px;font-family:var(--font-sans)">
              <div style="font-weight:700;color:#0284c7;margin-bottom:4px">🏧 Physical ATM Terminal</div>
              <div><strong>ID:</strong> <code>${esc(atm.atm_id)}</code></div>
              <div><strong>Bank Network:</strong> ${esc(atm.bank_id || 'N/A')}</div>
              <div><strong>Type:</strong> ${esc(atm.atm_type || 'ATM')}</div>
              <div><strong>Distance from Corridor #${rank}:</strong> ${atm.distance_km != null ? atm.distance_km + ' km' : 'N/A'}</div>
              <div><strong>24x7 Operation:</strong> ${atm.is_24x7 ? '✅ Yes' : '❌ No'}</div>
              <div style="font-size:10px;color:var(--text-muted);margin-top:6px;border-top:1px solid var(--border);padding-top:4px">
                Physical ATM infrastructure mapping (ATMs_Locations.csv).
              </div>
            </div>
          `;
          atmMarker.bindPopup(atmPopup, { maxWidth: 240 });
          _atmLayer.addLayer(atmMarker);
        });
      }
    }

    if (rejectedCount > 0) {
      console.warn(`[GISMap] Safely rejected ${rejectedCount} predicted location records with invalid or out-of-bounds coordinates.`);
    }

    if (emptyEl) {
      emptyEl.style.display = displayedCount === 0 ? 'block' : 'none';
    }

    // Attach layers if master toggle is on
    if (isLayerActive) {
      if (!_map.hasLayer(_predictedLayer)) _predictedLayer.addTo(_map);
      if (showCatchments && !_map.hasLayer(_catchmentLayer)) _catchmentLayer.addTo(_map);
      if (!showCatchments && _map.hasLayer(_catchmentLayer)) _map.removeLayer(_catchmentLayer);
      if (showATMs && !_map.hasLayer(_atmLayer)) _atmLayer.addTo(_map);
      if (!showATMs && _map.hasLayer(_atmLayer)) _map.removeLayer(_atmLayer);
    }
  }

  // ── Layer visibility toggles ──────────────────────────────────────
  function setupLayerToggles() {
    const heatCb = document.getElementById('layer-heatmap');
    const hsCb   = document.getElementById('layer-hotspots');
    const evCb   = document.getElementById('layer-events');
    const hrCb   = document.getElementById('layer-high-risk');
    const predCb = document.getElementById('layer-predicted-locations');
    const xgbTog = document.getElementById('toggle-xgb-layer');
    const dbsTog = document.getElementById('toggle-dbs-layer');
    const predTog= document.getElementById('toggle-predicted-layer');
    const badge  = document.getElementById('corridor-status-badge');

    heatCb?.addEventListener('change', e => {
      if (xgbTog) xgbTog.checked = e.target.checked;
      if (!_heatLayer) return;
      e.target.checked ? _heatLayer.addTo(_map) : _map.removeLayer(_heatLayer);
    });

    xgbTog?.addEventListener('change', e => {
      if (heatCb) heatCb.checked = e.target.checked;
      if (!_heatLayer) return;
      e.target.checked ? _heatLayer.addTo(_map) : _map.removeLayer(_heatLayer);
    });

    hsCb?.addEventListener('change', e => {
      if (dbsTog) dbsTog.checked = e.target.checked;
      if (!_hotspotLayer) return;
      e.target.checked ? _hotspotLayer.addTo(_map) : _map.removeLayer(_hotspotLayer);
    });

    dbsTog?.addEventListener('change', e => {
      if (hsCb) hsCb.checked = e.target.checked;
      if (!_hotspotLayer) return;
      e.target.checked ? _hotspotLayer.addTo(_map) : _map.removeLayer(_hotspotLayer);
    });

    // Predicted Cashout Corridors layer toggles
    function handlePredictedToggle(checked) {
      if (predCb) predCb.checked = checked;
      if (predTog) predTog.checked = checked;

      if (checked) {
        loadPredictedLocations();
      } else {
        if (_predictedLayer && _map.hasLayer(_predictedLayer)) _map.removeLayer(_predictedLayer);
        if (_catchmentLayer && _map.hasLayer(_catchmentLayer)) _map.removeLayer(_catchmentLayer);
        if (_atmLayer && _map.hasLayer(_atmLayer)) _map.removeLayer(_atmLayer);
        if (badge) badge.textContent = 'Off';
      }
    }

    predCb?.addEventListener('change', e => handlePredictedToggle(e.target.checked));
    predTog?.addEventListener('change', e => handlePredictedToggle(e.target.checked));

    // Corridor Filter Controls
    document.getElementById('filter-corridor-risk')?.addEventListener('change', () => {
      renderPredictedLocations();
    });

    document.getElementById('filter-corridor-limit')?.addEventListener('change', () => {
      renderPredictedLocations();
    });

    document.getElementById('toggle-catchment-circles')?.addEventListener('change', e => {
      if (!_map || !_catchmentLayer) return;
      const isLayerActive = predCb?.checked || predTog?.checked;
      if (isLayerActive) {
        e.target.checked ? _catchmentLayer.addTo(_map) : _map.removeLayer(_catchmentLayer);
      }
    });

    document.getElementById('toggle-atm-markers')?.addEventListener('change', e => {
      if (!_map || !_atmLayer) return;
      const isLayerActive = predCb?.checked || predTog?.checked;
      if (isLayerActive) {
        e.target.checked ? _atmLayer.addTo(_map) : _map.removeLayer(_atmLayer);
      }
    });

    document.getElementById('btn-retry-corridors')?.addEventListener('click', () => {
      loadPredictedLocations(true);
    });

    evCb?.addEventListener('change', e => {
      if (!_eventsLayer) return;
      e.target.checked ? _eventsLayer.addTo(_map) : _map.removeLayer(_eventsLayer);
    });

    hrCb?.addEventListener('change', e => {
      if (!_highRiskLayer) return;
      e.target.checked ? _highRiskLayer.addTo(_map) : _map.removeLayer(_highRiskLayer);
    });

    document.getElementById('heatmap-metric-select')?.addEventListener('change', e => {
      const metric = e.target.value || 'risk';
      loadHeatmap(_currentFilters, metric);
      const metricLegendLabel = document.getElementById('legend-active-metric');
      if (metricLegendLabel) {
        metricLegendLabel.textContent = metric === 'density' ? 'Complaint Volume Density' : 'Predictive Risk Density (XGBoost)';
      }
    });

    document.getElementById('btn-reset-map-view')?.addEventListener('click', () => {
      if (_map) {
        _map.fitBounds([[8.5, 74.4], [17.7, 83.3]]);
      }
    });
  }

  // ── Hotspot detail drill-down ─────────────────────────────────────
  async function showHotspotDetail(hotspotId) {
    const panel  = document.getElementById('detail-panel');
    const body   = document.getElementById('detail-body');
    const title  = document.getElementById('detail-title');

    title.textContent = `HOTSPOT DETAILS · HS-${hotspotId}`;
    body.innerHTML = '<div class="loading-text">Loading analytical hotspot details…</div>';
    panel.classList.add('open');

    try {
      const res = await fetch(`/gis/hotspots/${hotspotId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const d = await res.json();

      const dowNames = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

      let riskBars = '';
      if (d.risk_distribution) {
        const rd = d.risk_distribution;
        const total = (rd.low||0) + (rd.moderate||0) + (rd.high||0) + (rd.critical||0);
        if (total > 0) {
          const pct = v => total > 0 ? Math.round((v||0)/total*100) : 0;
          riskBars = `
            <div class="detail-section-title">XGBoost Risk Summary</div>
            ${['low','moderate','high','critical'].map(k => `
              <div class="risk-bar-row">
                <div class="risk-bar-label"><span>${k.toUpperCase()}</span><span>${rd[k]||0} (${pct(rd[k])}%)</span></div>
                <div class="risk-bar-bg"><div class="risk-bar-fill fill-${k}" style="width:${pct(rd[k])}%"></div></div>
              </div>
            `).join('')}
            ${row('High-Risk Complaints', fmt(d.high_risk_count))}
            ${row('Critical-Risk Complaints', fmt(d.critical_risk_count))}
            ${row('Priority Class', rd.priority_class || 'Not available')}
          `;
        }
      }

      const tempoInfo = d.temporal_info || {};
      const timeRangeStr = (d.time_range_start && d.time_range_end) 
        ? `${d.time_range_start.slice(0,10)} to ${d.time_range_end.slice(0,10)}` 
        : 'Not available';

      body.innerHTML = `
        <div class="detail-section-title">HOTSPOT DETAILS</div>
        ${row('Hotspot ID', 'HS-' + (d.hotspot_id !== undefined ? d.hotspot_id : 'Not available'))}
        ${row('Event Count', fmt(d.event_count))}
        ${row('Average Risk', d.average_risk_score !== null && d.average_risk_score !== undefined ? `<span style="color:${riskColor(d.average_risk_score)};font-weight:700">${d.average_risk_score} / 100</span>` : 'Not available')}
        ${row('Maximum Risk', d.maximum_risk_score !== null && d.maximum_risk_score !== undefined ? `<span style="color:${riskColor(d.maximum_risk_score)};font-weight:700">${d.maximum_risk_score} / 100</span>` : 'Not available')}
        ${row('Dominant Crime Category', fmt(d.dominant_crime_type))}
        ${row('Time Range', timeRangeStr)}

        ${riskBars}

        <div class="detail-section-title">DBSCAN Cluster Information</div>
        ${row('Status', (d.hotspot_status||'').replace('_',' ') || 'Not available')}
        ${row('Cluster Rank', d.hotspot_rank ? '#' + d.hotspot_rank : 'Not available')}
        ${row('Centroid Coordinates', d.centroid_latitude ? `${d.centroid_latitude}°N, ${d.centroid_longitude}°E` : 'Not available')}
        ${row('Cluster Radius', fmt(d.cluster_radius_km, ' km'))}
        ${row('Density Metric', fmt(d.density_metric))}
        ${row('Withdrawal Events', fmt(d.withdrawal_event_count))}
        ${row('Active Time Span', fmt(tempoInfo.time_span_days, ' days'))}
        ${row('Peak Activity Hour', tempoInfo.peak_hour_of_day !== null && tempoInfo.peak_hour_of_day !== undefined ? `${tempoInfo.peak_hour_of_day}:00 hrs` : 'Not available')}
        ${row('Peak Activity Day', tempoInfo.peak_day_of_week !== null && tempoInfo.peak_day_of_week !== undefined ? (dowNames[tempoInfo.peak_day_of_week] || tempoInfo.peak_day_of_week) : 'Not available')}

        <div style="font-size:11px;color:var(--text-secondary);padding:6px;background:var(--bg-card);border-radius:4px;margin-top:8px;margin-bottom:8px;border:1px solid var(--border-subtle);">
          Analytical Hotspot derived via DBSCAN (eps=500m, MinPts=3). Identifies spatial concentrations of historical complaints. Does NOT forecast future withdrawals or prove criminal intent.
        </div>

        <div class="panel-action-row">
          <button class="btn btn-sm btn-primary" onclick="GISMap.zoomToHotspot(${d.hotspot_id}, ${d.centroid_latitude}, ${d.centroid_longitude})">View Analysis</button>
          <a class="btn btn-sm btn-outline" href="/analyst/investigation.html?hotspot_id=${d.hotspot_id}&notes=Investigation%20opened%20for%20Analytical%20Hotspot%20HS-${d.hotspot_id}" target="_blank">Create Investigation ↗</a>
        </div>

        <div class="detail-disclaimer">${d.disclaimer || 'Analytical signals for decision support only.'}</div>
      `;
    } catch (e) {
      body.innerHTML = `<div class="error-text">Failed to load hotspot detail: ${e.message}</div>`;
    }
  }

  function zoomToHotspot(id, lat, lon) {
    if (_map && lat && lon) {
      _map.setView([lat, lon], 12);
    }
  }

  function row(key, val) {
    return `<div class="detail-row"><span class="detail-key">${key}</span><span class="detail-val">${val}</span></div>`;
  }

  // ── Public API ────────────────────────────────────────────────────
  return {
    init,
    loadHeatmap,
    loadHotspots,
    loadEvents,
    loadPredictedLocations,
    clearPredictedLayers,
    renderPredictedLocations,
    setupLayerToggles,
    showHotspotDetail,
    zoomToHotspot,
    invalidateSize: () => { if (_map) _map.invalidateSize(); },
    getMap: () => _map,
    getPredictedCache: () => _predictedDataCache,
  };
})();

// Expose for popup onclick
window.GISMap = GISMap;
