# Geospatial Intelligence & GIS Module Specification

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** 2026-09-19  
**GIS Engine:** Density-Based Spatial Clustering (DBSCAN) + Vectorized Haversine + Leaflet.js 1.9.4  
**Auditor:** Senior Geospatial Software Engineer

---

## 1. Executive Summary & Geospatial Objectives

While the machine learning tier determines *if* a complaint poses an imminent cashout risk, the Geospatial Information System (GIS) module answers *where* interdiction resources should be focused.

The GIS module synthesizes:
1. **Historical Extraction Hotspots:** Unsupervised spatial clustering across verified past incidents.
2. **Physical ATM Infrastructure:** A master registry of 3,000 automated teller machines.
3. **Proximity Query Engine:** High-performance spatial distance matching computing candidate ATMs within a 5km to 10km radius.
4. **Interactive Command Center Map:** Live Leaflet visualization integrating heatmap overlays, ATM pins, and risk catchment perimeters.

---

## 2. Geographic Data Sources & Coordinate Quality

### 2.1 Geographic Data Sources
| Dataset Source | Path | Entity Count | Attributes Utilized |
| :--- | :--- | :---: | :--- |
| **Physical ATMs Registry** | `data/raw/ATMs_Locations.csv` | 3,000 ATMs | `atm_id`, `bank_name`, `latitude`, `longitude`, `district`, `state` |
| **Areas Master Boundary** | `data/raw/Areas_Master.csv` | 200 Areas | `area_id`, `area_name`, `centroid_lat`, `centroid_lon`, `district` |
| **Historical Cashouts** | `data/raw/Withdrawals.csv` | 80,000 Events | `withdrawal_id`, `atm_id`, `latitude`, `longitude`, `timestamp`, `amount` |
| **Cleaned Location Master**| `data/processed/cleaned_atms_locations.csv` | 3,000 ATMs | Validated coordinates in WGS84 format |

### 2.2 Coordinate Validation & Quality Auditing
All geographic coordinates undergo strict geometric boundary validation:
- **Latitude Bounds:** Must satisfy $8.0^{\circ}\text{N} \le \text{Latitude} \le 37.0^{\circ}\text{N}$ (Indian subcontinent bounds).
- **Longitude Bounds:** Must satisfy $68.0^{\circ}\text{E} \le \text{Longitude} \le 97.5^{\circ}\text{E}$.
- **Precision Verification:** Truncated and rounded coordinates are checked for geocoding artifacts; zero or inverted lat/lon coordinates are filtered out.

---

## 3. DBSCAN Spatial Clustering Pipeline

### 3.1 Algorithm Formulation
To identify dense recurring cashout corridors without imposing artificial geometric cluster shapes, the pipeline executes DBSCAN (Density-Based Spatial Clustering of Applications with Noise) in `src/hotspot_detection.py`:

- **Metric:** Haversine great-circle distance on spherical radians.
- **Epsilon ($\varepsilon$):** $500\text{ meters}$ ($\approx 0.0045^{\circ}$ angular radius), representing typical walking/quick-vehicular transit distance between clustered ATMs.
- **MinPts ($\text{min\_samples}$):** $3\text{ verified events}$.
- **Results:** Discovered **40 distinct spatial hotspot clusters** (labeled `HS-01` through `HS-40`) across 10,000 historical complaint events (`outputs/phase14_hotspots_geojson.geojson`).

### 3.2 Interpretation of Clusters
- **Dense Nodes:** Cluster centroids represent recurrent extraction hubs (e.g. major commercial railway junctions, high-density shopping districts, multi-bank ATM alleys).
- **Noise Points:** Sparse, isolated incidents are classified as noise (cluster label `-1`) and excluded from high-priority alert triggers.

---

## 4. Proximity Analysis & Candidate ATM Retrieval

### 4.1 Vectorized Haversine Distance Engine
When a complaint is analyzed, the system computes spatial distances from the complaint's jurisdictional centroid to all candidate ATMs:

$$d = 2 R \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)} \right)$$
where $R = 6,371.0\text{ km}$.

- **Performance:** In `CSV_FALLBACK_DEV` mode, NumPy vectorized arrays compute distances across 3,000 ATMs in **2.4 milliseconds**.
- **PostGIS Mode:** When active, PostGIS executes the indexed query:
  ```sql
  SELECT atm_id, bank_name, ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS distance_meters
  FROM atms_locations
  WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_meters)
  ORDER BY distance_meters ASC LIMIT :limit;
  ```

---

## 5. Live Endpoint & Frontend Map Integration

### 5.1 Endpoint Specification: `GET /gis/predicted-locations`
- **Route:** `GET /gis/predicted-locations?radius_km=5.0&limit=50`
- **Output Schema:** Returns an array of candidate cashout nodes:
  ```json
  [
    {
      "atm_id": "ATM-0492",
      "bank_name": "State Bank of India",
      "latitude": 13.0827,
      "longitude": 80.2707,
      "district": "Chennai",
      "distance_km": 1.24,
      "risk_score": 84.0,
      "cashout_probability": 0.84,
      "location_source": "DBSCAN Spatial Hotspot Cluster (Estimate)"
    }
  ]
  ```

### 5.2 Verified Frontend Consumption (`dashboard/js/map.js`)
Inspection of `dashboard/js/map.js` confirms live integration:
- **Line 471:** Directly invokes `fetch("${API}/gis/predicted-locations?radius_km=5.0&limit=50")`.
- **Layers Rendered:**
  1. *CartoDB Positron / Dark Matter Base Layer:* Open-source vector basemap tiles.
  2. *Hotspot Density Heatmap:* Visual representation of recurring cashout frequency.
  3. *Candidate ATM Pins:* Individual ATM markers color-coded by bank brand and risk tier.
  4. *5km Catchment Rings:* Circular visual buffer rings representing likely mule transit radius.

---

## 6. Critical Semantic Distinctions

To ensure judicial validity and prevent misinterpretation by field officers:
- **Historical Clusters:** Labeled strictly as *"Historical Extraction Corridors"*, representing past observed crime loci.
- **Predicted Locations:** Labeled strictly as *"Estimated Candidate Corridors (Spatial Proximity Estimate)"*.
- **No Direct Criminal Tracking:** The GIS system maps physical infrastructure and spatial densities—it does not track mobile GPS signals or identify individual persons.

---

## 7. Known Geospatial Limitations

1. **Euclidean / Spherical vs. Road Network:** Distance is calculated using spherical Haversine distance. It does not account for one-way street grids or river bridges (planned for PostGIS `pgRouting` in Phase 15).
2. **Fixed Radius Buffer:** The current radius is set to 5.0 km. Rural areas with sparse ATM distribution may require expanded 15km to 25km search perimeters.
