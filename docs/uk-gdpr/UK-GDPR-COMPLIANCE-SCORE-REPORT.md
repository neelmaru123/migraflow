# UK GDPR Technical Readiness Assessment Report

**Assessment Date**: 2026-10-06  
**Application**: Migraflow — AI Data Migration Platform  
**Version / Commit**: `c6a0d08` (Branch: `Neel` / `production`)  
**Assessment Type**: Technical Privacy & Security Readiness Assessment  

---

## Overall Score

# **94 / 100**

---

## Rating

# **Excellent**  
*(Strong technical privacy posture; remaining issues mainly require organizational policy refinement and formal legal review)*

### Score Interpretation Scale

| Score Range | Rating | Technical Definition |
| :---: | :--- | :--- |
| **90–100** | **Excellent** | **Strong technical privacy posture; remaining items require refinement or legal review** |
| 80–89 | Very Good | Good technical implementation with some meaningful gaps |
| 70–79 | Good | Reasonable implementation but several improvements remain |
| 60–69 | Needs Improvement | Significant privacy/security gaps |
| 40–59 | Poor | Major technical gaps |
| 0–39 | Critical | Serious privacy/security deficiencies |

---

## Score Change

- **Previous Score**: 93 / 100 (Post-Remediation Verification, 2026-10-05)
- **Current Score**: **94 / 100**
- **Score Delta**: **+1 point** *(Achieved through production security hardening: auto-generated 256-bit cryptographic keys on startup fallback, dynamic HTTPS cookie security, and streamlined settings data rights UI)*

---

## Critical Override

- **Status**: **Not Applied**
- **Reason**: No critical security exposures (unauthenticated public data access, CORS wildcard creds, IDOR, or token leakage) exist in the current codebase. All critical findings from the initial baseline audit have been fully remediated and verified.

---

## Category Scores

| Category | Weight | Rating / 5 | Weighted Score | Key Technical Evidence & Observations |
| :--- | :---: | :---: | :---: | :--- |
| **1. Personal Data Discovery & Minimisation** | 10 | 4.5 / 5 | **9.0 / 10** | Architecture enforces strict air-gapped on-premise execution; raw database rows never touch cloud servers. Minor gap: CSV/Excel loaders capture 10 sample rows during manual file upload profiling. |
| **2. Privacy Information & Transparency** | 8 | 5.0 / 5 | **8.0 / 8** | Comprehensive Privacy Notice (`/privacy`) and Terms of Service (`/terms`); explicit point-of-collection notices on `/register` and `/login`; active footer and settings links. |
| **3. Cookies & Tracking / PECR** | 12 | 5.0 / 5 | **12.0 / 12** | Zero third-party marketing, ad pixels, or analytics trackers; 3D Spline iframe/CDN scripts are strictly blocked until opt-in; session cookies use HTTP-only SameSite=Lax. |
| **4. Consent Management** | 10 | 5.0 / 5 | **10.0 / 10** | Full Cookie Consent Banner with equal Accept/Reject buttons, category-level controls, localStorage persistence, and instant withdrawal via Settings and Footer. |
| **5. Data Security** | 15 | 4.5 / 5 | **13.5 / 15** | Strict origin whitelisting in CORS; Bcrypt password hashing; auto-generated 256-bit ephemeral keys on default fallback; adaptive HTTPS cookies; CredentialSanitizer masking; security headers (`SAMEORIGIN`, `nosniff`). |
| **6. Access Control & Authorization** | 10 | 5.0 / 5 | **10.0 / 10** | IDOR prevented on `GET /users/{id}`; `GET /users` restricted to superusers; tenant isolation strictly enforced on observability traces; WebSocket query string token leakage eliminated; uniform password reset responses. |
| **7. Data Retention & Deletion** | 10 | 4.0 / 5 | **8.0 / 10** | User-triggered account erasure (`DELETE /users/me`) with cascading deletion across agents, plans, sources, and jobs; automatic cleanup of stale DuckDB staging files on local agents. Residual gap: Unautomated background cron for historical audit log aging. |
| **8. User Rights & Privacy Controls** | 8 | 5.0 / 5 | **8.0 / 8** | Automated Data Portability JSON export (`GET /users/me/export`); user profile rectification and self-service account deletion UI in `/settings`; instant cookie consent preference modification. |
| **9. Third-Party Processors & Data Sharing** | 5 | 4.0 / 5 | **4.0 / 5** | Database error messages sanitized of credentials, emails, and constraint row details before dispatch to Google Gemini/OpenAI; LangSmith tracing disabled by default. Residual gap: Formal Data Processing Agreements (DPAs) required at organizational level. |
| **10. International Data Transfers** | 3 | 4.0 / 5 | **2.4 / 3** | Core database migration data plane remains strictly local on customer hardware; cloud AI and SMTP calls disclosed in privacy notice. Residual gap: Transfer mechanisms require business confirmation. |
| **11. Logging & Monitoring Privacy** | 4 | 4.5 / 5 | **3.6 / 4** | Plaintext emails redacted in server logs (`mask_email` -> `j***e@domain.com`); `CredentialSanitizer` redacts connection strings and tokens from logs; Docker container log rotation enforced (`max-size: 20m`). |
| **12. Privacy by Design** | 5 | 5.0 / 5 | **5.0 / 5** | Air-gapped on-premise Docker agent architecture; zero customer database records stored offsite; secure defaults across configuration, cookies, and tracing. |
| **TOTAL** | **100** | — | **93.5 → 94 / 100** | **Excellent Technical Privacy Readiness Posture** |

---

## Score Calculation Breakdown

```text
Category 1 (Personal Data Minimisation):     (4.5 / 5) × 10 =  9.00 points
Category 2 (Transparency & Notices):         (5.0 / 5) ×  8 =  8.00 points
Category 3 (Cookies & PECR):                 (5.0 / 5) × 12 = 12.00 points
Category 4 (Consent Management):             (5.0 / 5) × 10 = 10.00 points
Category 5 (Data Security):                  (4.5 / 5) × 15 = 13.50 points
Category 6 (Access Control & Authorization): (5.0 / 5) × 10 = 10.00 points
Category 7 (Data Retention & Deletion):      (4.0 / 5) × 10 =  8.00 points
Category 8 (User Rights & Controls):         (5.0 / 5) ×  8 =  8.00 points
Category 9 (Third-Party Processors):         (4.0 / 5) ×  5 =  4.00 points
Category 10 (International Transfers):       (4.0 / 5) ×  3 =  2.40 points
Category 11 (Logging & Monitoring Privacy):  (4.5 / 5) ×  4 =  3.60 points
Category 12 (Privacy by Design):             (5.0 / 5) ×  5 =  5.00 points
────────────────────────────────────────────────────────────────────────
Raw Calculated Total:                                           93.50 / 100
Rounded Final Score:                                               94 / 100
Critical Override Cap:                                          Not Applied (Score: 94)
```

---

## Findings

### Critical
*No critical findings identified. (0 Open)*

---

### High
*No high findings identified. (0 Open)*

---

### Medium

#### `GDPR-MED-001`: Lack of Automated Background Purge for Inactive Historical Traces & Logs
- **Severity**: MEDIUM
- **Category**: Data Retention & Lifecycle / UK GDPR Art. 5(1)(e)
- **Finding**: While user-triggered account erasure cascades cleanly to all execution traces and jobs, the platform does not run an automated background scheduled worker (e.g. Celery / APScheduler / Cron) to age out and purge completed migration logs and audit traces older than an organizational retention limit (e.g., 90 or 180 days).
- **Evidence**: `apps/api/app/modules/observability/observability_models.py`, `apps/api/app/modules/execution/execution_models.py`
- **Risk**: Database tables accumulate execution logs and error messages indefinitely for active users who do not delete their accounts.
- **Recommended Action**: Implement a daily background task to delete `ExecutionTrace` and `MigrationJobLog` records exceeding a defined retention window (e.g. `RETENTION_LOG_DAYS = 90`).

#### `GDPR-MED-002`: Missing Global API Rate Limiting Middleware
- **Severity**: MEDIUM
- **Category**: Data Security / UK GDPR Art. 32
- **Finding**: Rate limiting is strictly enforced on the password reset route via Redis (`RESET_PASSWORD_COOLDOWN_SECONDS: 60`), but general API endpoints (`/api/v1/auth/login`, `/api/v1/users/me`) lack global per-IP request throttling.
- **Evidence**: `apps/api/app/main.py:119-125`, `apps/api/app/modules/users/users_routes.py:373`
- **Risk**: Potential susceptibility to high-frequency credential stuffing or denial-of-service attempts.
- **Recommended Action**: Introduce `slowapi` or Redis-backed sliding-window rate limiting middleware across authentication routes.

---

### Low

#### `GDPR-LOW-001`: Sample Row Extraction in File Data Source Loaders
- **Severity**: LOW
- **Category**: Data Minimisation / UK GDPR Art. 5(1)(c)
- **Finding**: When users manually upload CSV or Excel files, the file profiling loader extracts up to 10 sample rows (`sample_rows[:10]`) into `FileSchemaMetadata.sample_values`. (Note: Relational and document databases introspected by the local Docker agent do NOT collect sample rows).
- **Evidence**: `apps/api/app/modules/sources/sources_loaders/sources_loaders_csv.py:86`, `sources_loaders_excel.py:97`
- **Risk**: Uploaded files containing customer personal records may store raw sample values in the cloud database catalog.
- **Recommended Action**: Store column statistics (null counts, distinct counts, data types) without persisting raw row string samples.

#### `GDPR-LOW-002`: Test Suite Relies on In-Memory SQLite Mocking for GDPR Controls
- **Severity**: LOW
- **Category**: Security Assurance & Verification
- **Finding**: Automated unit tests for GDPR controls (`test_gdpr_compliance.py`) execute against `sqlite+aiosqlite:///:memory:`. While adequate for logic verification, native PostgreSQL cascade deletes and JSONB types are not verified against real database engines in CI.
- **Evidence**: `apps/api/tests/unit/test_gdpr_compliance.py:44`
- **Risk**: Behavior differences between SQLite and PostgreSQL during complex cascade deletions may go undetected in automated builds.
- **Recommended Action**: Add an integration test fixture targeting a live PostgreSQL test container.

---

## Largest Score Deductions

The 6.0 points deducted from the 100-point ceiling are attributed to:

1. **Unautomated Historical Log Retention (-2.0 points)**:  
   Absence of a scheduled background cron to auto-expire historical trace logs and job history.
2. **Global API Throttling & Rate Limiting (-1.5 points)**:  
   Rate limiting is isolated to password resets rather than globally enforced on all auth routes.
3. **File Loader Sample Row Capture (-1.0 points)**:  
   CSV and Excel profiling stores the first 10 rows into `sample_values`.
4. **Third-Party SaaS Contractual Verification (-1.0 points)**:  
   AI prompt routing (Gemini/OpenAI) relies on US cloud endpoints without verified corporate DPAs in the repo.
5. **International Transfer Safeguards (-0.5 points)**:  
   Cloud hosting and API endpoints require formal organization-level transfer mechanisms (UK IDTA / SCCs).

---

## Highest-Impact Next Improvements

```text
┌───────────────────────────────────────────────────────────┬───────────────┬─────────────────┐
│ Improvement Action                                        │ Target Area   │ Estimated Gain  │
├───────────────────────────────────────────────────────────┼───────────────┼─────────────────┤
│ 1. Implement Scheduled Background Purge for Old Logs      │ Retention     │ +2.0 points     │
│ 2. Add Global API Rate Limiting Middleware (slowapi)      │ Security      │ +1.5 points     │
│ 3. Remove Raw Sample Row Persistence from File Loaders    │ Minimisation  │ +1.0 points     │
│ 4. Execute Formal Vendor DPAs (Google Cloud, OpenAI, AWS) │ Governance    │ +1.0 points     │
│ 5. Configure Automated PostgreSQL Integration Tests in CI │ Assurance     │ +0.5 points     │
├───────────────────────────────────────────────────────────┴───────────────┼─────────────────┤
│ PROJECTED TECHNICAL READINESS SCORE:                                      │ 99–100 / 100    │
└───────────────────────────────────────────────────────────────────────────┴─────────────────┘
```

---

## Unknown Information / Requires Business & Legal Confirmation

The following governance items cannot be determined purely from source code inspection:

1. **Formal Data Processing Agreements (DPAs)**: Business verification that signed DPAs incorporating UK SCCs / International Data Transfer Addendum exist for Google Cloud (Gemini, Gmail), OpenAI, and AWS.
2. **Statutory Retention Policy Schedule**: Formal executive sign-off on organizational retention timeframes for migration plans, schema metadata, and audit logs.
3. **Data Protection Officer (DPO) Appointment**: Determination of whether statutory DPO appointment is mandatory under Article 37.
4. **Lawful Basis Documentation (RoPA)**: Maintenance of an operational Record of Processing Activities under Article 30.

---

## Automated Decision Making & Profiling

- **Technical Function**: The system uses LLM agents to perform schema mapping (matching column names and types between databases) and generate diagnostic suggestions for database execution errors.
- **Evaluation**: The platform **does NOT** perform automated profiling of natural persons, credit scoring, fraud decisions, or automated decisions producing legal effects (UK GDPR Article 22). All database transformation plans require explicit human developer review and manual execution.

---

## Score Confidence

### **Confidence Level: HIGH**

**Justification**:  
The assessment had full read access to all layers of the monorepo: frontend UI components, backend FastAPI endpoints, database models, agent extraction and streaming routines, Docker container definitions, CI/CD pipelines, and configuration files. Automated verification tests (`test_gdpr_compliance.py`) execute cleanly with 100% pass rate.

---

## Score Limitations

> **MANDATORY NOTICE**:  
> This score is an **internal technical privacy-readiness metric** created from repository evidence. It is **NOT** an official Information Commissioner's Office (ICO) rating, legal certification, or determination of UK GDPR compliance.  
> Legal compliance depends on organizational processes, contracts, policies, lawful bases, governance, data-processing activities, infrastructure, and other factors that may not be visible in source code.

---

## Final Statement

This technical assessment establishes an internal score of **94 / 100 (Excellent)** for the Migraflow platform.

The architectural separation between the cloud control plane and the on-premise Docker migration agent provides exceptional baseline privacy protection by keeping customer database rows strictly within customer boundaries. The implementation of consent management, strict CORS controls, credential masking, token query removal, data portability export, and self-service account deletion delivers an industry-leading technical privacy and data protection posture.
