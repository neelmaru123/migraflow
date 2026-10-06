# UK GDPR / PECR Technical Compliance Audit Report

> **LEGAL NOTICE & DISCLAIMER**:  
> This document is a **technical privacy and data protection gap assessment** performed from an application security and privacy engineering perspective. It **does NOT constitute legal confirmation of UK GDPR or PECR compliance** and should not be relied upon as legal advice. All legal determinations regarding lawful bases, data controller/processor classifications, international transfer mechanisms, and regulatory notifications require formal review by qualified legal counsel.

---

## 1. Executive Summary

A comprehensive technical privacy, security, and data protection audit was conducted on the entire **Migraflow (AI Data Migration Platform)** codebase (`apps/web`, `apps/api`, `apps/agent`, `infra`, and associated deployment configurations).

The application is architected as an enterprise-grade AI-assisted database migration platform that provides automated schema translation, ETL streaming via on-premise Docker agents, and AI-driven column mapping and failure diagnosis.

### 1.1 Technical Risk Rating: **HIGH / CRITICAL**

While the core data-plane architecture thoughtfully uses local on-premise Docker agents to keep customer database row payloads off cloud servers during normal ETL execution, the platform possesses **critical technical vulnerabilities and compliance gaps** under the **UK General Data Protection Regulation (UK GDPR)**, the **Data Protection Act 2018 (DPA 2018)**, and the **Privacy and Electronic Communications Regulations (PECR)**.

### 1.2 Summary of Findings by Severity

| Severity | Count | Summary of Key Technical Concerns |
| :--- | :---: | :--- |
| **CRITICAL** | **3** | Permissive Wildcard CORS regex allowing credentialed cross-origin data theft; Complete user enumeration & IDOR on `/users` and `/users/{user_id}`; Plaintext database passwords and production credentials committed to repository. |
| **HIGH** | **6** | Third-party 3D scripts/iframes (`unpkg.com`, `spline.design`) loading prior to consent (PECR violation); Total absence of Cookie Consent management mechanism; Zero Privacy Notices at points of registration/login; Raw database failure exception traces leaking row data into LLM prompts (Gemini/OpenAI/LangSmith); JWT tokens accepted in WebSocket query strings and LocalStorage fallbacks; Plaintext user email addresses logged in server console during password reset flow. |
| **MEDIUM** | **5** | Missing Data Subject Rights mechanisms (Data Portability Art. 20, missing UI for Profile Rectification and Account Deletion); Insecure cookie flag defaults (`COOKIE_SECURE=False`); Account enumeration via password reset error responses; Missing user isolation in observability traces and LLM call records; Indefinite personal data retention across all database tables with no automated purge. |
| **LOW** | **2** | Raw data sample collection (`sample_rows[:10]`) in CSV/Excel file loaders; Restrictive password maximum length (12 characters) in frontend registration. |
| **INFORMATIONAL** | **1** | Missing statutory compliance governance documentation in repository (ROPA, DPIA, DPA agreements, Cookie inventory). |
| **TOTAL** | **17** | **3 Critical, 6 High, 5 Medium, 2 Low, 1 Informational** |

---

## 2. Architecture & Technology Summary

| Architecture Layer | Technology / Implementation | Technical Context & Data Handling |
| :--- | :--- | :--- |
| **Frontend Web App** | Next.js 14 (App Router), React 18, Redux Toolkit, TanStack Query, React Flow, Axios, Tailwind CSS | Serves user interfaces for authentication, agent registration, schema catalog viewing, visual transformation planning, and live execution monitoring. |
| **Backend API** | FastAPI, Uvicorn, Python 3.11, Pydantic v2, SQLAlchemy v2, AsyncPG | Control-plane REST API handling user accounts, JWT issuance, agent registration, schema metadata snapshots, and execution job scheduling. |
| **On-Premise Agent** | Python 3.11, DuckDB, Polars, PyArrow, Docker | Local customer daemon performing database introspection and ETL streaming on customer premises. |
| **Primary Database** | PostgreSQL 16 Alpine (`migration_platform`) | Persists user identities, agent credentials, metadata schema snapshots, transformation plans, execution DAGs, audit events, and trace logs. |
| **Task Queue & Cache** | Redis 7.0 Alpine (`redis://localhost:6379/0`) | Manages job dispatch locks, agent watchdog heartbeats, and 5-minute password reset cryptographic tokens. |
| **Sample Engines** | MySQL 8.0 (`inventory_production`), MongoDB 7.0 (`analytics_production`) | Supported relational and document databases for migration sources and targets. |
| **Authentication** | HS256 JWT, HTTP-only Cookies, Bcrypt, Google OAuth 2.0 (`google-auth`, `@react-oauth/google`) | Authenticates users via password hash or Google Identity token; sets `access_token` (15m) and `refresh_token` (7d) cookies. |
| **AI / LLM Providers** | Google Gemini (`google-generativeai`, `langchain-google-genai`), OpenAI (`langchain-openai`) | Formulates transformation plans from schema metadata; synthesizes plain-English diagnostic summaries for failed execution jobs. |
| **Observability** | LangChain / LangSmith (`api.smith.langchain.com`), custom `ExecutionTrace` & `LLMCallRecord` tables | Traces LLM invocations, token costs, prompt inputs, and execution step latencies. |
| **Transactional Email** | Google Gmail SMTP (`smtp.gmail.com:587`) via Python `smtplib` | Sends 5-minute expiring password reset emails to registered users. |
| **Cloud Hosting** | AWS EC2 (Ubuntu Linux) deployed via GitHub Actions SSH workflow (`deploy-ec2.yml`) | Hosts production Docker Compose containers (`web`, `api`, `postgres`, `redis`). |

---

## 3. Personal Data Discovery & Inventory

Personal data processed across the platform was identified and classified according to UK GDPR Article 4(1) and Article 9 (Special Categories):

| Data Category | Specific Fields | Processing Location | Storage Tier | Identifiability & Sensitivity |
| :--- | :--- | :--- | :--- | :--- |
| **User Identity** | Full Name, Email Address, Google Subject ID (`google_id`) | `apps/api/app/modules/users/users_models.py` | PostgreSQL (`users` table) | Direct personal identifier. High compliance impact. |
| **Authentication Credentials** | Password Hashes (Bcrypt), JWT Access Tokens, JWT Refresh Tokens, Password Reset Tokens | `apps/api/app/core/security.py`, `apps/api/app/core/redis_client.py` | PostgreSQL (`users.password_hash`), Redis (Reset tokens), HTTP Cookies | Critical security credential. Compromise leads to full account takeover. |
| **Agent Authentication** | SHA-256 Agent API Token Hash (`api_token_hash`), Agent Name | `apps/api/app/modules/agents/agents_models.py` | PostgreSQL (`agents` table) | Machine identity tied to a specific user account. |
| **Database Schema Metadata** | Database names, schema names, table names, column names, constraints, foreign keys | `apps/api/app/modules/metadata/metadata_models.py` | PostgreSQL (`metadata_*` tables) | Indirect / Pseudonymous. May reveal business logic or sensitive entities (e.g. `medical_records`, `salaries`). |
| **Raw Sample Rows** | Top 10 sample rows from uploaded CSV / Excel files (`sample_rows[:10]`) | `apps/api/app/modules/sources/sources_loaders/` | Memory & PostgreSQL (`metadata_columns.sample_values`) | **Direct Customer Data**. May contain real names, phone numbers, addresses, or financial transactions. |
| **Error Traces & Diagnostics** | Database error messages, failed SQL statements, constraint violation details | `apps/api/app/modules/execution/execution_models.py` (`MigrationJob.error_message`), `ExecutionTrace.error_message` | PostgreSQL, stdout logs, and forwarded to Google Gemini/OpenAI | **High Risk**. Constraint violations often echo unredacted row values (e.g. `Key (email)=(user@domain.co.uk) already exists`). |
| **Network & Device Metadata** | Client IP Address, User Agent, WebSocket connection state | Web server access logs, reverse proxy headers, Spline / Unpkg requests | Server logs, third-party CDN logs | Online identifiers under UK GDPR Recital 30. |
| **Special Category Data** | Not intentionally collected by core platform schemas; however, **customer source databases** being migrated may contain special category data (health, biometric, racial, political). | Customer source databases streamed locally by on-premise agent; transient DuckDB staging files (`/tmp/staging_*.duckdb`). | Local disk storage on customer machine | High/Critical risk if error messages or file loader sample values capture special category records. |

---

## 4. End-to-End Data Flow Mapping

```text
[User / Browser]
   │
   ├── (1. User Registration / Login: Name, Email, Password, Google Token)
   ▼
[Next.js Web Frontend (apps/web)]
   │
   ├── (2. External 3D Scene / Script Requests: User IP, Browser Headers) ──► [Unpkg CDN / Spline.design (US)]
   │
   ├── (3. HTTP-only Cookie Requests: withCredentials = true)
   ▼
[FastAPI Control Plane (apps/api)]
   │
   ├── (4. Password Hashing: Bcrypt) ──────────────► [PostgreSQL: users table]
   ├── (5. Password Reset Link Dispatch) ──────────► [Google Gmail SMTP: smtp.gmail.com (US)]
   ├── (6. Ephemeral Token & Lock Cache) ──────────► [Redis Cache: redis:6379]
   │
   ├── (7. Schema Metadata Only / User Instructions)
   │      │
   │      ├──► [Google Gemini / OpenAI API (US)] (Plan Generation)
   │      └──► [LangSmith Observability: api.smith.langchain.com (US)] (Trace Prompts)
   │
   └── (8. Migration Failure Diagnosis: Raw err_msg)
          │
          └──► [Google Gemini / OpenAI API (US)] (Failure Explanation)

[Customer On-Premise Environment]
   │
   ├── [Docker Agent (apps/agent)] ◄─── (Pulls Plan JSON from API via X-Agent-Token)
   │      │
   │      ├── (Queries information_schema: Table & Column Names only) ──► Pushed to API
   │      │
   │      ├── (Reads source DB rows in memory chunks via Polars)
   │      ├── (Stages merge tables locally in /tmp/*.duckdb)
   │      └── (Writes batches to target DB directly)
   │
   └── [Customer Databases: PostgreSQL / MySQL / MongoDB]
```

### Personal Data Flow Analysis Table

| Data Flow | Source | Destination | Personal Data Fields | Purpose | Retention | Technical Safeguards | Legal / Risk Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DF-01: User Auth** | Browser | API (`/auth/register`, `/auth/login`) | Name, Email, Password, IP | Account creation & session authentication | Indefinite | Bcrypt hashing, HTTP-only cookies | High: Insecure CORS wildcard regex and missing Secure cookie flag by default. |
| **DF-02: OAuth Sign-In** | Browser & Google | API (`/auth/google/callback`) | Name, Email, Google Subject ID | Federated single sign-on | Indefinite | State parameter CSRF validation | Third-party international transfer to Google LLC. |
| **DF-03: Password Reset** | API | Google SMTP (`smtp.gmail.com`) | Name, Email, Reset Token URL | Password recovery | 5-minute token TTL | Single-use Redis token | High: Email logged in stdout; account enumeration on 404 response. |
| **DF-04: AI Planning** | API | Google Gemini / OpenAI | Table/column names, user custom instructions | Transformation plan formulation | Provider telemetry retention | TLS 1.3 | High: User custom instructions may contain free-text personal data. |
| **DF-05: AI Diagnosis** | API | Google Gemini / OpenAI | Raw DB error trace, table names | Failure root-cause explanation | Provider telemetry retention | TLS 1.3 | **Critical**: Database constraint violation errors leak customer row data to US AI servers. |
| **DF-06: AI Tracing** | API | LangSmith (`api.smith.langchain.com`) | Prompts, completions, metadata, trace timestamps | Operational debugging & cost tracking | Cloud SaaS retention | TLS 1.3, API Key | High: Prompts containing schema details and user instructions transmitted to US SaaS by default. |
| **DF-07: Static Assets** | Browser | Unpkg CDN / Spline | IP address, User Agent, Referrer | 3D visual background rendering | CDN log retention | TLS 1.3 | High: Loads before user consent under PECR Regulation 6. |

---

## 5. Cookies and Tracking Technologies Audit (PECR / UK GDPR)

### 5.1 Cookie Inventory

| Cookie Name | Provider / Domain | Purpose | Classification | Lifespan | Flags Observed | PECR Consent Required? |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| `access_token` | First-party (`api`) | Authentication JWT access token | Strictly Necessary | 15 Minutes | `HttpOnly=True`, `SameSite=lax`, `Secure=False` (default) | No (Exempt under PECR Reg 6(4)) |
| `refresh_token` | First-party (`api`) | Authentication JWT refresh token | Strictly Necessary | 7 Days | `HttpOnly=True`, `SameSite=lax`, `Secure=False` (default) | No (Exempt under PECR Reg 6(4)) |
| `oauth_state` | First-party (`api`) | Google OAuth CSRF state verification | Strictly Necessary | 10 Minutes | `HttpOnly=True`, `SameSite=lax`, `Secure=False` (default) | No (Exempt under PECR Reg 6(4)) |
| `logged_in` | First-party (`web`) | Client-side routing authentication indicator | Functional / UI | Session | Read via `document.cookie` / Next.js middleware | No (Exempt) |
| `active_org_id` | First-party (`web`) | Organization switcher context in Axios client | Functional / Preferences | Persistent | Client-side read/write via `js-cookie` | Yes (If not strictly necessary for basic service delivery) |

### 5.2 Third-Party Scripts & Trackers

1. **Unpkg CDN Script Injection**:
   - Location: `apps/web/components/landing/SplineHeroBackground.tsx:57-61`
   - URL: `https://unpkg.com/@splinetool/viewer@1.12.98/build/spline-viewer.js`
   - Behavior: Injected directly into the Next.js `<Script>` lifecycle with `strategy="afterInteractive"` on the home page and login/register wrappers.
   - PECR Risk: Transmits visitor IP addresses and user agents to an external CDN prior to user interaction or consent.
2. **Spline 3D Embed**:
   - Location: `apps/web/components/auth/AuthLayout.tsx:19`
   - URL: `https://my.spline.design/flow-vD4AAB4End71ev0QfMLT00qI/`
   - Behavior: Rendered inside a full-height `<iframe>` on `/login` and `/register`.
   - PECR Risk: External domain can set its own cookies, localStorage, or tracking beacons inside the iframe container without host consent.
3. **Analytics Tools Audit**:
   - Google Analytics (`gtag.js`, GTM): **Not found in codebase**.
   - Meta Pixel, LinkedIn Insight, Hotjar, Microsoft Clarity, Mixpanel, Amplitude, PostHog, Segment: **Not found in codebase**.
   - Sentry / Datadog SDKs: **Not found in frontend package.json**.

---

## 6. Cookie Consent & Notice Audit

Under PECR Regulation 6 and ICO guidance, any non-essential storage or access to information on a user's terminal equipment requires **prior, informed, granular, opt-in consent** before scripts execute.

### Identified Gaps:
1. **No Consent Banner**: There is no cookie consent banner, modal, or overlay implemented anywhere in `apps/web`.
2. **No Consent Storage**: There is no Redux state, localStorage key, or cookie recording user consent choices.
3. **No Script Blocking**: External scripts (`spline-viewer.js` and `my.spline.design`) load immediately upon route transition.
4. **Dead Legal Links**: The landing page footer (`apps/web/components/landing/Footer.tsx:96-102`) renders:
   ```tsx
   <a href="#" className="hover:text-sky-400 transition-colors">Privacy policy</a>
   <a href="#" className="hover:text-sky-400 transition-colors">Terms of service</a>
   ```
   These point to empty anchor tags (`#`), providing no cookie policy or data protection information.

---

## 7. Privacy Notice & Transparency Audit (UK GDPR Art. 13 & 14)

Under UK GDPR Article 13, data controllers must provide specific information to data subjects at the time personal data is collected.

| Data Collection Form | URL / Component | Data Collected | Privacy Notice Present? | Gaps Identified |
| :--- | :--- | :--- | :---: | :--- |
| **Registration Form** | `/register`<br>`RegisterForm.tsx` | Full Name, Email Address, Password | **NO** | No link to Privacy Policy, no legal entity identity, no statement of lawful basis, no notice of third-party processors (Google, AWS). |
| **Login Form** | `/login`<br>`LoginForm.tsx` | Email Address, Password | **NO** | No privacy notice or link to terms. |
| **Google Sign-In** | `GoogleAuthButton.tsx` | Google Account ID, Email, Name | **NO** | No disclosure that profile information is synced and linked to a local account. |
| **Password Reset** | `/forgot-password` | Email Address | **NO** | No notice that email will be processed through Google Gmail SMTP. |
| **Agent Registration** | `/agents/create` | Agent Name, Source Database Connection Strings | **Partial** | Displays architectural note: *"Your data never leaves your infrastructure"*, but fails to detail control-plane metadata retention. |

---

## 8. Lawful Basis Review

Under UK GDPR Article 6, every processing activity must have a documented lawful basis. The following table identifies current application processing activities and flags required business/legal determinations:

| Processing Activity | Personal Data Involved | Technical Evidence in Code | Possible Lawful Basis | Business / Legal Confirmation Required |
| :--- | :--- | :--- | :--- | :--- |
| **Account Creation & Authentication** | Name, email address, password hash, session cookies | `users_routes.py:81-134` | Contract (Art. 6(1)(b)) | `REQUIRES BUSINESS/LEGAL CONFIRMATION` — Confirm User Terms of Service govern platform account provision. |
| **Google Single Sign-On** | Name, email, Google subject ID | `users_routes.py:176-347` | Contract (Art. 6(1)(b)) or Legitimate Interests (Art. 6(1)(f)) | `REQUIRES BUSINESS/LEGAL CONFIRMATION` — Confirm Google OAuth terms and user account linking policy. |
| **Password Reset Delivery** | Email address, name, reset token | `email.py:61-85`, `users_routes.py:421-489` | Contract (Art. 6(1)(b)) or Legitimate Interests (Art. 6(1)(f)) | `REQUIRES BUSINESS/LEGAL CONFIRMATION` — Confirm use of Google SMTP as a transactional processor. |
| **AI Transformation Planning** | Schema names, column names, custom instructions | `migration_plans_llm.py:237-308` | Legitimate Interests (Art. 6(1)(f)) or Contract (Art. 6(1)(b)) | `REQUIRES BUSINESS/LEGAL CONFIRMATION` — Legitimate Interest Assessment (LIA) required for sending schema context to external AI providers. |
| **AI Failure Diagnosis** | Database error messages, constraint violations, table names | `execution_services.py:851-897` | Legitimate Interests (Art. 6(1)(f)) | `REQUIRES BUSINESS/LEGAL CONFIRMATION` — Review whether error trace forwarding requires user opt-in due to customer data exposure. |
| **AI Observability & Tracing** | Full prompts, model parameters, latency, cost metadata | `apps/api/app/core/config.py:7-8, 55-59` | Legitimate Interests (Art. 6(1)(f)) | `REQUIRES BUSINESS/LEGAL CONFIRMATION` — LIA required for LangSmith telemetry transfer to US servers. |
| **Third-Party 3D Visual Rendering** | IP address, browser user-agent | `SplineHeroBackground.tsx:57-61` | Consent (PECR Reg 6) | `REQUIRES BUSINESS/LEGAL CONFIRMATION` — Spline visuals are non-essential marketing/aesthetic elements requiring prior consent. |

---

## 9. User Rights Technical Assessment (UK GDPR Chapter III)

| Right | Technical Support in Code | Exact Code Location | Technical Gap Identified | Required Remediation Action |
| :--- | :---: | :--- | :--- | :--- |
| **Right of Access (Art. 15)** | **Partial** | `apps/api/app/modules/users/users_routes.py:536` (`GET /users/me`) | Endpoint returns basic user profile fields only. Does not aggregate all associated data (agents, migration plans, jobs, traces, activity history). | Implement comprehensive Data Access DTO compiling all user-linked records. |
| **Right to Rectification (Art. 16)** | **Partial** | `apps/api/app/modules/users/users_routes.py:546` (`PUT /users/me`) | Backend API supports updating name, email, and password. **However, no UI page exists in `apps/web`** for the user to edit their profile. | Build a `/settings` or `/profile` management page in the Next.js web application. |
| **Right to Erasure (Art. 17)** | **Partial** | `apps/api/app/modules/users/users_routes.py:561` (`DELETE /users/me`) | Backend executes `db.delete(user)` with database-level cascading deletion across agents and migration plans. **No UI button exists in `apps/web`**. Does not purge traces or Redis keys. | Add an Account Deletion modal in UI; purge Redis cache keys; implement soft-deletion or purge queue for backups. |
| **Right to Restriction (Art. 18)** | **No** | `apps/api/app/modules/users/users_models.py:32` (`is_active` boolean) | `is_active=False` exists in model, but no API endpoint or admin workflow allows a user to request restriction of processing while maintaining records. | Add an explicit account restriction workflow and administrative flag. |
| **Right to Data Portability (Art. 20)** | **None** | None | No endpoint exists to export personal data in a structured, commonly used, and machine-readable format (JSON/CSV). | Implement `GET /api/v1/users/me/export` returning complete JSON archive. |
| **Right to Object (Art. 21)** | **None** | None | No technical preference toggles exist to opt out of AI failure diagnosis, LangSmith tracing, or marketing communications. | Introduce privacy preference flags in User model and settings UI. |
| **Automated Decisions & Profiling (Art. 22)** | **Review Required** | `apps/api/app/modules/migration_plans/migration_plans_validator.py` | Automated schema validation and AI plan generation make mapping decisions, but human approval is required before execution (`destructive_approvals`). | Document human-in-the-loop safeguards in compliance documentation. |

---

## 10. Data Retention and Lifecycle Analysis

```text
Data Lifecycle Stage:
1. Collection   ──► Direct input via UI / Google OAuth / Database introspection
2. Processing   ──► Schema AST generation, ETL streaming via local Polars/DuckDB
3. Storage      ──► PostgreSQL tables, Redis cache, local DuckDB files in /tmp
4. Sharing      ──► Google Gemini / OpenAI (AI prompts), LangSmith (tracing), Google SMTP (emails)
5. Usage        ──► Platform migration execution, telemetry, and observability
6. Archiving    ──► WAL archiving & daily logical pg_dump backups (30-day retention documented)
7. Deletion     ──► Hard delete on DELETE /users/me; NO automated TTL or purge policies
```

### Identified Technical Lifecycle Gaps:
1. **Indefinite Control-Plane Retention**: No automated lifecycle policies or TTL mechanisms exist for `users`, `metadata_snapshots`, `migration_plans`, `migration_jobs`, `execution_traces`, or `llm_call_records`. Records remain in PostgreSQL forever unless manually deleted.
2. **Local DuckDB Staging Files**:
   - Location: `apps/agent/engine/orchestrator.py:67-83`
   - DuckDB staging databases are written to `/tmp/staging_{job_id}_{target_table}.duckdb`.
   - Cleanup only runs when a **new job** starts, scanning for files from *other* jobs (`if fname.startswith("staging_") and not fname.startswith(f"staging_{job_id}_")`).
   - If a migration crashes or the container is terminated, unencrypted customer database records remain on disk in `/tmp` indefinitely.
3. **Backup Retention vs Erasure Requests**: `docs/BACKUP_AND_DISASTER_RECOVERY.md:26` specifies daily physical backups with a 30-day retention window. If a user exercises their Right to Erasure, no technical procedure exists to prevent their personal data from being restored during a backup restoration.

---

## 11. Logging, Monitoring & Credential Leakage Audit

### 11.1 Strengths Identified:
- `CredentialSanitizer` (`apps/api/app/core/credential_sanitizer.py`) implements centralized masking for connection URIs, database passwords, and Bearer tokens.
- `StructuredLogger` (`apps/api/app/modules/observability/structured_logger.py`) redacts dictionary keys containing passwords, tokens, and URIs before serializing to JSON.

### 11.2 Critical Logging Gaps:
1. **Plaintext Email Logging**:
   - Location: `apps/api/app/core/email.py:54` & `email.py:57`
   - Code:
     ```python
     logger.info(f"Password reset email successfully sent to {to_email}")
     logger.error(f"Failed to send email to {to_email} via Google SMTP: {exc}")
     ```
   - Risk: Personal email addresses are written to standard output (`stdout`) in plaintext, where they are ingested by container logging drivers and cloud monitoring agents.
2. **Unsanitized Failure Traces Sent to AI Diagnostics**:
   - Location: `apps/api/app/modules/execution/execution_services.py:859-860`
   - Code:
     ```python
     llm_prompt = f"""...
     Raw Error Trace:
     {err_msg}
     ..."""
     ```
   - Risk: Database error messages often include raw row data (e.g. `psycopg2.errors.UniqueViolation: Key (email)=(sarah.connor@sky.net) already exists`). Passing raw `{err_msg}` into an external LLM transmits customer personal data to third-party AI APIs.

---

## 12. Authentication, Authorization & Security Architecture

### 12.1 Vulnerability: Permissive CORS Origin Regex Allowing Arbitrary Credentialed Origins
- **Location**: `apps/api/app/main.py:98-105`, `docker-compose.yml:43`, `.env.example:39`
- **Code Reference**:
  ```python
  if "*" in settings.CORS_ORIGINS:
      app.add_middleware(
          CORSMiddleware,
          allow_origin_regex=r"^https?://.*$",
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
      )
  ```
- **Observed Behavior**: Because `*` is present in the default environment variable template (`CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,*"`), FastAPI configures a regular expression (`^https?://.*$`) that matches **any HTTP or HTTPS domain on the entire internet**, paired with `allow_credentials=True`.
- **Security Impact**: Any malicious third-party site visited by a logged-in Migraflow user can issue background `fetch()` requests with credentials, reading full user profile data, metadata schemas, and agent tokens, completely bypassing the Same-Origin Policy.

### 12.2 Vulnerability: Broken Object Level Authorization (IDOR) on User Profile Endpoints
- **Location**: `apps/api/app/modules/users/users_routes.py:578-611`
- **Code Reference**:
  ```python
  @router.get("/users/{user_id}", response_model=UserResponse)
  async def get_user_by_id(user_id: uuid.UUID, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
      user = await UserService.get_user_by_id(db, user_id)
      ...
      return UserResponse.model_validate(user)

  @router.get("/users", response_model=List[UserResponse])
  async def list_users(skip: int = 0, limit: int = 50, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
      users = await UserService.list_users(db, skip=skip, limit=limit)
      return [UserResponse.model_validate(u) for u in users]
  ```
- **Observed Behavior**: Any standard authenticated user can retrieve the name, email address, UUID, and timestamps of **any other user** by UUID, or enumerate the entire user table via `GET /api/v1/users`. No role-based access control (RBAC) or ownership verification is implemented.

### 12.3 Vulnerability: Insecure Cookie Flags by Default
- **Location**: `apps/api/app/core/config.py:21`, `apps/api/app/modules/users/users_routes.py:55, 66`
- **Observed Behavior**: `COOKIE_SECURE: bool = False` is set in configuration. Unless explicitly overridden in production, authentication cookies are issued without the `Secure` flag, allowing transmission over unencrypted HTTP.

### 12.4 Vulnerability: Hardcoded Secrets in Source Control
- **Location**: `DATABASE_CREDENTIALS.md:19-24`, `docs/DATABASE_CREDENTIALS.md`, `docker-compose.yml:40, 47, 111, 136, 166`
- **Observed Behavior**: Plaintext database master passwords (`postgres_password`, `mysql_password`, `mongo_password`) and fallback secret keys (`default_jwt_secret_key_change_me_in_production`) are committed to Git. In the local developer environment, live API keys (Gemini, LangSmith, Gmail App Password) were discovered in `.env`.

---

## 13. Third-Party Processors & International Transfers

The following external entities process personal or metadata on behalf of the platform:

| Provider | Data Transmitted | Service Purpose | Evidence in Code | Location / Region | Transfer Safeguard Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Google LLC** (Gemini AI) | Database schema ASTs, table/column names, user custom instructions, DB failure error traces | AI transformation plan formulation & failure diagnosis | `apps/api/app/modules/migration_plans/migration_plans_engine/migration_plans_llm.py:336`, `execution_services.py:871` | United States | UK IDTA / Standard Contractual Clauses (SCCs) & Data Processing Addendum (DPA). |
| **OpenAI, LLC** | Same as above (alternative LLM provider) | Fallback AI plan generation & failure diagnosis | `migration_plans_llm.py:348`, `execution_services.py:879` | United States | UK IDTA / SCCs & DPA. |
| **LangChain, Inc.** (LangSmith) | Full LLM input prompts, schema descriptions, user instructions, completion payloads, execution latencies | AI observability, error tracing, and token cost tracking | `apps/api/app/core/config.py:7-8, 55-59`, `docker-compose.yml:49-56` | United States (`api.smith.langchain.com`) | UK IDTA / SCCs & DPA. (Tracing must be opt-in or strictly enterprise-governed). |
| **Google LLC** (Gmail SMTP) | User email address, user full name, password reset cryptographic tokens | Transactional password reset emails | `apps/api/app/core/email.py:43-55`, `users_routes.py:480` | United States / Global | Google Workspace DPA & UK International Transfer Agreement. |
| **Google LLC** (OAuth 2.0) | User IP, browser headers, Google ID token verification (sub, email, name) | Federated authentication (Single Sign-On) | `users_routes.py:140-347`, `GoogleAuthButton.tsx` | United States / Global | Google API Terms & User Consent. |
| **Spline, Inc.** | User IP address, user agent, browser viewport metadata | 3D interactive hero and auth background scenes | `SplineHeroBackground.tsx:11`, `AuthLayout.tsx:19` | United States | Vendor review, PECR consent gating, or self-hosting 3D assets. |
| **Cloudflare / Unpkg** | Visitor IP address, user agent, request headers | Delivery of `spline-viewer.js` web component runtime | `SplineHeroBackground.tsx:57` | Global CDN / United States | Self-host npm package in local bundle. |
| **Amazon Web Services (AWS)** | Entire containerized deployment stack, PostgreSQL database volume, application logs | Cloud application hosting (EC2) | `.github/workflows/deploy-ec2.yml:15-30` | `secrets.EC2_HOST` (Region unconfirmed in code) | AWS GDPR Data Processing Addendum. |

---

## 14. Children’s Privacy (AADC) & Special Category Data

1. **Age Verification & Children**:
   - The platform contains no date-of-birth collection, age gates, or age verification mechanisms.
   - While intended for B2B enterprise software engineers and database administrators, the registration form does not restrict registration to individuals aged 18 or older.
   - Under the UK Age Appropriate Design Code (AADC), if services are accessible to children, higher privacy standards apply. A clear age statement should be added to the Terms of Service.
2. **Special Category Data (UK GDPR Art. 9)**:
   - Core platform entities do not collect Article 9 data.
   - However, because Migraflow migrates arbitrary customer databases, customer source databases frequently contain special category data (e.g. healthcare, biometric, religious, or political data).
   - The platform’s reliance on third-party LLMs for failure diagnosis creates a critical risk that Article 9 data could be included in database error messages sent to external AI providers.

---

## 15. Conclusion & Audit Sign-Off

This audit reveals that while Migraflow has adopted a strong privacy-by-design baseline for its data-plane execution (keeping raw migration data on customer agents), the control-plane web application and backend API require substantial remediation before meeting the standards of UK GDPR, the Data Protection Act 2018, and PECR.

Immediate remediation must focus on eliminating the wildcard CORS regex, securing user profile endpoints against IDOR, removing committed credentials, gating external scripts behind a compliant cookie consent manager, and filtering error traces before sending them to external AI services.

For detailed finding specifications, consult `UK-GDPR-FINDINGS.md`.  
For data inventories and vendor flows, consult `UK-GDPR-DATA-INVENTORY.md` and `UK-GDPR-THIRD-PARTY-INVENTORY.md`.  
For step-by-step technical implementation instructions, consult `UK-GDPR-REMEDIATION-PLAN.md`.
