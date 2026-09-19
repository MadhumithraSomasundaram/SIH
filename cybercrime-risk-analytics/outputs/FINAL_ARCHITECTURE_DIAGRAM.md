# Final System Architecture Diagram & Data Flow Specifications
## End-to-End Component Flow & Inter-Module Interfaces
### Problem Statement ID: 26184 — Cybercrime Predictive Analytics Framework

---

### Master Architectural Flow Diagram

```
                       CYBERCRIME COMPLAINTS
                       (Helpline / Bank Ingestion)
                                  │
                                  ▼
                           DATA PROCESSING
                       (PII Stripping, Imputation)
                                  │
                                  ▼
                         FEATURE ENGINEERING
                     (64 Behavioral Kinematic Predictors)
                                  │
                                  ▼
                      FUTURE WITHDRAWAL TARGET
                     (Binary 24-Hour Cash-Out Target)
                                  │
                                  ▼
                         XGBOOST PREDICTION
                     (100 Trees, Max Depth 4, 1.8ms)
                                  │
                   +--------------+--------------+
                   │                             │
                   ▼                             ▼
              RISK SCORE                       SHAP
         (Platt Scaling 0-100)          (TreeExplainer Local)
                   │                             │
                   └──────────────┬──────────────┘
                                  │
                                  ▼
                          POSTGRESQL/POSTGIS
                     (Spatial Geometries & Cache)
                                  │
                    +-------------+-------------+
                    │                           │
                    ▼                           ▼
                 DBSCAN                      GIS MAP
           (eps=500m, MinPts=3)        (Leaflet Tactical UI)
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                             ALERT ENGINE
                    (Tiered Dispatch & De-duplication)
                                  │
                                  ▼
                          ANALYST INTERFACE
                   (Role-Based Case Management Workspace)
                                  │
                                  ▼
                            INVESTIGATION
                   (Notes, Evidence Hashes & Sec 91)
                                  │
                                  ▼
                              AUDIT LOG
                   (Append-Only SHA-256 Trail)
```

---

### Detailed Stage-by-Stage Specifications & Data Contracts

| Stage | Input Data Contract | Processing Logic | Output Data Contract |
|---|---|---|---|
| **1. Complaints Ingestion** | Raw incident JSON (`case_id`, `amount`, `timestamp`, `channel`, `area`) | Schema validation via Pydantic v2; PII stripping. | Sanitized Complaint Payload |
| **2. Data Processing** | Sanitized Complaint Payload | Numerical median imputation; categorical encoding; coordinate bounding validation. | Cleaned Data Record |
| **3. Feature Engineering** | Cleaned Data Record | Computes rolling 30m velocity, amount-to-baseline ratios, temporal sine/cosine deltas. | 64-Dimensional Feature Vector ($\mathbf{x} \in \mathbb{R}^{64}$) |
| **4. Future Target Mapping** | Historical complaint time series | Correlates whether an unauthorized ATM cash-out occurs within a 24-hour horizon. | Ground Truth Label $y \in \{0, 1\}$ |
| **5. XGBoost Prediction** | 64-Dimensional Feature Vector | Evaluates regularized decision trees ($n=100$, depth 4) to minimize residual loss. | Raw Decision Margin ($z \in \mathbb{R}$) |
| **6. Risk Score Calibration** | Raw Margin ($z$) | Applies Platt logistic calibration: $P = \sigma(Az + B)$, followed by integer rounding. | Calibrated Score $\in [0, 100]$ & Category |
| **7. SHAP Attribution** | Feature Vector & Tree Ensembles | `shap.TreeExplainer` decomposes score into exact additive contributions ($\sum \phi_i$). | Feature Attribution Vector ($\vec{\phi}$) |
| **8. PostgreSQL / PostGIS** | Spatial coordinate $(lat, lon)$ | Indexed using PostGIS `GEOMETRY(Point, 4326)` with resilient GeoJSON cache fallback. | Spatial Entity Record |
| **9. DBSCAN Clustering** | Historical incident coordinates | Haversine clustering with $\varepsilon=500\text{m}$ and $\text{MinPts}=3$; filters noise. | Cluster ID (or Noise `-1`) & Centroid |
| **10. GIS Map Dashboard** | Spatial clusters & risk scores | Leaflet.js renders vector polygon perimeters and nearby ATM pins. | Tactical Spatial Map View |
| **11. Alert Engine** | Risk Score, Category & Hotspot | Evaluates severity thresholds; applies 30-minute deduplication window. | Analytical Alert Object |
| **12. Analyst Interface** | Analytical Alert Object | Authenticated JWT session; presents case triage and spatial overlays. | Active Case Dossier |
| **13. Investigation Case** | Active Case Dossier | Analyst logs field notes, attaches SHA-256 evidence hashes, and triggers bank notices. | Updated Case Record |
| **14. Audit Trail** | User ID, Timestamp, Action, Case ID | Database enforces INSERT-ONLY permission; seals row with SHA-256 hash. | Non-Repudiable Audit Record |

---

### Zero-Single-Point-of-Failure Resilience Map

```
[ Incoming Telemetry ] ──> [ FastAPI REST Gateway ] ──> [ XGBoost Pipeline (CPU Memory) ]
                                                                   │
                              ┌────────────────────────────────────┴────────────────────────────────────┐
                              ▼                                                                         ▼
                [ Primary Path: PostGIS DB ]                                              [ Fallback Path: Local GeoJSON Cache ]
                (Active PostgreSQL Instance)                                              (Offline phase15_hotspots.geojson)
                              │                                                                         │
                              └────────────────────────────────────┬────────────────────────────────────┘
                                                                   ▼
                                                  [ Leaflet Tactical Dashboard ]
                                                                   │
                                                                   ▼
                                                  [ Authorized Analyst Workspace ]
                                                                   │
                                                                   ▼
                                                  [ Immutable SHA-256 Audit Trail ]
```
