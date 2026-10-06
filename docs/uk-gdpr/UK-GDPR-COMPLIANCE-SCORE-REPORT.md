# UK GDPR Technical Readiness Assessment Report

**Assessment Date**: 2026-10-05  
**Application**: Migraflow — AI Data Migration Platform  
**Repository Branch**: `Neel`  
**Assessment Type**: Baseline Technical Readiness Assessment

---

## 1. Overall Score

# **31 / 100**

## 2. Rating

# **Critical** _(Serious technical privacy and security deficiencies)_

### Score Interpretation Scale:

- `90–100`: Excellent (Strong technical privacy posture; remaining issues mainly require refinement/legal review)
- `80–89`: Very Good (Good technical implementation with some meaningful gaps)
- `70–79`: Good (Reasonable implementation but several improvements remain)
- `60–69`: Needs Improvement (Significant privacy/security gaps)
- `40–59`: Poor (Major technical gaps)
- **`0–39`: Critical (Serious privacy/security deficiencies)**

---

## 3. Score Change

- **Previous Score**: None (Baseline assessment)
- **Current Score**: **31 / 100**
- **Score Delta**: Baseline assessment established

---

## 4. Critical Override Evaluation

- **Status**: **Applied (Cap: 49 / 100)**
- **Reason**: Discovered three Critical Security Exposures:
  1. Permissive Wildcard CORS regex (`^https?://.*$`) with `allow_credentials=True` allowing arbitrary external web origins to steal authenticated user sessions, profile data, and schema metadata.
  2. Severe Broken Object Level Authorization (IDOR) and user harvesting on user profile endpoints (`GET /api/v1/users/{user_id}` and `GET /api/v1/users`).
  3. Committed master database credentials and predictable default JWT fallback secrets in configuration files.
- **Impact**: Under the Critical Override Rule, when critical security exposures or authentication/authorization bypasses are present, the overall score is strictly capped at **49/100**. Because the raw calculated score is **30.8 (rounded to 31 / 100)**, the score remains at **31 / 100**.

---

## 5. Category Scores Table

| Category                                      | Weight  | Rating (0–5) |   Weighted Score    | Key Technical Evidence & Gaps                                                                                                                   |
| :-------------------------------------------- | :-----: | :----------: | :-----------------: | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Personal Data Discovery & Minimisation** |   10    |    3 / 5     |    **6.0 / 10**     | Strong on-premise agent boundary for operational data; gap in flat file loaders capturing `sample_rows[:10]` into catalog storage.              |
| **2. Privacy Information & Transparency**     |    8    |    1 / 5     |     **1.6 / 8**     | Complete absence of Privacy Notice and Cookie Policy; dead links in landing footer (`<a href="#">`); zero point-of-collection notices on forms. |
| **3. Cookies & Tracking / PECR**              |   12    |    2 / 5     |    **4.8 / 12**     | No advertising pixels, but external scripts (`unpkg.com`) and iframes (`my.spline.design`) load unconditionally before consent.                 |
| **4. Consent Management**                     |   10    |    0 / 5     |    **0.0 / 10**     | Completely missing cookie banner, consent preference categories, script gating, and consent withdrawal controls.                                |
| **5. Data Security**                          |   15    |    1 / 5     |    **3.0 / 15**     | Bcrypt hashing implemented, but critical CORS wildcard regex, committed database passwords, and `COOKIE_SECURE=False` defaults.                 |
| **6. Access Control & Authorization**         |   10    |    1 / 5     |    **2.0 / 10**     | Agent/plan ownership verified, but severe IDOR on `GET /users/{id}` and public listing of all users via `GET /users`.                           |
| **7. Data Retention & Deletion**              |   10    |    2 / 5     |    **4.0 / 10**     | Indefinite database retention with no automated cleanup; unpurged DuckDB staging files on local agents if jobs abort.                           |
| **8. User Rights & Privacy Controls**         |    8    |    1 / 5     |     **1.6 / 8**     | Backend supports profile update and deletion, but zero frontend UI screens exist; no Data Portability export mechanism.                         |
| **9. Third-Party Processors & Sharing**       |    5    |    2 / 5     |     **2.0 / 5**     | Plan generation uses structural metadata only; but failure diagnosis leaks raw database constraint error traces to US AI APIs.                  |
| **10. International Data Transfers**          |    3    |    2 / 5     |     **1.2 / 3**     | Data sent to US-based SaaS providers (Google, OpenAI, LangSmith, Spline, AWS) without documented UK IDTA/SCC transfer safeguards.               |
| **11. Logging & Monitoring Privacy**          |    4    |    2 / 5     |     **1.6 / 4**     | `CredentialSanitizer` masks passwords/tokens, but `email.py` logs plaintext user emails during password resets.                                 |
| **12. Privacy by Design**                     |    5    |    2 / 5     |     **2.0 / 5**     | Strong data-plane design (agent transforms data locally), but insecure defaults (`COOKIE_SECURE=False`, LangSmith tracing enabled).             |
| **TOTAL**                                     | **100** |      —       | **30.8 → 31 / 100** | **Critical technical privacy readiness rating**                                                                                                 |

---

## 6. Score Calculation Breakdown

```text
Category 1 (Personal Data):          (3 / 5) × 10 =  6.00 points
Category 2 (Transparency):           (1 / 5) ×  8 =  1.60 points
Category 3 (Cookies / PECR):         (2 / 5) × 12 =  4.80 points
Category 4 (Consent Management):     (0 / 5) × 10 =  0.00 points
Category 5 (Data Security):          (1 / 5) × 15 =  3.00 points
Category 6 (Access Control):         (1 / 5) × 10 =  2.00 points
Category 7 (Data Retention):         (2 / 5) × 10 =  4.00 points
Category 8 (User Rights):            (1 / 5) ×  8 =  1.60 points
Category 9 (Third Parties):          (2 / 5) ×  5 =  2.00 points
Category 10 (Transfers):             (2 / 5) ×  3 =  1.20 points
Category 11 (Logging):               (2 / 5) ×  4 =  1.60 points
Category 12 (Privacy by Design):     (2 / 5) ×  5 =  2.00 points
────────────────────────────────────────────────────────────────
Raw Total:                                          30.80 / 100
Rounded Final Score:                                   31 / 100
Critical Override Cap Applied:                         49 / 100 (Raw score 31 <= 49)
```

---

## 7. Findings Register

### 7.1 Critical Severity Findings

#### `GDPR-SEC-001`: Wildcard CORS Origin Regex with Credentials Enabled

- **Severity**: CRITICAL
- **Category**: Security / Access Control / UK GDPR Art. 5(1)(f) & Art. 32
- **Evidence**: [apps/api/app/main.py:98-105](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/main.py#L98-L105), [docker-compose.yml:43](file:///d:/GitHub/Ai_data_migration_platform/docker-compose.yml#L43), [.env.example:39](file:///d:/GitHub/Ai_data_migration_platform/.env.example#L39)
- **Risk**: Any external web page can issue credentialed cross-origin requests stealing user profile data, agent tokens, schema metadata, and execution blueprints.
- **Recommended Action**: Remove `*` from `CORS_ORIGINS`, delete `allow_origin_regex=r"^https?://.*$"`, and enforce strict origin whitelisting.

#### `GDPR-SEC-002`: Broken Access Control & IDOR on User Profile Endpoints

- **Severity**: CRITICAL
- **Category**: Access Control / IDOR / UK GDPR Art. 5(1)(f) & Art. 32
- **Evidence**: [apps/api/app/modules/users/users_routes.py:578-611](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/modules/users/users_routes.py#L578-L611)
- **Risk**: Any authenticated user can view any other user's profile (`GET /users/{id}`) or enumerate the entire user directory (`GET /users`), causing a personal data breach.
- **Recommended Action**: Restrict `GET /users/{id}` to own account; restrict `GET /users` behind an admin role check.

#### `GDPR-SEC-003`: Committed Database Passwords & Predictable Default JWT Secrets

- **Severity**: CRITICAL
- **Category**: Secrets Management / UK GDPR Art. 32
- **Evidence**: [DATABASE_CREDENTIALS.md:19-24](file:///d:/GitHub/Ai_data_migration_platform/DATABASE_CREDENTIALS.md#L19-L24), [docker-compose.yml:40-47](file:///d:/GitHub/Ai_data_migration_platform/docker-compose.yml#L40-L47), [apps/api/app/core/config.py:15-16](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/core/config.py#L15-L16)
- **Risk**: Hardcoded passwords committed to Git; default fallback secret keys enable JWT token forgery and total platform takeover.
- **Recommended Action**: Add startup assertions terminating production boot if default secrets are used; untrack credential markdown files from Git.

---

### 7.2 High Severity Findings

#### `GDPR-TRK-001`: Third-Party Scripts & Iframes Loaded Prior to Consent

- **Severity**: HIGH
- **Category**: Cookies / Tracking / PECR Regulation 6
- **Evidence**: [apps/web/components/landing/SplineHeroBackground.tsx:57-61](file:///d:/GitHub/Ai_data_migration_platform/apps/web/components/landing/SplineHeroBackground.tsx#L57-L61), [apps/web/components/auth/AuthLayout.tsx:19](file:///d:/GitHub/Ai_data_migration_platform/apps/web/components/auth/AuthLayout.tsx#L19)
- **Risk**: Unpkg CDN script and Spline 3D iframe load automatically on `/` and `/login`, transmitting visitor IP addresses to US CDNs without prior consent.
- **Recommended Action**: Self-host the web component runtime; gate 3D canvas loading behind cookie consent.

#### `GDPR-CONS-001`: Complete Absence of Cookie Consent Banner & Controls

- **Severity**: HIGH
- **Category**: Consent Management / PECR Regulation 6 & UK GDPR Art. 7
- **Evidence**: [apps/web/app/layout.tsx:1-25](file:///d:/GitHub/Ai_data_migration_platform/apps/web/app/layout.tsx#L1-L25), [apps/web/components/landing/Footer.tsx:96-102](file:///d:/GitHub/Ai_data_migration_platform/apps/web/components/landing/Footer.tsx#L96-L102)
- **Risk**: Direct violation of PECR; footer legal links are dead anchors; no preference management or withdrawal mechanism exists.
- **Recommended Action**: Build a client-side Cookie Consent Banner with Accept, Reject, and Category Preferences.

#### `GDPR-NOT-001`: Missing Privacy Notice at Personal Data Collection Points

- **Severity**: HIGH
- **Category**: Transparency / UK GDPR Art. 12 & 13
- **Evidence**: [apps/web/components/auth/RegisterForm.tsx:1-175](file:///d:/GitHub/Ai_data_migration_platform/apps/web/components/auth/RegisterForm.tsx#L1-L175), [apps/web/components/auth/LoginForm.tsx:1-143](file:///d:/GitHub/Ai_data_migration_platform/apps/web/components/auth/LoginForm.tsx#L1-L143)
- **Risk**: Personal data collected on registration and login without informing users of controller identity, lawful basis, or rights.
- **Recommended Action**: Publish `/privacy` and `/terms` pages, and add explicit point-of-collection links on forms.

#### `GDPR-AI-001`: Database Exception Traces Forwarded to External AI APIs & LangSmith

- **Severity**: HIGH
- **Category**: AI Privacy / International Transfers / UK GDPR Art. 5(1)(c) & Art. 28
- **Evidence**: [apps/api/app/modules/execution/execution_services.py:859-860](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/modules/execution/execution_services.py#L859-L860), [docker-compose.yml:49-56](file:///d:/GitHub/Ai_data_migration_platform/docker-compose.yml#L49-L56)
- **Risk**: Database unique constraint violations echoing raw row values are sent unredacted to Google Gemini / OpenAI and LangSmith in the US.
- **Recommended Action**: Mask row values and emails in error messages before prompt interpolation; disable LangSmith by default in production.

#### `GDPR-SEC-004`: Sensitive JWT Tokens in WebSocket URL Query Strings & LocalStorage Fallback

- **Severity**: HIGH
- **Category**: Session Security / UK GDPR Art. 32
- **Evidence**: [apps/api/app/modules/agents/agents_routes.py:168-178](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/modules/agents/agents_routes.py#L168-L178), [apps/web/components/agents/DockerCommandOutput.tsx:80](file:///d:/GitHub/Ai_data_migration_platform/apps/web/components/agents/DockerCommandOutput.tsx#L80)
- **Risk**: JWT tokens accepted in `?token=` query parameters are leaked in server access logs; frontend reads `localStorage` access tokens as agent tokens.
- **Recommended Action**: Enforce first-frame JSON WebSocket authentication; remove `localStorage` access token fallbacks.

#### `GDPR-LOG-001`: Plaintext User Email Addresses Logged in Application Console

- **Severity**: HIGH
- **Category**: Logging / UK GDPR Art. 5(1)(f) & Art. 32
- **Evidence**: [apps/api/app/core/email.py:54, 57](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/core/email.py#L54-L57)
- **Risk**: Plaintext email addresses logged to container `stdout` during password reset flows.
- **Recommended Action**: Mask email addresses in application logs (e.g. `j***n@domain.com`).

---

### 7.3 Medium Severity Findings

- **`GDPR-RIGHTS-001`**: Missing Data Portability API (`GET /users/me/export`) and lack of web UI for profile editing and account deletion ([apps/api/app/modules/users/users_routes.py](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/modules/users/users_routes.py), [apps/web/app/](file:///d:/GitHub/Ai_data_migration_platform/apps/web/app/)).
- **`GDPR-SEC-005`**: Insecure default cookie configuration (`COOKIE_SECURE=False`) transmitting session tokens over unencrypted HTTP ([apps/api/app/core/config.py:21](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/core/config.py#L21)).
- **`GDPR-SEC-006`**: Account enumeration vulnerability on password reset endpoint returning 404 for non-existent emails ([apps/api/app/modules/users/users_routes.py:437-440](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/modules/users/users_routes.py#L437-L440)).
- **`GDPR-OBS-001`**: Missing tenant isolation on observability endpoints allowing users to query traces and LLM logs of other users ([apps/api/app/modules/observability/observability_routes.py:36-50](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/modules/observability/observability_routes.py#L36-L50)).
- **`GDPR-RET-001`**: Indefinite personal data retention across database tables and unpurged DuckDB staging files in `/tmp` ([apps/api/app/modules/users/users_models.py](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/modules/users/users_models.py), [apps/agent/engine/orchestrator.py:67-83](file:///d:/GitHub/Ai_data_migration_platform/apps/agent/engine/orchestrator.py#L67-L83)).

---

### 7.4 Low Severity Findings

- **`GDPR-MIN-001`**: Raw customer row sampling (`sample_rows[:10]`) in flat file loaders ([sources_loaders_csv.py:86](file:///d:/GitHub/Ai_data_migration_platform/apps/api/app/modules/sources/sources_loaders/sources_loaders_csv.py#L86)).
- **`GDPR-PWD-001`**: Restrictive 12-character maximum password limit in frontend registration form ([RegisterForm.tsx:138-140](file:///d:/GitHub/Ai_data_migration_platform/apps/web/components/auth/RegisterForm.tsx#L138-L140)).

---

## 8. Largest Score Deductions

The following technical deficiencies account for the largest point losses from the 100-point ceiling:

1. **Consent Management Deficiency (-10.0 points)**:  
   Complete absence of a cookie consent banner, category controls, preference storage, and script gating resulted in a 0/5 rating in Category 4.
2. **Data Security Vulnerabilities (-12.0 points)**:  
   Wildcard CORS regex, committed passwords in Git, and unencrypted cookie defaults reduced Category 5 from 15.0 to 3.0 points.
3. **Access Control & IDOR Failures (-8.0 points)**:  
   Public user harvesting via `GET /users` and IDOR on `GET /users/{id}` reduced Category 6 from 10.0 to 2.0 points.
4. **Missing Privacy Notices & Transparency (-6.4 points)**:  
   Dead footer links and zero points of collection notices reduced Category 2 from 8.0 to 1.6 points.
5. **Cookies & Third-Party CDN Scripts (-7.2 points)**:  
   Loading Unpkg scripts and Spline iframes prior to consent reduced Category 3 from 12.0 to 4.8 points.
6. **Data Subject Rights Technical Gaps (-6.4 points)**:  
   No export mechanism and missing frontend UI for profile update and deletion reduced Category 8 from 8.0 to 1.6 points.
7. **Indefinite Data Retention (-6.0 points)**:  
   Absence of automated database purge tasks and lingering agent staging files reduced Category 7 from 10.0 to 4.0 points.

---

## 9. Highest-Impact Next Improvements

Executing the following prioritized technical fixes from [UK-GDPR-REMEDIATION-PLAN.md](file:///d:/GitHub/Ai_data_migration_platform/UK-GDPR-REMEDIATION-PLAN.md) will deliver the highest score gains:

```text
┌───────────────────────────────────────────────────────────┬───────────────┬─────────────────┐
│ Remediation Action                                        │ Target Area   │ Estimated Gain  │
├───────────────────────────────────────────────────────────┼───────────────┼─────────────────┤
│ 1. Fix CORS Wildcard Regex & Enforce Strict Whitelist     │ Security      │ +6.0 points     │
│ 2. Remediate User IDOR & Restrict /users to Admins        │ Access Control│ +5.0 points     │
│ 3. Implement Cookie Consent Banner & Gate Third-Party CDN │ Consent/PECR  │ +10.0 points    │
│ 4. Publish Privacy Notices & Link on Registration/Login   │ Transparency  │ +4.8 points     │
│ 5. Implement Data Portability API & Settings UI           │ User Rights   │ +4.8 points     │
│ 6. Sanitize DB Error Traces for AI & Disable LangSmith    │ AI / Sharing  │ +3.0 points     │
│ 7. Automate Retention Purge & Delete Staging Files        │ Retention     │ +3.0 points     │
├───────────────────────────────────────────────────────────┴───────────────┼─────────────────┤
│ PROJECTED SCORE AFTER PRIORITY REMEDIATIONS:                              │ 68 / 100        │
└───────────────────────────────────────────────────────────────────────────┴─────────────────┘
```

---

## 10. Unknown Information & Required Business / Legal Decisions

The following items cannot be determined purely from source code inspection and require formal determination by the business owner and legal counsel:

1. **Authorized Production Domain Whitelist**: Define the exact domain names and staging origins permitted to access the API via CORS.
2. **Statutory Privacy Policy & Cookie Policy Text**: Legal counsel must draft and approve the official Privacy Notice and Cookie Policy to replace dead links.
3. **Data Retention Schedule**: Business definition of approved retention timeframes for migration plans, schema snapshots, and execution trace logs.
4. **Third-Party Data Processing Agreements (DPAs)**: Formal execution of DPAs with Google Cloud, OpenAI, and LangChain Inc., incorporating the UK International Data Transfer Agreement (IDTA).
5. **Physical AWS Hosting Region**: Verification of the AWS EC2 hosting region (`eu-west-2` London vs US) to determine if domestic processing applies.
6. **Data Subject Request (DSR) Standard Operating Procedures**: Operational policy defining how requests for access, rectification, and erasure are tracked and fulfilled within the statutory 30-day timeline.

---

## 11. Score Confidence

### **Confidence Level: HIGH**

**Justification**:  
The audit had complete, unrestricted read access to the entire monorepo, including frontend pages, components, backend API routes, database models, background watchdogs, Docker configurations, CI/CD deployment workflows, and environment variable templates. The identified technical gaps are supported by exact file paths and line numbers.

---

## 12. Score Limitations

> **IMPORTANT NOTICE**:  
> This score is an **internal technical privacy-readiness engineering metric** created from repository evidence. It is **NOT** an official ICO rating, legal certification, or determination of UK GDPR compliance.  
> Legal compliance depends on organizational processes, contracts, policies, lawful bases, governance, data-processing activities, physical infrastructure controls, and operational handling that cannot be evaluated solely from source code.

---

## 13. Final Statement

This technical assessment establishes an internal baseline score of **31 / 100 (Critical)** for the Migraflow platform.

The application possesses a strong architectural foundation in its on-premise Docker Agent model (which keeps raw database migration records local to customer infrastructure), but significant technical security and privacy engineering remediation is required on the control-plane web application and backend API before it can achieve a Good or Excellent privacy posture.

Executing Phase 1 (Critical Security) and Phase 2 (Consent & Tracking) of the [UK-GDPR-REMEDIATION-PLAN.md](file:///d:/GitHub/Ai_data_migration_platform/UK-GDPR-REMEDIATION-PLAN.md) will resolve all three critical vulnerabilities and lift the score toward an estimated **68 / 100**.
