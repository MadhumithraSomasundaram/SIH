# Phase 14 — DBSCAN Spatial Hotspot Detection
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Objective
Identify geographical areas with unusually dense concentrations of cybercrime-related complaints
using DBSCAN spatial clustering on WGS 84 geographic coordinates.

> **IMPORTANT INTERPRETATION:** DBSCAN identifies spatial concentrations of observed events.
> It does NOT prove criminal identity, criminal intent, future criminal activity, or causation.
> A hotspot is an analytical spatial cluster. Model risk score and hotspot rank are separate concepts.

---

## 2. Input Data
- **Source:** CSV: targeted_cybercrime_data.csv (10000 rows)
- **Total records:** 10000
- **Usable geographic points:** 10000
- **Missing coordinates:** 0
- **Invalid coordinates:** 0

---

## 3. Geographic Coverage
- **Latitude range:** 8.52 degrees N to 17.69 degrees N (South India)
- **Longitude range:** 74.50 degrees E to 83.22 degrees E
- **Geographic region:** South India (Kerala, Tamil Nadu, Andhra Pradesh, Karnataka)
- **Coordinate system:** WGS 84 (EPSG:4326)

---

## 4. Coordinate Validation
All 10000 records passed WGS 84 bounds checking:
- Latitude within [-90.0, 90.0]: PASS
- Longitude within [-180.0, 180.0]: PASS

---

## 5. DBSCAN Method
scikit-learn DBSCAN with algorithm=ball_tree and metric=haversine.

---

## 6. Distance Metric — Haversine
Raw latitude/longitude degrees are not valid Euclidean distances.
The haversine great-circle formula is used instead.
Epsilon conversion: eps_radians = eps_km / Earth_radius_km = eps_km / 6371.0088

---

## 7. Parameter Testing
7 configurations tested (see outputs/phase14_dbscan_parameter_results.csv):
- eps values: 0.5 km, 1.0 km, 2.0 km
- min_samples values: 3, 5, 10

---

## 8. Selected Parameters
- **eps:** 0.5 km (= 0.000078 radians)
- **min_samples:** 3
- **Rationale:** Selected eps=0.5km min_samples=3 because it produces 40 meaningful clusters with 0.0% noise — geographically interpretable at ~0.5 km neighbourhood radius.

---

## 9. Cluster Results
- **Total clusters:** 40
- **Noise points:** 0 (0.0%)
- **Largest cluster:** 310 events
- **Median cluster size:** 251.5 events
- **Silhouette score:** 1.0

---

## 10. Noise Analysis
- Noise = 0 events not assigned to any spatial cluster at eps=0.5 km.
- This is expected for dispersed singleton events.

---

## 11. Hotspot Statistics
- **Total analytical hotspots:** 40
- **Top hotspot:** Cluster 23 — 310 events at (13.6288°N, 79.4192°E)

---

## 12. Withdrawal Hotspots
Based on future_withdrawal == 1 sub-population.
See outputs/phase14_withdrawal_hotspots.csv.

---

## 13. Risk x Hotspot Analysis
See outputs/phase14_hotspot_risk_summary.csv.
Cross-tabulates cluster membership with Phase 9 XGBoost risk categories.
Note: Phase 9 predictions cover only the 1,500-record test split.

---

## 14. Temporal Analysis
See outputs/phase14_hotspot_temporal_summary.csv.

---

## 15. Validation
- Silhouette score (non-noise points, haversine): 1.0

---

## 16. Stability
See outputs/phase14_cluster_stability.csv.

---

## 17. Security
All outputs exclude: account numbers, card numbers, PINs, OTPs, CVVs, passwords, phone/email PII.
See outputs/phase14_sensitive_data_audit.csv.

---

## 18. Leakage Audit
DBSCAN uses ONLY geographic coordinates (latitude/longitude) as input.
No risk scores, target labels, or future information enter the distance matrix.
See outputs/phase14_leakage_audit.csv.

---

## 19. Limitations
1. Hotspot clusters are descriptive — they reflect past event density, not future criminal certainty.
2. Phase 9 risk scores cover only 1,500 test records; 8,500 training records have no risk annotation.
3. Haversine DBSCAN does not correct for population density or complaint reporting rates.
4. Cluster stability depends on sufficient spatial density; sparse periods may yield few clusters.

---

## 20. Conclusion
Phase 14 successfully identified 40 spatial hotspot clusters from 10000 validated
geographic complaint records. Hotspots are documented for authorized analytical use by human
investigators. All findings require human review and institutional authorization before any action.

---

## 21. Phase 15 Readiness
Phase 14 outputs available for Phase 15:
- outputs/phase14_hotspots_geojson.geojson — Map-ready spatial hotspot features
- outputs/phase14_hotspot_summary.csv — Ranked analytical hotspot catalog
- PostGIS table: cybercrime_hotspots (status: SKIPPED - PostgreSQL offline)
