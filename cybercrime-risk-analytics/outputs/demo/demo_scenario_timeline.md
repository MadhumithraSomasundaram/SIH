# Phase 18 — Demonstration Scenario Timeline
## End-to-End Operational Lifecycle: From Incident Signal to Audit Trail
**Problem Statement ID:** 26184  
**Project:** Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations  
**Scenario Name:** Multi-Complaint Surge in Urban Commercial Corridor  
**Demonstration Reference:** `DEMO-SCENARIO-2026-09`  

---

## Scenario Background

In a 24-hour window, multiple cybercrime complaints (unauthorized debit transactions and phishing scams) are lodged by citizens within an urban commercial zone. The authorized law enforcement analytics pipeline ingests a newly registered complaint, extracts temporal and spatial features, runs the calibrated XGBoost inference engine, contextualizes the event against DBSCAN spatial clusters, triggers a high-priority alert, and supports analyst decision-making through case investigation and immutable audit logging.

---

## Chronological Operational Sequence

| Step | Timestamp (Relative) | Pipeline Stage | Event Description & Technical State | Operational / Decision-Support Action |
|:---:|:---:|:---|:---|:---|
| **01** | `T + 00:00:00` | **New Complaint Ingestion** | Synthetic complaint received via authorized ingestion route: `DEMO_CASE_003_HIGH`. Amount: ₹85,000; Category: Online Financial Fraud; Area: Andheri East (Grid: 19.12_72.86). | Raw complaint registered; PII (account number, phone, complainant name) stripped before feature transformation. |
| **02** | `T + 00:00:02` | **Feature Preparation** | Pipeline loads frozen feature dictionary (64 features). Computes backward rolling counts: `rolling_event_count_24h = 4`, `events_in_previous_3_days = 7`, `amount_log1p = 11.35`. | Input schema verified against trained metadata. Zero future target leakage confirmed. |
| **03** | `T + 00:00:04` | **XGBoost Inference** | Pre-trained model (`Phase7_XGBoost_v1.0`) executes inference over preprocessed feature vector. | Raw likelihood generated: $P(\text{future\_withdrawal} = 1) = 0.631938$. |
| **04** | `T + 00:00:05` | **Risk Score Computation** | Formula: $\text{risk\_score} = \text{round}(0.631938 \times 100) = 63$. | Calibrated integer risk score: **63 / 100**. |
| **05** | `T + 00:00:05` | **Risk Tier Assignment** | Score 63 maps to **HIGH** risk tier (60–79 range). | Flagged for priority analytical triage. *Note: CRITICAL tier (≥80) is not naturally produced by this model distribution.* |
| **06** | `T + 00:00:07` | **SHAP Local Explanation** | TreeExplainer generates local feature attributions without refitting. | **Top Positive Contributors**: `rolling_event_count_24h` (+0.182), `amount_log1p` (+0.141), `previous_activity_by_district` (+0.098). |
| **07** | `T + 00:00:08` | **Spatial Hotspot Correlation** | Spatial engine checks coordinates `(19.12, 72.86)` against Phase 14 DBSCAN clusters (40 clusters). | Match confirmed: Incident falls within **Hotspot Cluster #14** (High density cluster, 18 historical incidents, 6 proximate ATMs). |
| **08** | `T + 00:00:09` | **Combined Analytical Priority** | Rule: $\text{Priority} = f(\text{Risk: HIGH}, \text{Hotspot: TRUE})$. Composite priority: **CRITICAL_REVIEW**. | Alert generation criteria satisfied. Cooldown deduplication checked (no duplicate alert in past 60 min). |
| **09** | `T + 00:00:10` | **Operational Alert Generated** | Alert record `ALT-20260916-014` generated. Status: `NEW`, Priority: `HIGH`, `human_review_required = True`. | Pushed to Analyst Alert Inbox. **Zero automated coercive action, no account freeze, no accusation.** |
| **10** | `T + 00:01:15` | **Analyst Triage & Review** | Authorized Officer (Role: `ANALYST`, User: `demo_analyst`) logs into `/analyst` and opens alert `ALT-20260916-014`. | Analyst inspects risk score (63), SHAP feature drivers, and geographic proximity to Cluster #14 ATMs. |
| **11** | `T + 00:02:00` | **Investigation Created** | Analyst transitions alert status: `NEW` $\to$ `ACKNOWLEDGED`. Creates Investigation Case `INV-2026-0042`. | Case titled: *"Analytical Review: Clustered Withdrawal Likelihood in Andheri East Sector"*. |
| **12** | `T + 00:03:30` | **Analyst Observation Logged** | Analyst appends formal case note: *"Elevated complaint frequency in 24h window matches historical withdrawal staging patterns. Recommending enhanced beat patrol near ATM cluster."* | Note saved with immutable timestamp and user attribution. |
| **13** | `T + 00:04:45` | **Evidence Reference Attached** | Safe external reference attached: `NCRP-ACK-REF-2026-991204` and `GIS-SURVEILLANCE-SECTOR-14`. | No raw personal files uploaded; standardized reference strings linked for cross-agency alignment. |
| **14** | `T + 00:05:30` | **Status Transition to In-Review** | Case status updated: `ACKNOWLEDGED` $\to$ `IN_REVIEW`. Assigned to Sector Patrol Coordination Unit. | Field patrol units notified of analytical risk zone for proactive deterrence. |
| **15** | `T + 00:06:00` | **Resolution / Closure** | Preventative patrol dispatched; deterrence achieved. Analyst updates case status: `IN_REVIEW` $\to$ `RESOLVED`. Alert marked `RESOLVED`. | Investigation lifecycle successfully closed with outcome documented. |
| **16** | `T + 00:06:05` | **Audit Trail Verification** | Audit subsystem verifies 7 discrete immutable records logged for session `SES-9941`. | Entries: `LOGIN`, `VIEW_ALERT`, `ACKNOWLEDGE_ALERT`, `CREATE_INVESTIGATION`, `ADD_NOTE`, `ADD_EVIDENCE`, `RESOLVE_INVESTIGATION`. |

---

## 3. Key Operational Takeaways

1. **Deterministic Speed**: Full predictive flow from raw input to alert dispatch completes in `< 10 seconds`.
2. **Explainable AI in Action**: Law enforcement officers are never presented with a "black-box" score; SHAP factors clearly state why the area risk is elevated.
3. **Strict Human-in-the-Loop Safeguards**: Every operational decision (from acknowledgment to patrol briefing) requires human verification.
4. **Accountability Guaranteed**: Every action is permanently recorded in the non-repudiable audit ledger.
