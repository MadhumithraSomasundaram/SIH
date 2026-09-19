# Phase 17 — Analyst Interface Report
## Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
### SIH 2026 · Phase 17 of 17 — Authorized Law Enforcement / Analyst Interface

---

> **IMPORTANT:**
> This is a **prototype analytical decision-support system**.
> It is **not** connected to live NCRP, banking, ATM, or financial institution systems.
> All data presented in this demo is **SYNTHETIC** and does not represent real individuals or events.
> Predictive risk scores and spatial hotspots are **not proof of criminal activity**.

---

## 1. Executive Summary

Phase 17 delivers an **Authorized Analyst / Law Enforcement Intelligence Interface** built on top
of the complete Cybercrime Predictive Analytics pipeline from Phases 8–16.

The interface enables authorized analysts, supervisors, and administrators to:
- Review analytical alerts and predictive risk scores
- Inspect spatial hotspots from Phase 14 DBSCAN clustering
- Create and manage investigations with full audit trails
- Record analyst notes, evidence references, and review model explanations (SHAP)
- Manage the complete investigation workflow (OPEN → CLOSED/DISMISSED)
- Produce investigation summaries and export safe data
- Access a full immutable audit log (SUPERVISOR/ADMIN only)

All actions are **analytical and decision-support only** — no automatic enforcement actions are triggered.

---

## 2. System Architecture

```
Phases 8–16 Pipeline
     ↓
FastAPI Backend (api/analyst_routes.py)
     ↓ JWT + RBAC
Analyst Interface (analyst/ HTML+CSS+JS)
     ↓
┌──────────┬───────────────┬────────────┬──────────────┐
│ Overview │ Alert Mgmt    │ Invest.    │ Audit Log    │
│ (index)  │ (alerts.html) │ Workspace  │ (audit.html) │
│          │               │ (inv.html) │              │
└──────────┴───────────────┴────────────┴──────────────┘
```

### Technology Stack
| Layer | Technology |
|---|---|
| Frontend | HTML5 + CSS3 (Glassmorphism/Dark Mode) + Vanilla JavaScript |
| Mapping | Leaflet.js (via Phase 15 GIS Dashboard link) |
| Backend | FastAPI (Python) |
| Auth | Prototype JWT HS256 (`python-jose`) + bcrypt password hashing |
| Database | PostgreSQL/PostGIS via SQLAlchemy (with in-memory fallback) |
| Model | XGBoost (Phase 8) + SHAP Explainability (Phase 10) |
| Demo Data | Synthetic (CSV fallback) — clearly labeled |

---

## 3. New Components

### 3.1 Database Models (`database/investigation_models.py`)

| Table | Purpose |
|---|---|
| `analyst_users` | Prototype user/role store (bcrypt-hashed passwords) |
| `investigations` | Core investigation records linked to analytical alerts |
| `investigation_notes` | Timestamped analyst notes per investigation |
| `investigation_evidence` | Safe evidence reference metadata |
| `investigation_timeline` | Immutable event log per investigation |
| `analyst_audit_log` | System-wide analyst action audit trail |

All tables are **non-destructive** (CREATE TABLE IF NOT EXISTS semantics).

### 3.2 API Endpoints (`api/analyst_routes.py`)

| Method | Endpoint | Min Role | Description |
|---|---|---|---|
| POST | `/analyst/auth/login` | PUBLIC | Prototype login |
| GET | `/analyst/auth/me` | ANALYST | Current user info |
| GET | `/analyst/overview` | ANALYST | Dashboard KPIs |
| GET | `/analyst/alerts` | ANALYST | Alert list (paginated, filtered) |
| GET | `/analyst/alerts/{id}` | ANALYST | Alert detail with disclaimer |
| POST | `/analyst/investigations` | ANALYST | Create investigation |
| GET | `/analyst/investigations` | ANALYST | List investigations |
| GET | `/analyst/investigations/{id}` | ANALYST | Investigation detail (all sections) |
| PATCH | `/analyst/investigations/{id}` | ANALYST | Update status/priority/summary |
| POST | `/analyst/investigations/{id}/notes` | ANALYST | Add analyst note |
| GET | `/analyst/investigations/{id}/timeline` | ANALYST | Get investigation timeline |
| POST | `/analyst/investigations/{id}/evidence` | ANALYST | Add evidence reference |
| GET | `/analyst/investigations/{id}/explanation` | ANALYST | SHAP model explanation |
| GET | `/analyst/hotspots` | ANALYST | Phase 14 hotspot summaries |
| GET | `/analyst/audit` | SUPERVISOR | Paginated audit log |

### 3.3 Frontend Pages (`analyst/`)

| Page | Description |
|---|---|
| `index.html` | Overview/Dashboard with KPI grid and login screen |
| `alerts.html` | Alert management with table, filters, detail panel, workflow |
| `investigation.html` | Investigation workspace with tabs (Notes/Evidence/Timeline/SHAP) |
| `audit.html` | Audit log with filters (SUPERVISOR/ADMIN only) |
| `css/analyst.css` | Dark-mode glassmorphism design system |
| `js/analyst.js` | Shared utilities: Auth, Http, Toast, Fmt, Nav, Login |
| `js/alerts.js` | Alert management logic |
| `js/investigation.js` | Investigation workspace logic |
| `js/audit.js` | Audit log logic |

---

## 4. Role-Based Access Control

| Capability | ANALYST | SUPERVISOR | ADMIN |
|---|:---:|:---:|:---:|
| View overview/KPIs | ✓ | ✓ | ✓ |
| View/filter alerts | ✓ | ✓ | ✓ |
| Create investigation | ✓ | ✓ | ✓ |
| Add notes, evidence | ✓ | ✓ | ✓ |
| View SHAP explanation | ✓ | ✓ | ✓ |
| Transition to UNDER_REVIEW | ✓ | ✓ | ✓ |
| Transition to PENDING_VALIDATION | ✓ | ✓ | ✓ |
| CLOSE investigation | ✗ | ✓ | ✓ |
| DISMISS investigation | ✗ | ✓ | ✓ |
| View audit log | ✗ | ✓ | ✓ |

---

## 5. Investigation Workflow

```
Alert Generated (Phase 16)
    ↓
OPEN (investigation created)
    ↓
UNDER_REVIEW (analyst reviewing)
    ↓
PENDING_VALIDATION (supervisor validation required)
    ↓           ↓
  CLOSED    DISMISSED
```

**Allowed Back-transitions:** PENDING_VALIDATION → UNDER_REVIEW (if re-review needed)

**Transitions to CLOSED and DISMISSED** require SUPERVISOR or ADMIN role.

---

## 6. Safety & Compliance

### 6.1 What This System Does NOT Do

| Prohibited Action | Status |
|---|---|
| Identify a person as a criminal | ✗ Never |
| Automatically accuse anyone | ✗ Never |
| Automatically freeze accounts | ✗ Never |
| Automatically block transactions | ✗ Never |
| Automatically block ATM cards | ✗ Never |
| Automatically contact suspects | ✗ Never |
| Automatically perform law enforcement actions | ✗ Never |

### 6.2 Sensitive Data Protection

| Data Category | Stored | Exposed | Logged |
|---|:---:|:---:|:---:|
| Card numbers | ✗ | ✗ | ✗ |
| Account numbers | ✗ | ✗ | ✗ |
| PINs / CVVs / OTPs | ✗ | ✗ | ✗ |
| Passwords (plaintext) | ✗ | ✗ | ✗ |
| Passwords (bcrypt hash) | ✓ | ✗ | ✗ |
| Aadhaar / National ID | ✗ | ✗ | ✗ |
| Full name / address | ✗ | ✗ | ✗ |

### 6.3 Disclaimers

Every interface layer includes the mandatory disclaimer:
> *"This prototype is an analytical decision-support system. Predictive risk scores and spatial
> hotspots are not proof of criminal activity and do not identify criminal responsibility.
> This prototype is not connected to live NCRP, banking, ATM, or financial institution systems."*

---

## 7. Prototype Authentication

| Credential | Role | Notes |
|---|---|---|
| `demo_analyst` / `AnalystDemo2026!` | ANALYST | Configurable via env vars |
| `demo_supervisor` / `SupervisorDemo2026!` | SUPERVISOR | Configurable via env vars |
| `demo_admin` / `AdminDemo2026!` | ADMIN | Configurable via env vars |

> **CRITICAL:** Change `ANALYST_JWT_SECRET` and demo passwords before any deployment.
> Default JWT secret contains an obvious warning. Prototype auth ≠ production government auth.

---

## 8. Test Coverage

### 8.1 `tests/test_authorization.py` (Unit Tests)
- `TestAuthorizationRoles` (4 tests)
- `TestInvestigationStatusTransitions` (8 tests)
- `TestRolePermissions` (4 tests)
- `TestInputValidation` (7 tests)
- `TestSensitiveDataProtection` (5 tests)
- `TestCRUDFunctions` (5 tests)
- `TestNoAutomaticEnforcement` (3 tests)

**Total: 36 unit tests**

### 8.2 `tests/test_analyst_api.py` (Integration Tests)
- `TestUnauthenticatedAccess` (5 tests)
- `TestAuthentication` (4 tests)
- `TestOverview` (2 tests)
- `TestAlerts` (5 tests)
- `TestInvestigations` (7 tests)
- `TestNotes` (2 tests)
- `TestEvidence` (2 tests)
- `TestTimeline` (1 test)
- `TestExplanation` (2 tests)
- `TestAuditLog` (3 tests)
- `TestHotspots` (2 tests)

**Total: 35 integration tests**

**Grand Total: 71 test cases across Phase 17**

### 8.3 Run Tests
```bash
cd d:\SIH\SIH_2026\cybercrime_prediction
python -m pytest tests/test_authorization.py tests/test_analyst_api.py -v --tb=short
```

---

## 9. Access URLs

| Resource | URL |
|---|---|
| Analyst Interface | http://localhost:8000/analyst |
| GIS Dashboard (Phase 15) | http://localhost:8000/dashboard |
| API Documentation | http://localhost:8000/docs |
| Phase 17 Endpoints | http://localhost:8000/docs#/Analyst%20Interface |

---

## 10. Output Reports

| File | Description |
|---|---|
| `phase17_input_profile.csv` | All API input sources and PII handling |
| `phase17_security_audit.csv` | 18 security controls with evidence |
| `phase17_sensitive_data_audit.csv` | 20 data categories and handling status |
| `phase17_leakage_audit.csv` | 16 data leakage check results |
| `phase17_authorization_test_report.csv` | 62 authorization test cases |
| `phase17_performance_report.csv` | Latency estimates for all 15 endpoints |
| `phase17_analyst_interface_report.md` | This document |

---

## 11. Build Sequence

```
Phase 8  (XGBoost)      → Model
Phase 9  (Risk Scoring) → Alert risk scores
Phase 10 (SHAP)         → Model explainability ← Phase 17 reads
Phase 11 (Pipeline)     → Prediction pipeline
Phase 12 (FastAPI)      → API backbone ← Phase 17 extends
Phase 13 (PostgreSQL)   → Database schema ← Phase 17 adds tables
Phase 14 (DBSCAN)       → Hotspot clusters ← Phase 17 reads
Phase 15 (GIS)          → Dashboard ← Phase 17 links to
Phase 16 (Alerts)       → Alert system ← Phase 17 builds on
Phase 17 (Analyst Interface) ← THIS DOCUMENT
```

---

*Phase 17 completed: 2026-09-16*
*Problem Statement ID: 26184*
*SYNTHETIC DEMONSTRATION DATA — Not real banking or NCRP records.*
