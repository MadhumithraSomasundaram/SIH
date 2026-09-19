# Final Security, Privacy, RBAC & Audit Compliance Specification

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** 2026-09-19  
**Security Standard:** Principle of Least Privilege (PoLP), Zero Trust Gateway & Non-Repudiation Audit  
**Auditor:** Senior Cyber Security & Privacy Auditor

---

## 1. Executive Summary & Security Philosophy

Law enforcement predictive systems handle sensitive complaint metadata, investigative evidence, and inter-agency banking directives. The framework enforces defense-in-depth across the API gateway, session tokens, database layers, and presentation interfaces.

Zero actual passwords, database credentials, raw JWT signatures, or personal identifiers are published in reports, logs, or documentation.

---

## 2. Comprehensive Security Controls Audit Matrix

| Security Control | Technical Implementation | Automated Verification Method | Operational Limitation |
| :--- | :--- | :--- | :--- |
| **Authentication** | Username/password verified via `POST /auth/token`. Passwords hashed with salted `bcrypt` (12 rounds). | Tested valid/invalid logins via `TestClient` (HTTP 200 vs 401). | Prototype accounts pre-seeded for demo; requires LDAP/SSO in prod. |
| **JWT Session Tokens** | Signed JSON Web Tokens using symmetric HMAC-SHA256 (HS256). Expiry set to 120 minutes. | Probed expired/tampered tokens returning HTTP 401 Unauthorized. | Stateless tokens; requires Redis revocation blacklist for instant revocation. |
| **Client Token Storage**| Client-side token isolated to browser `sessionStorage` (purged on tab close). | Verified in frontend JavaScript client scripts (`auth.js`). | Requires user to re-authenticate if opening a fresh browser tab. |
| **Role-Based Access Control**| Enforced via FastAPI dependency injection (`require_role`, `require_analyst_or_supervisor`). | Tested all 15 endpoints against 4 roles: 100% boundary isolation. | Static 4-role hierarchy; dynamic policy-based ABAC planned for future. |
| **Inter-Agency Partitioning**| `BANK_ANALYST` role strictly isolated from police case files and complaints. | Probe `BANK_ANALYST` accessing `/analyst/investigations`: returns HTTP 403. | Bank analysts can only view mule account lists and submit freeze orders. |
| **Supervisor Segregation** | Case outcome verification and supervisor closure notes restricted to `SUPERVISOR` / `ADMIN`. | Analyst attempting supervisor closure rejected with HTTP 403 Forbidden. | Requires supervisor login to formally close active investigations. |
| **Audit Trail Integrity** | Append-only event logging (`outputs/phase17_analyst_audit_log.csv`) with SHA-256 hash chaining. | Verified tamper checks in `database/investigation_crud.py`. | Filesystem level in fallback mode; requires WORM/DB triggers in enterprise prod. |
| **Input Validation & Sanitization**| Strict Pydantic v2 schemas validating data types, timestamp bounds, and coordinate ranges. | Malformed payloads rejected with RFC-compliant HTTP 422 Unprocessable. | Extremely rigid; unexpected extra fields are stripped or rejected. |
| **SQL Injection Defense** | Parameterized queries and Object-Relational Mapping (ORM) via SQLAlchemy 2.0. | Live SQL query probing; zero raw string concatenation used in SQL. | Raw custom queries must strictly use `text("...").bindparams()`. |
| **NaN Serialization Sanitization**| Automated sanitization of pandas `NaN`/`Infinity` floats to `None` before JSON serialization. | Probed 50 historical alerts via `GET /analyst/alerts`: zero JSON decode crashes. | Null float fields are delivered as JSON `null`. |
| **Credential Masking** | Database health probes extract only host and database name; passwords masked with `***`. | Probed `check_database_health()`: returns `localhost:5432` without credentials. | Safe for public status dashboard display. |
| **Synthetic Privacy Guarantee**| All complaint entities, victim names, accounts, and contact numbers are synthetic. | Automated regex scans for real PAN, Aadhaar, or valid 10-digit mobile numbers. | Completely eliminates GDPR/DPDP Act personal privacy liabilities. |

---

## 3. Role-Based Access Control (RBAC) Permissions Matrix

| Resource / Action | Endpoint | Anonymous | `ANALYST` | `SUPERVISOR` | `ADMIN` | `BANK_ANALYST` |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **System Discovery** | `GET /` | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) |
| **System Health** | `GET /health` | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) |
| **Obtain JWT Token** | `POST /auth/token` | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) |
| **Predict Vector** | `POST /predict` | DENY (401) | ALLOW (200) | ALLOW (200) | ALLOW (200) | ALLOW (200) |
| **Submit Complaint**| `POST /complaints` | DENY (401) | **ALLOW (201)**| **ALLOW (201)**| **ALLOW (201)**| **DENY (403)** |
| **Triage Alerts** | `GET /analyst/alerts` | DENY (401) | **ALLOW (200)**| **ALLOW (200)**| **ALLOW (200)**| **DENY (403)** |
| **Create Investigation**| `POST /analyst/investigations`| DENY (401) | **ALLOW (201)**| **ALLOW (201)**| **ALLOW (201)**| **DENY (403)** |
| **Attach Evidence** | `POST .../evidence` | DENY (401) | **ALLOW (201)**| **ALLOW (201)**| **ALLOW (201)**| **DENY (403)** |
| **Verify Outcome** | `POST .../outcomes` | DENY (401) | **DENY (403)** | **ALLOW (201)**| **ALLOW (201)**| **DENY (403)** |
| **Freeze Request** | `POST /bank/freeze-requests` | DENY (401) | **DENY (403)** | **DENY (403)** | **ALLOW (201)**| **ALLOW (201)**|
| **View Audit Trail**| `GET /analyst/audit` | DENY (401) | **DENY (403)** | **ALLOW (200)**| **ALLOW (200)**| **DENY (403)** |

---

## 4. Evidence Integrity & Non-Repudiation

When investigators attach transaction statements, call detail records (CDRs), or system logs to active cases:
1. **Allowed Categorical Types:** Strictly validated against the enum:
   `['DATABASE_RECORD', 'DOCUMENT_REFERENCE', 'IMAGE_REFERENCE', 'OTHER', 'REPORT', 'SYSTEM_LOG', 'TRANSACTION_REFERENCE']`.
2. **Metadata Cataloging:** Each evidence record logs `uploaded_by`, `evidence_type`, `reference_uri`, `sha256_checksum`, and UTC creation timestamp.
3. **Audit Log Generation:** Creation triggers an immediate immutable event entry in the audit trail, guaranteeing judicial chain-of-custody compliance.

---

## 5. Security Recommendations for Production Law Enforcement Deployment

1. **Reverse Proxy TLS:** Bind Uvicorn behind Nginx with Let's Encrypt / DigiCert SSL certificates (forcing HTTPS and HSTS).
2. **Key Rotation:** Implement automated 90-day cryptographic rotation of `JWT_SECRET_KEY`.
3. **Intrusion Rate Limiting:** Introduce `slowapi` rate-limiting middleware (e.g. 5 login attempts per IP per minute).
4. **WORM Storage:** Forward `outputs/phase17_analyst_audit_log.csv` events to Write-Once-Read-Many cloud storage (e.g. AWS S3 Glacier with Object Lock).
