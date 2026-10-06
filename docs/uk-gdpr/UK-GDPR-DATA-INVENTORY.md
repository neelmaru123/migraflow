# UK GDPR Personal Data Inventory (RoPA Data Map)

> **LEGAL NOTICE**: This personal data inventory reflects technical discovery across application source code, database models, API payloads, and logging outputs. It is intended to assist in preparing a formal Record of Processing Activities (RoPA) under Article 30 of the UK GDPR. Final legal verification of categories and lawful bases is required.

---

## 1. Personal Data Inventory Table

| Data Type | Collected? | Source / Location in Code | Purpose | Storage Location | Third-Party Sharing | Retention Period | Technical Privacy Risk |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **User Full Name** | Yes | `apps/web/components/auth/RegisterForm.tsx`<br>`apps/api/app/modules/users/users_models.py:31` | User identification, communication, and greeting | PostgreSQL (`users.name`) | Google SMTP (included in password reset emails) | Indefinite (until account deletion) | Medium: Exposed via `GET /users` IDOR vulnerability. |
| **User Email Address** | Yes | `apps/web/components/auth/RegisterForm.tsx`<br>`apps/web/components/auth/LoginForm.tsx`<br>`apps/api/app/modules/users/users_models.py:24` | Primary account identity, login authentication, password reset | PostgreSQL (`users.email` unique index) | Google SMTP (`smtp.gmail.com`), Google OAuth (`oauth2.googleapis.com`) | Indefinite (until account deletion) | High: Logged in plaintext in `email.py`; exposed via `GET /users` enumeration; account enumeration on reset. |
| **Password Hashes** | Yes | `apps/api/app/core/security.py:12-18`<br>`apps/api/app/modules/users/users_models.py:27` | Credential verification for standard password authentication | PostgreSQL (`users.password_hash` as Bcrypt string) | None (Never shared) | Indefinite (updated on password change) | Medium: Secure Bcrypt hash; frontend registration artificially caps input at 12 characters. |
| **Google Subject ID (`google_id`)** | Yes (OAuth users) | `apps/api/app/modules/users/users_routes.py:251`<br>`apps/api/app/modules/users/users_models.py:28` | Federated single sign-on mapping | PostgreSQL (`users.google_id` unique index) | Google LLC | Indefinite (until account deletion) | Low: Pseudonymous external identifier. |
| **Authentication JWT Tokens** | Yes | `apps/api/app/core/security.py:27-65`<br>`apps/api/app/modules/users/users_routes.py:47-69` | Stateless session authorization (Access: 15m, Refresh: 7d) | Client-side HTTP Cookies (`access_token`, `refresh_token`), in-flight HTTP headers | None | Access: 15 minutes<br>Refresh: 7 days | High: Transmitted over plain HTTP if `COOKIE_SECURE=False`; accepted in WebSocket URL query string. |
| **Password Reset Cryptographic Tokens** | Yes | `apps/api/app/modules/users/users_routes.py:464`<br>`apps/api/app/core/redis_client.py` | Secure single-use password recovery verification | Redis (`reset_token:<token>` key with value `{"user_id": ..., "email": ...}`) | Google SMTP (embedded in reset URL) | 5 Minutes (automatic Redis TTL expiry) | Low: Strong entropy (`secrets.token_urlsafe(32)`), single-use invalidation upon reset. |
| **Agent API Tokens & Hashes** | Yes | `apps/api/app/modules/agents/agents_models.py:41`<br>`apps/agent/main.py` | Daemon authentication for on-premise Docker agents | PostgreSQL (`agents.api_token_hash` as SHA-256) | Client web console (displayed once during creation) | Indefinite (until revoked or agent deleted) | High: Frontend attempts fallback substitution using user JWT from `localStorage`. |
| **Database Connection Credentials (Customer)** | User-Provided | `DATABASE_CREDENTIALS.md`<br>`apps/api/app/modules/agents/agents_command_generator.py`<br>`apps/agent/engine/db.py` | Establishing database connectivity for schema scanning and ETL streaming | Process environment variables on customer machine; `.env` templates | None during runtime (agent connects directly to customer DB) | Stored locally in customer Docker container `.env` | Critical: Plaintext master database passwords committed to Git repository files. |
| **Database Schema Metadata** | Yes | `apps/agent/metadata_engine.py`<br>`apps/api/app/modules/metadata/metadata_models.py` | Generating AI migration plans, data type mapping, constraint resolution | PostgreSQL (`metadata_snapshots`, `metadata_schemas`, `metadata_tables`, `metadata_columns`) | Google Gemini, OpenAI, LangSmith (Prompts contain schema ASTs) | Indefinite (retained across plan versions) | Medium: May disclose proprietary business logic or sensitive entities (e.g. `patient_diagnosis`). |
| **Raw Sample Rows** | Yes (CSV / Excel files) | `apps/api/app/modules/sources/sources_loaders/sources_loaders_csv.py:86`<br>`sources_loaders_excel.py:95-97` | Preliminary schema type inference for flat file loaders | In-memory and PostgreSQL (`metadata_columns.sample_values`) | None | Indefinite | Low/Medium: Violates data minimisation by capturing real row payloads into catalog storage. |
| **Migration Failure Error Traces** | Yes | `apps/api/app/modules/execution/execution_services.py:859-860`<br>`apps/api/app/modules/execution/execution_models.py` | Failure diagnostics and automated remediation suggestions | PostgreSQL (`migration_jobs.error_message`), `ExecutionTrace.error_message` | Forwarded to Google Gemini / OpenAI and LangSmith | Indefinite | **Critical**: Database constraint violation exceptions echo unredacted row data (emails, names, keys). |
| **User Custom AI Instructions** | Yes (Optional) | `apps/api/app/modules/migration_plans/migration_plans_engine/migration_plans_llm.py:305-307` | Customizing transformation logic and business mapping rules | PostgreSQL (`migration_plans.custom_instructions`) | Google Gemini / OpenAI, LangSmith | Indefinite | Medium: Free-text field; users may inadvertently paste sensitive personal or confidential data. |
| **IP Addresses & User Agents** | Yes | Web server reverse proxy headers, CDN requests, Spline requests | Network routing, connection establishment, and security logging | Server access logs, Docker logs, Unpkg / Spline CDN access logs | Cloudflare (Unpkg), Spline, AWS EC2 | Default server log retention (indefinite if unmanaged) | Medium: Transmitted to external CDNs prior to user consent. |
| **Customer Operational Row Data** | Streamed Locally | `apps/agent/main.py`<br>`apps/agent/engine/staging/duckdb_staging.py` | In-memory ETL transformation and streaming from source to target DB | Customer local memory buffers and temporary DuckDB staging files (`/tmp/staging_*.duckdb`) | None (Transferred directly between customer databases) | Transient (during job); but unpurged staging files linger if job crashes | Medium: Unencrypted disk staging in `/tmp` without guaranteed immediate cleanup on crash. |
| **Special Category Data (UK GDPR Art. 9)** | Not Intentionally Collected | Customer source databases streamed locally | High-risk customer migration data (medical, biometric, political, etc.) | Customer local databases; transient agent memory buffers | None intended; but exposed if constraint violation error messages echo raw data to AI | Transient | High/Critical: If customer migrates sensitive databases, error traces may leak Article 9 records. |
| **Children’s Personal Data** | Not Intentionally Collected | Registration and login forms | Account creation | PostgreSQL (`users` table) | None | Indefinite | Low: Enterprise B2B tool, but no age verification gate exists on public registration. |

---

## 2. Personal Data Storage Locations Summary

```text
1. Control-Plane PostgreSQL Database (Port 5434 / 5432)
   ├── Table: users (name, email, password_hash, google_id, is_active, timestamps)
   ├── Table: agents (user_id, name, agent_identifier, api_token_hash, status, last_error)
   ├── Table: metadata_* (database_name, table_name, column_name, data_type, sample_values)
   ├── Table: migration_plans (user_id, agent_id, plan_data AST, custom_instructions)
   ├── Table: migration_jobs (migration_plan_id, status, error_message, row_counts)
   └── Table: execution_traces & llm_call_records (trace_id, operation_type, error_message, metadata_snapshot)

2. In-Memory Task Queue & Cache (Redis: Port 6379)
   ├── Key: reset_token:<token> (user_id, email, 5-minute TTL)
   ├── Key: rate_limit:reset:<email> (60-second cooldown lock)
   └── Key: active_execution_lock:<plan_id> (job concurrency lock)

3. Client-Side Browser Storage
   ├── Cookie: access_token (HTTP-only, 15m expiry, Lax)
   ├── Cookie: refresh_token (HTTP-only, 7d expiry, Lax)
   ├── Cookie: oauth_state (HTTP-only, 10m expiry, Lax)
   ├── Cookie: active_org_id (Client-accessible, persistent)
   └── LocalStorage: access_token (Intermittently read by agent UI components)

4. Customer On-Premise Agent Filesystem
   ├── Environment File: .env (local DB connection strings and passwords)
   └── Temporary Staging: /tmp/staging_{job_id}_{table}.duckdb (intermediate ETL tables)
```

---

## 3. Data Sensitivity Classification Summary

- **Tier 1 — High Sensitivity / Direct Identifiers**: User full names, email addresses, password reset tokens, raw error traces containing constraint records.
- **Tier 2 — High Sensitivity / Authentication Secrets**: Bcrypt password hashes, active JWT access & refresh tokens, SHA-256 agent token hashes, committed database root passwords.
- **Tier 3 — Medium Sensitivity / Metadata**: Database schema catalogs, table names, column definitions, custom AI instructions, IP addresses, user agents.
- **Tier 4 — Ephemeral / Processing Payload**: Customer operational rows streamed locally through agent memory buffers and DuckDB staging files.
