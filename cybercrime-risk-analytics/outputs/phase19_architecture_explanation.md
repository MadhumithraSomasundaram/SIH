# Phase 19 — Technical Architecture Explanation
## Beginner-Friendly Subsystem Breakdown
**Problem Statement ID:** 26184  
**Project:** Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations  

---

### 1. Python (Core Programming Language)
- **What it does**: Serves as the primary runtime environment orchestrating all data ingestion, machine learning inference, API serving, and test execution.
- **Why it is used**: Universal standard in artificial intelligence and geospatial data science with rich, stable libraries for machine learning, web serving, and database connectivity.
- **Input**: Source code scripts and external application configuration.
- **Output**: Executed computational instructions, data structures, and runtime objects.

---

### 2. Pandas (Data Manipulation & Preprocessing)
- **What it does**: Provides structured, high-performance tabular DataFrame objects used to load, clean, transform, and chronologically partition complaint and transactional data.
- **Why it is used**: Fast, vectorized tabular operations that handle missing value imputation, timestamp parsing, and feature merges with minimal memory overhead.
- **Input**: Raw CSV files (`Fraud_Cases.csv`, `Withdrawals.csv`, etc.).
- **Output**: Cleaned and formatted DataFrames ready for feature engineering and ML consumption.

---

### 3. Scikit-learn (Feature Pipelines & Benchmarks)
- **What it does**: Provides foundational machine learning utilities including `ColumnTransformer`, standard scalers, one-hot encoders, and baseline classifiers (Random Forest, Logistic Regression).
- **Why it is used**: Ensures reproducible, leak-free preprocessing pipelines where transformations fitted on training data can be frozen and applied identically to new inference samples.
- **Input**: Cleaned tabular feature columns.
- **Output**: Transformed numerical NumPy arrays and benchmark model evaluation metrics.

---

### 4. XGBoost (Predictive Risk Classifier)
- **What it does**: An optimized gradient-boosted decision tree library that calculates the probability that a cybercrime complaint will culminate in a cash withdrawal within 24 hours.
- **Why it is used**: Superior performance on tabular datasets with complex non-linear feature interactions, missing data handling, and native `scale_pos_weight` support for imbalanced fraud data.
- **Input**: 64 preprocessed numerical and encoded categorical features.
- **Output**: Calibrated probability $P \in [0.0, 1.0]$ and classification predictions.

---

### 5. SHAP (Model Explainability)
- **What it does**: Breaks open the "black box" of the XGBoost classifier by calculating the exact marginal contribution (Shapley value) of each feature for an individual prediction.
- **Why it is used**: Provides mathematically grounded, cooperative game-theory explanations so law enforcement officers understand why an area is marked high-risk.
- **Input**: Trained XGBoost model and an individual complaint's feature vector.
- **Output**: Positive and negative Shapley attribution values explaining feature impact on predicted risk.

---

### 6. PostgreSQL (Relational Database)
- **What it does**: Provides robust, enterprise-grade relational data storage for structured cybercrime events, prediction results, user accounts, and investigation records.
- **Why it is used**: ACID-compliant, open-source database with rock-solid reliability, foreign key constraints, and seamless extensibility for spatial intelligence.
- **Input**: SQL transactions, ORM model operations, and application queries.
- **Output**: Persisted records, indexed tables, and relational query results.

---

### 7. PostGIS (Geospatial Extension)
- **What it does**: Extends PostgreSQL to store and query spatial objects using the WGS84 coordinate reference system (`SRID 4326`) and GIST spatial indices.
- **Why it is used**: Enables sub-10 millisecond geographic calculations, such as identifying all physical ATMs within 1.5 km of a complaint centroid using `ST_DWithin`.
- **Input**: Latitude/longitude coordinates and spatial radius parameters.
- **Output**: Spatial points, bounding boxes, distance calculations, and GeoJSON geometries.

---

### 8. DBSCAN (Spatial Hotspot Discovery)
- **What it does**: An unsupervised density-based clustering algorithm that groups proximate geographic coordinates of historical cash withdrawals into dense spatial clusters.
- **Why it is used**: Discovers non-linear, arbitrary cluster shapes following urban road and commercial corridors without requiring an arbitrary predefined cluster count ($k$).
- **Input**: GPS coordinates of historical cashout events.
- **Output**: Cluster labels for each incident and 40 delineated spatial hotspot boundary polygons.

---

### 9. FastAPI (REST Backend & Serving)
- **What it does**: Exposes high-throughput, low-latency HTTP REST endpoints for single/batch prediction, explainability, alerts, and analyst case operations.
- **Why it is used**: Asynchronous performance, automatic interactive OpenAPI/Swagger documentation (`/docs`), and native Pydantic schema validation preventing malformed payloads.
- **Input**: JSON HTTP requests from clients and dashboards.
- **Output**: Typed, validated JSON responses and HTTP status codes.

---

### 10. Leaflet.js (GIS Visualization & Command Center)
- **What it does**: Renders an interactive browser-based map displaying choropleth risk gradients, DBSCAN hotspot polygons, and ATM overlays.
- **Why it is used**: Lightweight, mobile-friendly JavaScript mapping library that runs smoothly on standard police command center hardware without bulky GIS desktop software.
- **Input**: GeoJSON feature collections, map tile layers, and analytical alert feeds.
- **Output**: Interactive visual map with click-to-inspect drawers and filtering controls.

---

### 11. Alert Engine (Operational Notification)
- **What it does**: Evaluates continuous model predictions against operational rules, manages cooldown periods, deduplicates triggers, and dispatches prioritized notifications.
- **Why it is used**: Automates the transition from passive data modeling to proactive operational intelligence while preventing officer alert fatigue.
- **Input**: Predicted risk scores, incident coordinates, and spatial hotspot memberships.
- **Output**: Prioritized operational alert objects with mandatory `human_review_required = True` flags.

---

### 12. Analyst Interface (Human Investigation Workspace)
- **What it does**: Provides a role-gated, audited web application where authorized law enforcement officers review alerts, open investigations, log notes, and link evidence references.
- **Why it is used**: Ensures human-in-the-loop accountability, state machine governance, and legal defensibility across all investigative decisions.
- **Input**: Analyst authentication credentials, case notes, evidence references, and status transitions.
- **Output**: Case management records and immutable entries in `analyst_audit_log`.
