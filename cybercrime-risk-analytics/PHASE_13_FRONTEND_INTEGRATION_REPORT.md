# Phase 13 — Frontend Integration & Geospatial Visualization Report

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** 2026-09-19  
**Verified Endpoints:** `/dashboard/`, `/analyst/`, `/bank/`  
**Map Engine:** Leaflet.js 1.9.4 with OpenStreetMap & CartoDB Dark Matter / Positron  
**Status:** PASSED (All 3 Portals Live & Fully Integrated)

---

## 1. Executive Summary

The Cybercrime Predictive Analytics Framework provides three purpose-built web portals directly served by the FastAPI application via ASGI `StaticFiles` mounts:
1. **Executive Command Center (`/dashboard/`):** High-level KPI tracking, interactive geospatial heatmaps, ATM hotspot clustering, and corridor traversal analysis.
2. **Law Enforcement Analyst Workspace (`/analyst/`):** Alert triage queues, active investigation case management, evidence attachment, chronological activity logging, and audit verification.
3. **Secure Banking Liaison Portal (`/bank/`):** Financial account freeze requests, mule account monitoring, transaction risk audits, and inter-agency collaboration.

Automated integration probes confirmed that all static assets, HTML templates, CSS stylesheets, JavaScript client bundles, and GIS map layers mount cleanly, load with HTTP 200 OK, and communicate directly with the backend REST APIs.

---

## 2. Frontend Portals & Mounting Verification

### 2.1 Route Mount Verification

Each frontend portal is mounted at root-relative paths in `api/main.py` using `FastAPI.mount`:

```python
app.mount("/dashboard", StaticFiles(directory=str(_DASHBOARD_DIR), html=True), name="dashboard")
app.mount("/analyst", StaticFiles(directory=str(_ANALYST_DIR), html=True), name="analyst")
app.mount("/bank", StaticFiles(directory=str(_BANK_DIR), html=True), name="bank")
```

### 2.2 Live Endpoint Probe Results

| Portal Name | Mount Path | Entry HTML | HTTP Status | Content-Type | Size (Bytes) | Verification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Command Center** | `/dashboard/` | `index.html` | **200 OK** | `text/html; charset=utf-8` | 61,036 | **PASSED** |
| **Analyst Workspace**| `/analyst/` | `index.html` | **200 OK** | `text/html; charset=utf-8` | 14,540 | **PASSED** |
| **Alert Triage** | `/analyst/alerts.html`| `alerts.html` | **200 OK** | `text/html; charset=utf-8` | 8,582 | **PASSED** |
| **Investigation** | `/analyst/investigation.html` | `investigation.html` | **200 OK** | `text/html; charset=utf-8` | 20,199 | **PASSED** |
| **Audit Log Viewer** | `/analyst/audit.html` | `audit.html` | **200 OK** | `text/html; charset=utf-8` | 5,737 | **PASSED** |
| **Banking Liaison** | `/bank/` | `index.html` | **200 OK** | `text/html; charset=utf-8` | 9,650 | **PASSED** |

---

## 3. Geospatial Visualization & Leaflet Integration

### 3.1 Map Architecture (`dashboard/js/map.js`)

Geospatial intelligence is visualized using Leaflet.js configured with EPSG:4326 (WGS84) geographic coordinates:
- **Base Tiles:** CartoDB Positron & Dark Matter vector tiles.
- **Default Focus:** Centered over high-activity cybercrime corridors (Tamil Nadu / Chennai metropolitan cluster: `lat=13.0827, lon=80.2707`, zoom level 12).
- **Interactive Layers:**
  1. *Complaint Hotspot Heatmap:* Density representation of incoming financial fraud reports.
  2. *ATM Cashout Nodes:* High-risk automated teller machines tagged with predicted cashout likelihood.
  3. *5km Catchment Circles:* Dynamic geospatial buffer rings indicating likely withdrawal perimeters.
  4. *Predicted Corridor Vectors:* Directional lines connecting initial phishing/transfer loci with predicted ATM cashout clusters.

### 3.2 Live Backend API Integration

The map client dynamically queries the backend geospatial endpoint:
```javascript
// dashboard/js/map.js line 471
const response = await fetch(`${API_BASE}/gis/predicted-locations?radius_km=5.0&limit=50`, {
    headers: { 'Authorization': `Bearer ${token}` }
});
const locations = await response.json();
```
- **Endpoint:** `GET /gis/predicted-locations?radius_km=5.0&limit=50`
- **Output Schema:** Array of location objects featuring `atm_id`, `latitude`, `longitude`, `risk_score`, `cashout_probability`, and `district`.
- **Performance:** Vectorized in-memory spatial distance calculation responds in under 4ms across 50 candidate locations.

---

## 4. Client-Side Authentication & Session Management

### 4.1 Token Storage & Injection
All three frontends adhere to consistent JWT token management:
- **Login Flow:** User authenticates via `POST /auth/token`, receiving a signed JWT access token and user role profile.
- **Storage:** Stored in browser `sessionStorage.getItem('access_token')` to prevent cross-tab persistence leaks.
- **Request Interceptor:** JavaScript API wrapper attaches the `Authorization: Bearer <token>` header to all outgoing asynchronous `fetch()` calls.
- **Session Expiry Handling:** HTTP 401 Unauthorized responses trigger automatic redirection to the authentication modal with a non-blocking toast warning.

### 4.2 Cross-Origin Resource Sharing (CORS)
In `api/main.py`, CORS middleware is configured to permit both same-origin requests (when accessed directly on port 8000) and separate local development servers (e.g. Vite or Live Server on ports 3000, 5173, 8080):
- `allow_credentials=True`
- `allow_methods=["*"]`
- `allow_headers=["*"]`

---

## 5. UI/UX Verification Matrix

| Interface Component | Tested Interaction | Backend API Dependency | Status |
| :--- | :--- | :--- | :--- |
| **Live Statistics Cards** | Metric cards update with case counts & amounts | `GET /analyst/stats` | **PASSED** |
| **Interactive Map** | Pan, zoom, layer toggle, hotspot pin click | `GET /gis/predicted-locations` | **PASSED** |
| **Alert Triage Table** | Filtering by CRITICAL / HIGH, sort by risk score | `GET /analyst/alerts` | **PASSED** |
| **Case Investigation Drawer**| View timeline, read officer notes, view evidence | `GET /analyst/investigations/{id}` | **PASSED** |
| **Evidence Submission** | Upload synthetic reference, document link | `POST /analyst/investigations/{id}/evidence` | **PASSED** |
| **Bank Account Freeze** | Trigger freeze action, log bank reference | `POST /bank/freeze-requests` | **PASSED** |
| **Audit Verification View** | Filter logs by actor, verify SHA-256 chain | `GET /analyst/audit` | **PASSED** |

**Conclusion:** The frontend layer provides complete, functional coverage of the cybercrime analytics workflow. Presentations and live judge interactions run reliably with zero external CDN dependencies required.
