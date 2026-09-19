# Phase 19 — SIH Demonstration Screenshot Checklist
## 12 Required Presentation & Slide Visual Assets
**Problem Statement ID:** 26184  
**Project:** Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations  
**Guidelines:** Capture in high resolution (1920×1080 or higher). Ensure zero sensitive citizen PII (real names, phone numbers, full account numbers) is visible.  

---

### Screenshot 1: Command Center Home / Overview Dashboard
- **URL**: `http://localhost:8000/dashboard`
- **Key Visual Elements**: Full overview showing KPI chips (Active Incidents, Total Hotspots, Monitored ATMs), sidebar navigation, and primary map canvas in dark tactical theme.
- **Presentation Slide**: Slide 10 (GIS Command Dashboard) / Slide 1.

---

### Screenshot 2: Spatio-Temporal Risk Heatmap Layer
- **URL**: `http://localhost:8000/dashboard` (Layer toggle: Risk Gradient active)
- **Key Visual Elements**: Choropleth risk intensity gradients across municipal boundaries showing color transition from LOW (green) to HIGH (orange/red).
- **Presentation Slide**: Slide 10 (GIS Command Dashboard).

---

### Screenshot 3: High-Risk Analytical Area Selection
- **URL**: `http://localhost:8000/dashboard` (Selected Sector #14 / Andheri East corridor)
- **Key Visual Elements**: Highlighted sector boundary bounding box, localized coordinate centroid display, and highlighted alert indicator icon.
- **Presentation Slide**: Slide 3 (Proposed Solution) / Slide 10.

---

### Screenshot 4: DBSCAN Hotspot Overlay & Polygons
- **URL**: `http://localhost:8000/dashboard` (Layer toggle: Hotspot Clusters active)
- **Key Visual Elements**: Clear polygon boundary of Hotspot Cluster #14 showing historical cashout concentration and proximate ATM markers.
- **Presentation Slide**: Slide 9 (Spatial Intelligence).

---

### Screenshot 5: Predictive Risk Metric Card & Probability Details
- **URL**: `http://localhost:8000/dashboard` or `/predict` modal
- **Key Visual Elements**: Clear KPI card displaying **Predicted Probability: 0.6319**, **Risk Score: 63 / 100**, and **Risk Tier: HIGH** with mathematical identity indicator.
- **Presentation Slide**: Slide 6 (Machine Learning) / Slide 13 (Demo Workflow).

---

### Screenshot 6: SHAP Feature Attribution Plot
- **URL**: `http://localhost:8000/dashboard` (Model Explanation drawer) or local plot
- **Key Visual Elements**: Horizontal bar plot displaying local Shapley feature contributions: `rolling_event_count_24h` (+0.182), `amount_log1p` (+0.141), with clear positive (red) and negative (blue) bars.
- **Presentation Slide**: Slide 8 (Explainable AI via SHAP).

---

### Screenshot 7: Operational Alert Inbox & Summary Panel
- **URL**: `http://localhost:8000/analyst` (Alerts tab) or `/dashboard` (Alert feed)
- **Key Visual Elements**: Filtered alert list showing alert reference `ALT-20260916-014`, severity badge (HIGH), status tag (NEW), and mandatory review chip (`human_review_required`).
- **Presentation Slide**: Slide 11 (Alert Engine).

---

### Screenshot 8: Alert Inspection & Operational Details Drawer
- **URL**: `http://localhost:8000/analyst` (Click alert to open inspection drawer)
- **Key Visual Elements**: Detailed modal showing source complaint reference, coordinate centroid, linked hotspot ID (`HS-14`), operational guidance text, and action buttons (`Acknowledge`, `Dismiss`).
- **Presentation Slide**: Slide 11 (Alert Engine) / Slide 12 (Analyst Interface).

---

### Screenshot 9: Analyst Case Investigation Workspace
- **URL**: `http://localhost:8000/analyst` (Active case: `INV-2026-0042`)
- **Key Visual Elements**: Comprehensive case management screen showing case title, assigned officer (`demo_analyst`), status timeline (`ACKNOWLEDGED` $\to$ `IN_REVIEW`), chronological case notes, and external evidence reference box (`NCRP-ACK-REF-*`).
- **Presentation Slide**: Slide 12 (Authorized Analyst Interface).

---

### Screenshot 10: Non-Repudiable Immutable Audit Trail
- **URL**: `http://localhost:8000/analyst` (Audit Log tab)
- **Key Visual Elements**: Tabular ledger showing chronological entries: `LOGIN`, `VIEW_ALERT`, `ACKNOWLEDGE_ALERT`, `CREATE_INVESTIGATION`, `ADD_NOTE`, with exact ISO-8601 timestamps and user roles.
- **Presentation Slide**: Slide 12 (Analyst Interface) / Slide 13 (Demo Lifecycle).

---

### Screenshot 11: Interactive API Documentation (FastAPI Swagger UI)
- **URL**: `http://localhost:8000/docs`
- **Key Visual Elements**: Clean FastAPI Swagger UI detailing available endpoint groups: `/predict`, `/explain`, `/alerts`, `/analyst`, `/database`, showcasing typed Pydantic request bodies.
- **Presentation Slide**: Technical Appendix / Q&A Slide.

---

### Screenshot 12: End-to-End System Architecture Diagram
- **Source**: Diagram rendered from `outputs/phase18_architecture.md` / Slide 3
- **Key Visual Elements**: High-resolution architecture flowchart cleanly demarcating the 8 functional subsystems: XGBoost, DBSCAN, PostGIS, SHAP, FastAPI, Leaflet GIS, Alert Engine, and Analyst Workspace.
- **Presentation Slide**: Slide 3 & Slide 5.
