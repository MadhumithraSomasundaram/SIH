# Debugging & Resolution Report: Empty Dashboard Metrics and Blank GIS Map

**Project:** Cybercrime Risk Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** September 19, 2026  
**Status:** **RESOLVED & VERIFIED IN LIVE BROWSER**

---

## 1. Executive Summary

An urgent issue on the Overview Dashboard was diagnosed, fixed, and verified across all 7 evaluation phases:
1. **Initial Symptoms:**
   - All 6 KPI cards displayed placeholder dashes (`—`) instead of numerical values.
   - The Geospatial Risk Intelligence map container was completely blank.
   - Alert counts in the Alert Summary Card loaded successfully, but map layers and KPI cards remained unpopulated.
2. **Investigation & Resolution:**
   - Investigated browser runtime console and network layers.
   - Identified a fatal syntax parsing error in `dashboard/js/dashboard.js` that completely aborted script execution before `loadKPIs()` and `GISMap.init()` could be reached.
   - Corrected the bracket syntax defect, hardened the KPI loading logic with fallback schema resolution, enabled filter-aware KPI updates on the `/gis/summary` endpoint, and added tile error resilience to Leaflet.
   - Verified live in browser: all 6 KPI cards populate with real dataset values, Leaflet GIS map renders 10,000 events and 40 clusters, and filters update both KPI cards and map layers synchronously.

---

## 2. Root Cause Analysis

### 2.1 Root Cause of Empty KPI Values
In [`dashboard/js/dashboard.js`](file:///d:/SIH/SIH_2026/cybercrime_prediction/dashboard/js/dashboard.js), function `setupSystemStatusModal()` (line 165) was missing its closing brace `}` before `openComplaintIntakeModal()` (line 180):
```javascript
// BEFORE (Lines 175-181)
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
        closeSystemStatusModal();
      }
    });
  // ── 3c. Dynamic Complaint Intake Modal ──────────────────────────────
  function openComplaintIntakeModal() {
```
This unclosed brace cascaded through the IIFE, causing the JavaScript engine to throw:
```
SyntaxError: Unexpected token ')' at http://127.0.0.1:8000/dashboard/js/dashboard.js:864:1
```
Because the script terminated at parse time:
- `bootstrap()` was never reached.
- `loadKPIs()` was never called.
- The DOM elements (`#kpi-total-val`, `#kpi-high-val`, `#kpi-critical-val`, `#kpi-hotspot-val`, `#kpi-avg-risk-val`, `#kpi-area-val`) remained with their default HTML template content (`—`).
- `alerts.js` loaded in a separate script tag prior to `dashboard.js`, which is why alert counts were visible while dashboard KPIs and the map were not.

### 2.2 Root Cause of Blank GIS Map
Because of the same fatal syntax error in `dashboard.js`:
- `GISMap.init()` (line 845) was never executed.
- Leaflet map instance was never created inside `#map`.
- Tile layers, heatmaps (`GISMap.loadHeatmap()`), and hotspot clusters (`GISMap.loadHotspots()`) were never requested or mounted.
- The container `#map` remained an uninitialized, blank `<div>`.

---

## 3. Files Changed

### 1. [`dashboard/js/dashboard.js`](file:///d:/SIH/SIH_2026/cybercrime_prediction/dashboard/js/dashboard.js)
- **Syntax Correction:** Added the missing `}` to properly close `setupSystemStatusModal()`.
- **Hardened KPI Rendering:** Implemented `_safeNum()`, `_safeRisk()`, and `_safeStr()` to safely format numbers (even `0`), prevent `null`/`undefined`/`NaN` errors, and display `"Data unavailable"` instead of silent dashes (`—`) upon failure.
- **Dynamic Schema Resolution:** Added resolution for primary and alternative API field names:
  ```javascript
  const total = d.total_analytical_records ?? d.total ?? d.count ?? d.records ?? null;
  const high = d.high_risk_records ?? d.high_risk_count ?? d.high_risk ?? null;
  const critical = d.critical_risk_records ?? d.critical_risk_count ?? d.critical_risk ?? null;
  const hotspots = d.hotspot_count ?? d.hotspots ?? d.total_hotspots ?? null;
  const avgRisk = d.average_risk_score ?? d.average_risk ?? d.avg_risk ?? d.risk_score ?? null;
  const topArea = d.highest_risk_area ?? d.top_risk_area ?? d.area ?? d.highest_area ?? null;
  ```
- **Filter Synchronization:** Enhanced `loadKPIs(filters)` to accept filter query parameters and wired it into `onFiltersApply(filters)`, ensuring KPI cards update consistently whenever filters are applied or reset.
- **Layout Invalidation:** Called `GISMap.invalidateSize()` after DOM bootstrap.

### 2. [`dashboard/js/map.js`](file:///d:/SIH/SIH_2026/cybercrime_prediction/dashboard/js/map.js)
- **Map Invalidation:** Added `setTimeout(() => _map.invalidateSize(), 250)` upon map initialization and exported `invalidateSize()`.
- **Tile Error Detection:** Attached `tileerror` listener to base tiles to surface a clear, non-misleading notification: `"Map tiles unavailable. Geospatial records could not be displayed."` if tile servers are unreachable.
- **Empty State Notification:** Configured `#map-notification-banner` to display `"No geospatial records available for the selected filters"` if a filter combination yields 0 coordinates.
- **Coordinate Rejection Safety:** In `renderPredictedLocations()`, added validation counter and console logging for any coordinates outside WGS 84 bounds or non-numeric coordinates:
  ```javascript
  if (rejectedCount > 0) {
    console.warn(`[GISMap] Safely rejected ${rejectedCount} predicted location records with invalid or out-of-bounds coordinates.`);
  }
  ```

### 3. [`api/gis_routes.py`](file:///d:/SIH/SIH_2026/cybercrime_prediction/api/gis_routes.py)
- **Filtered Summary Support:** Extended `GET /gis/summary` to accept optional query filters:
  `start_time`, `end_time`, `crime_category`, `crime_type`, `risk_category`, `min_risk_score`, `max_risk_score`, `hotspot_id`, `hotspot_only`.
- Computes KPI values on the filtered slice while preserving 100% backward compatibility for unfiltered calls.

---

## 4. Endpoints Tested & Verified

| Endpoint | HTTP Method | Auth Header | Status | Response Summary |
| :--- | :---: | :---: | :---: | :--- |
| `/gis/summary` | GET | `X-API-Key` | `200 OK` | `total_analytical_records: 10000`, `high_risk_records: 5`, `critical_risk_records: 0`, `hotspot_count: 40`, `average_risk_score: 33.57`, `highest_risk_area: "Tiruchirappalli"` |
| `/gis/summary?risk_category=HIGH` | GET | `X-API-Key` | `200 OK` | `total_analytical_records: 5`, `high_risk_records: 5`, `average_risk_score: 61.0`, `highest_risk_area: "Tiruchirappalli"` |
| `/gis/predicted-locations?radius_km=5.0&limit=50` | GET | `X-API-Key` | `200 OK` | GeoJSON FeatureCollection with 40 candidate corridor features, nearest ATMs, and WGS 84 coordinates |
| `/gis/risk-heatmap` | GET | `X-API-Key` | `200 OK` | GeoJSON FeatureCollection with 40 cluster points and normalized weights |
| `/gis/hotspots` | GET | `X-API-Key` | `200 OK` | GeoJSON FeatureCollection with 40 DBSCAN hotspots (`HS-01` to `HS-40`) |
| `/gis/statistics` | GET | `X-API-Key` | `200 OK` | Risk, crime category, hourly distributions, top districts |
| `/gis/mule-pattern-accounts?limit=15&flagged_only=true` | GET | `X-API-Key` | `200 OK` | 15 flagged heuristic fan-in accounts |

---

## 5. Before-and-After Comparison

### KPI Cards Display
| KPI Card | Before Fix | After Fix (Initial Unfiltered) | After Fix (Filter: Risk = HIGH) | After Reset |
| :--- | :---: | :---: | :---: | :---: |
| **Analytical Records** | `—` | **10,000** | **5** | **10,000** |
| **High-Risk Records** | `—` | **5** | **5** | **5** |
| **Critical-Risk Records** | `—` | **0** | **0** | **0** |
| **Analytical Hotspots** | `—` | **40** | **40** | **40** |
| **Average Model Risk** | `—` | **33.6** | **61.0** | **33.6** |
| **Highest Risk Area** | `—` | **Tiruchirappalli** | **Tiruchirappalli** | **Tiruchirappalli** |

### GIS Map State
| Attribute | Before Fix | After Fix |
| :--- | :--- | :--- |
| **Map Initialization** | Not initialized (blank DOM) | Initialized Leaflet 1.9.4 map centered on South India `[13.5, 79.0]` |
| **Event Heatmap** | Missing | Rendered professional density gradient across 10,000 incidents |
| **Hotspot Clusters** | Missing | 40 DBSCAN clusters mounted with interactive details |
| **Map Event Counters** | `— events` | Displayed `10,000 events · 40 hotspots · Historical/Prototype` |
| **Console State** | `SyntaxError: Unexpected token ')'` | **0 errors, 0 warnings** |

---

## 6. Verification Evidence & Automated Tests

1. **Automated Regression Suite Execution:**
   ```bash
   pytest tests/test_api.py tests/test_gis_dashboard.py tests/test_predicted_locations.py -v
   ```
   **Result:** **116 passed**, 0 failed (**100% pass rate** in 91.91s).
2. **Browser Subagent Live Test:**
   - Evaluated `http://127.0.0.1:8000/dashboard/`.
   - Verified that all 6 KPI cards display actual values (10,000, 5, 0, 40, 33.6, Tiruchirappalli).
   - Applied filter `Risk Category = HIGH`: verified KPI values updated synchronously (`total_analytical_records = 5`).
   - Clicked `Reset`: verified KPI values restored to `10,000`.
   - Verified map rendering and interactive controls.
   - Recording saved in artifacts: `dashboard_filter_test_1789837878861.webp`.

---

## 7. Remaining Limitations

1. **CartoDB / ESRI Tile Dependency:** The basemap tiles require internet connectivity to load raster tiles; if offline, vector pins and coordinate layers remain visible with the fallback banner.
2. **Database Storage Mode:** System operates in resilient `CSV_FALLBACK_DEV` mode with atomic file locks on local workstation. Production deployment requires starting PostgreSQL 16 + PostGIS 3.4 as documented in `DATABASE_SETUP.md`.
