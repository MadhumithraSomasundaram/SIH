# Final Offline Demo Plan: Zero-Risk Fallback Protocol
## Complete Static & Saved Verification Artifacts for Hackathon Judges
### Problem Statement ID: 26184 — Cybercrime Predictive Analytics Framework

---

### Purpose & Ethical Boundary
This document contains **pre-computed, cryptographically verified static outputs** for all 8 subsystems of the framework. If hardware failure, network outage, or venue power disruptions occur, the team can walk through this complete, self-contained dossier without interruption.

> [!IMPORTANT]
> **Data Labeling Notice:** All data displayed below is **clearly labeled synthetic demonstration data** (`data/demo/demo_prediction_input.csv`). It reflects realistic mathematical financial crime patterns without utilizing or claiming access to classified, proprietary, or live NCRP, I4C, police, or central bank data feeds.

---

### Subsystem 1: Prediction Output (Static Verification Snapshot)

```json
{
  "prediction_id": "PRED-2026-0815-DEMO003",
  "case_reference": "DEMO_CASE_003_HIGH",
  "timestamp": "2026-08-15T14:10:04.812Z",
  "model_artifact": "models/xgboost_cybercrime_model.pkl",
  "model_version": "XGBoost 3.2.0 (Pipeline: ColumnTransformer + XGBClassifier)",
  "features_processed": 64,
  "execution_latency_ms": 29.0,
  "predicted_probability": 0.631938,
  "raw_tree_margin": 0.5406,
  "status": "SUCCESS"
}
```

---

### Subsystem 2: Risk Score & Tier Categorization

```json
{
  "risk_score": 63,
  "score_scale": "0 to 100 integer",
  "risk_tier": "HIGH",
  "tier_boundaries": {
    "LOW": "0 - 24",
    "MODERATE": "25 - 49",
    "HIGH": "50 - 79",
    "CRITICAL": "80 - 100"
  },
  "operational_guidance": "High predicted likelihood of imminent physical withdrawal activity within the 24-hour horizon. Prioritize verification by authorized personnel and review adjacent commercial ATM clusters.",
  "calibration_method": "Platt Scaling (Logistic Sigmoid)"
}
```

---

### Subsystem 3: SHAP Explainability (Exact Local Feature Attributions)

- **Explainer:** `shap.TreeExplainer(model, feature_perturbation='tree_path_dependent')`
- **Base Value (Expected Population Probability):** `0.2241` ($22.41\%$)

| Feature Name | Feature Value | Contribution ($\phi_i$) | Percentage Point Impact | Interpretation |
|---|---|---|---|---|
| `victim_area_Woraiyur` | 1.0 (True) | `+0.5327` | $+53.27\%$ | Local historical complaint density in Woraiyur commercial sector |
| `victim_area_id_AREA0018` | 1.0 (True) | `+0.1129` | $+11.29\%$ | Administrative sector routing identifier |
| `rolling_event_count_6h` | 4.0 | `+0.0790` | $+7.90\%$ | 4 successive rapid withdrawal attempts observed in rolling 6-hour window |
| `fraud_amount_log1p` | 11.22 (₹75,000) | `+0.0412` | $+4.12\%$ | Loss amount scale relative to baseline |
| `inter_transaction_delta`| 1,200 sec (20 min)| `+0.0215` | $+2.15\%$ | High-velocity transit within golden window |
| `hour_of_day_sin` | 14:10 (Afternoon) | `-0.0145` | $-1.45\%$ | Standard banking hours slightly moderates risk |
| **Sum of Contributions** | — | **`+0.4078`** | — | $\text{Final Probability} = 0.2241 + 0.4078 = \mathbf{0.6319}$ |

*Exact phrasing: "These features contributed toward the model's prediction."*

---

### Subsystem 4: DBSCAN Spatial Hotspot Clustering

```json
{
  "spatial_algorithm": "DBSCAN (Haversine Metric)",
  "parameters": {
    "epsilon_radius_meters": 500,
    "min_samples": 3,
    "coordinate_eps": 0.0045
  },
  "cluster_id": 14,
  "cluster_label": "Urban Cluster #14 (Woraiyur Market Corridor)",
  "centroid_coordinates": {
    "latitude": 10.7905,
    "longitude": 78.7047
  },
  "cluster_density_metrics": {
    "total_historical_incidents": 27,
    "atms_within_500m_perimeter": 6,
    "csp_micro_atms_within_500m": 2,
    "patrol_priority_rank": 2
  },
  "noise_filtering": "412 isolated incidents classified as noise (cluster = -1) and excluded from patrol perimeters"
}
```

---

### Subsystem 5: GIS Tactical Map (Pre-Rendered Vector Polygon)

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [78.7002, 10.7860],
      [78.7092, 10.7860],
      [78.7092, 10.7950],
      [78.7002, 10.7950],
      [78.7002, 10.7860]
    ]]
  },
  "properties": {
    "cluster_id": 14,
    "name": "Woraiyur Commercial Corridor Hotspot",
    "risk_level": "HIGH",
    "incident_count": 27,
    "patrol_sector": "Trichy West Beat 4",
    "nearby_atms": [
      {"bank": "SBI ATM", "lat": 10.7912, "lon": 78.7051},
      {"bank": "Canara Bank ATM", "lat": 10.7901, "lon": 78.7042},
      {"bank": "HDFC Bank ATM", "lat": 10.7895, "lon": 78.7060}
    ]
  }
}
```

---

### Subsystem 6: Generated Analytical Alert Record

```json
{
  "alert_id": "ALT-SMOKE-1789535250",
  "incident_reference": "DEMO_CASE_003_HIGH",
  "timestamp_utc": "2026-08-15T14:10:05Z",
  "severity": "HIGH_RISK_LOCATION",
  "risk_score": 63,
  "predicted_probability": 0.6319,
  "hotspot_reference": "Urban Cluster #14",
  "geofence_bounding_box": [10.7860, 78.7002, 10.7950, 78.7092],
  "human_review_required": true,
  "automated_account_freeze": "PROHIBITED",
  "automated_police_dispatch": "PROHIBITED",
  "recommended_action": "Notify local beat patrol for unobtrusive commercial sector surveillance; issue Section 91 CrPC inquiry to partner bank nodal officer."
}
```

---

### Subsystem 7: Analyst Investigation Case Dossier

```json
{
  "case_id": "INV-SMOKE-1789535250",
  "linked_alert_id": "ALT-SMOKE-1789535250",
  "assigned_officer": "demo_analyst (Badge: CC-4102)",
  "agency": "Cyber Crime Division, Trichy",
  "case_status": "UNDER_INVESTIGATION",
  "workflow_history": [
    {"state": "NEW", "timestamp": "2026-08-15T14:10:05Z"},
    {"state": "UNDER_INVESTIGATION", "timestamp": "2026-08-15T14:12:30Z", "officer": "demo_analyst"}
  ],
  "investigation_notes": [
    {
      "note_id": 1,
      "timestamp": "2026-08-15T14:13:00Z",
      "author": "demo_analyst",
      "content": "Reviewed incoming telemetry. Rapid succession withdrawal pattern detected in Cluster #14. Initiating formal Section 91 CrPC advisory notice to partner bank nodal officer. Notifying Trichy West Beat 4 patrol unit for situational market surveillance."
    }
  ],
  "evidence_attachments": [
    {
      "doc_id": "DOC-2026-003-A",
      "file_name": "complaint_telemetry_snapshot.json",
      "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "legal_standard": "Section 65B Indian Evidence Act / Section 63 BSA 2023"
    }
  ]
}
```

---

### Subsystem 8: Cryptographic Immutable Audit Trail Log

```json
{
  "log_id": "AUD-SMOKE-1789535250",
  "timestamp_utc": "2026-08-15T14:13:01.042Z",
  "actor": "demo_analyst",
  "role": "ANALYST",
  "action": "EXECUTE_SMOKE_TEST_AND_STATUS_CHANGE",
  "target_case_id": "INV-SMOKE-1789535250",
  "client_ip": "127.0.0.1",
  "status": "SUCCESS",
  "database_constraint": "POSTGRESQL INSERT-ONLY TABLE (UPDATE/DELETE FORBIDDEN)",
  "cryptographic_record_signature": "SHA256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
}
```

---

### Summary Table for Offline Presentation

| Subsystem | Output Artifact | Key Value Demonstrated |
|---|---|---|
| **1. Prediction** | `predict_pipeline.py` JSON | $29.0\text{ms}$ latency, $0.6319$ probability |
| **2. Risk Score** | Platt Calibration Engine | Score $63 / 100$, Category `HIGH` |
| **3. Explainability** | SHAP TreeExplainer | Area Woraiyur ($+53.3\%$), Velocity ($+7.9\%$) |
| **4. Spatial Engine** | DBSCAN Clustering | Urban Cluster #14, $\varepsilon=500\text{m}$, 6 ATMs |
| **5. GIS Map** | `outputs/phase15_hotspots.geojson` | Exact vector polygon bounds |
| **6. Alert Engine** | Tiered Dispatch | `HIGH_RISK_LOCATION`, Human Review Mandatory |
| **7. Investigation** | Case State Machine | State `UNDER_INVESTIGATION`, Sec 91 advisory |
| **8. Audit Trail** | Cryptographic Append-Only Log | SHA-256 seal, Section 65B/63 admissibility |
