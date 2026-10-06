# UK GDPR / PECR Compliance Audit — Prioritized Findings

> **LEGAL NOTICE**: This findings register provides technical application security and privacy engineering analysis. It does NOT constitute legal confirmation of UK GDPR compliance. All suggested legal classifications require qualified legal review.

---

## Summary of Findings

| ID | Severity | Category | Title | Affected Files | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **GDPR-SEC-001** | **CRITICAL** | Security / Access Control | Wildcard CORS Origin Regex with Credentials Enabled | `apps/api/app/main.py:98-105`<br>`docker-compose.yml:43`<br>`.env.example:39` | Open |
| **GDPR-SEC-002** | **CRITICAL** | Access Control / IDOR | Broken Access Control & IDOR on User Endpoints (`/users`, `/users/{id}`) | `apps/api/app/modules/users/users_routes.py:578-611` | Open |
| **GDPR-SEC-003** | **CRITICAL** | Secrets Management | Committed Database Passwords, Fallback Secrets & Live API Keys | `DATABASE_CREDENTIALS.md:19-24`<br>`docs/DATABASE_CREDENTIALS.md`<br>`docker-compose.yml:40-47` | Open |
| **GDPR-TRK-001** | **HIGH** | Cookies / Tracking | Third-Party Scripts & Iframes Loaded Prior to User Consent | `apps/web/components/landing/SplineHeroBackground.tsx:57-61`<br>`apps/web/components/auth/AuthLayout.tsx:19`<br>`apps/web/app/login/page.tsx:10` | Open |
| **GDPR-CONS-001** | **HIGH** | Consent Management | Complete Absence of Cookie Consent Banner & Controls | `apps/web/app/layout.tsx:1-24`<br>`apps/web/components/landing/Footer.tsx:96-102` | Open |
| **GDPR-NOT-001** | **HIGH** | Transparency / Notice | Missing Privacy Notice at Personal Data Collection Points | `apps/web/components/auth/RegisterForm.tsx:1-175`<br>`apps/web/components/auth/LoginForm.tsx:1-143`<br>`apps/web/app/register/page.tsx` | Open |
| **GDPR-AI-001** | **HIGH** | AI Privacy / Data Transfer | Database Exception Traces Leaking Row Data to Third-Party AI & LangSmith | `apps/api/app/modules/execution/execution_services.py:859-860`<br>`apps/api/app/modules/migration_plans/migration_plans_engine/migration_plans_llm.py:305-307` | Open |
| **GDPR-SEC-004** | **HIGH** | Session Security | Sensitive JWT Tokens in URL Query Strings & LocalStorage Fallback | `apps/api/app/modules/agents/agents_routes.py:168-178`<br>`apps/web/components/agents/DockerCommandOutput.tsx:80` | Open |
| **GDPR-LOG-001** | **HIGH** | Logging / Telemetry | Plaintext User Email Addresses Logged in Application Console | `apps/api/app/core/email.py:54, 57` | Open |
| **GDPR-RIGHTS-001**| **MEDIUM** | User Rights | Missing Data Portability API & Lack of Profile/Erasure User Interface | `apps/api/app/modules/users/users_routes.py`<br>`apps/web/app/` | Open |
| **GDPR-SEC-005** | **MEDIUM** | Session Security | Insecure Default Cookie Flags (`COOKIE_SECURE=False`) Over Plain HTTP | `apps/api/app/core/config.py:21`<br>`apps/api/app/modules/users/users_routes.py:55, 66` | Open |
| **GDPR-SEC-006** | **MEDIUM** | Information Disclosure | Account Enumeration on Password Reset Endpoint | `apps/api/app/modules/users/users_routes.py:437-440` | Open |
| **GDPR-OBS-001** | **MEDIUM** | Access Control / Isolation | Missing Tenant Isolation in Observability Traces & LLM Call Logs | `apps/api/app/modules/observability/observability_routes.py:36-50, 67-83` | Open |
| **GDPR-RET-001** | **MEDIUM** | Data Lifecycle / Retention| Indefinite Personal Data Retention in Database & Lingering Staging Files | `apps/api/app/modules/users/users_models.py`<br>`apps/agent/engine/orchestrator.py:67-83` | Open |
| **GDPR-MIN-001** | **LOW** | Data Minimisation | Raw Customer Row Sampling (`sample_rows[:10]`) in File Loaders | `apps/api/app/modules/sources/sources_loaders/sources_loaders_csv.py:86`<br>`apps/api/app/modules/sources/sources_loaders/sources_loaders_excel.py:95-97` | Open |
| **GDPR-PWD-001** | **LOW** | Security / Passwords | Restrictive Password Maximum Length Limit (12 Characters) in Frontend | `apps/web/components/auth/RegisterForm.tsx:138-140` | Open |
| **GDPR-DOC-001** | **INFORMATIONAL**| Governance | Absence of Compliance Documentation in Repository (ROPA, DPIA, DPA) | Repository-wide | Open |

---

## Detailed Finding Reports

```text
Finding ID: GDPR-SEC-001

Severity: CRITICAL

Category:
Security / Access Control / UK GDPR Art. 5(1)(f) & Art. 32

Title:
Wildcard CORS origin regex with credentials enabled allows arbitrary cross-origin data theft

Evidence:
apps/api/app/main.py:98-105
docker-compose.yml:43
.env.example:39

Observed behavior:
The FastAPI application configures CORSMiddleware with:
if "*" in settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://.*$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
Because docker-compose.yml and .env.example set CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,*", the wildcard branch evaluates to true by default in production. This instructs FastAPI to dynamically mirror any requesting web origin (matching ^https?://.*$) and return Access-Control-Allow-Credentials: true.

Risk:
An attacker hosting an external malicious website (e.g. https://evil-attacker.com) can issue cross-origin fetch() requests with user credentials (cookies) to http://localhost:8000/api/v1 or the public API. Because credentials are permitted and the origin is matched, the attacker can silently extract the user's full profile, schema metadata, agent tokens, and execution blueprints, completely bypassing the browser's Same-Origin Policy.

Recommended action:
1. Immediately remove '*' from CORS_ORIGINS across docker-compose.yml, .env.example, and configuration files.
2. Completely remove the allow_origin_regex=r"^https?://.*$" branch in apps/api/app/main.py.
3. Explicitly validate that allow_credentials=True is ONLY paired with a strict whitelist of verified, explicit origin domains (e.g., [settings.FRONTEND_URL]).
4. Disallow any wildcard configurations when credentialed cookies are used.

Business/legal decision required:
Confirm the exact authorized production domains and staging hostnames allowed to access the API.
```

---

```text
Finding ID: GDPR-SEC-002

Severity: CRITICAL

Category:
Access Control / Insecure Direct Object Reference (IDOR) / UK GDPR Art. 5(1)(f) & Art. 32

Title:
Broken access control on user management endpoints allows unauthorized enumeration and profile harvesting

Evidence:
apps/api/app/modules/users/users_routes.py:578-611

Observed behavior:
The routes GET /api/v1/users/{user_id} and GET /api/v1/users are protected only by Depends(get_current_active_user).
1. Line 582-595: In GET /users/{user_id}, any authenticated user can pass an arbitrary user UUID and receive the user's full profile: name, email, account status, and registration timestamps.
2. Line 598-611: In GET /users, any authenticated user can fetch a paginated list of all users on the platform:
   users = await UserService.list_users(db, skip=skip, limit=limit)
   return [UserResponse.model_validate(u) for u in users]
There are no administrative role checks (RBAC) or tenant isolation checks.

Risk:
Any registered user (including a malicious actor who signs up for a free trial or account) can scrape the entire user database of names, email addresses, and account UUIDs, resulting in a personal data breach under UK GDPR Article 33/34 and facilitating spear-phishing or credential stuffing.

Recommended action:
1. Restrict GET /api/v1/users/{user_id} so that standard users can ONLY query their own user_id (user_id == current_user.id).
2. Remove or lock down GET /api/v1/users behind an explicit administrative role dependency (e.g. Depends(require_admin_user)).
3. Introduce an explicit role or is_superuser attribute on the User database model.

Business/legal decision required:
Define the organization's user role model and decide whether multi-tenant organizational isolation is required.
```

---

```text
Finding ID: GDPR-SEC-003

Severity: CRITICAL

Category:
Secrets Management / Credential Exposure / UK GDPR Art. 32

Title:
Committed database passwords, master credentials, and fallback secret keys in repository

Evidence:
DATABASE_CREDENTIALS.md:19-24
docs/DATABASE_CREDENTIALS.md:19-24
docker-compose.yml:40, 47, 111, 136, 166
apps/api/app/core/config.py:15-16

Observed behavior:
1. DATABASE_CREDENTIALS.md and docs/DATABASE_CREDENTIALS.md are tracked in the Git repository and contain master connection credentials, ports, usernames, and passwords for PostgreSQL (postgres:postgres_password), MySQL (root:mysql_password), and MongoDB (root:mongo_password).
2. docker-compose.yml defines hardcoded fallback secrets:
   JWT_SECRET_KEY=${JWT_SECRET_KEY:-default_jwt_secret_key_change_me_in_production}
   SECRET_KEY=${SECRET_KEY:-default_secret_key_change_me_in_production}
3. config.py has hardcoded fallback defaults for JWT_SECRET_KEY and SECRET_KEY.

Risk:
If containers are deployed without explicitly overriding environment variables, an attacker can use default secrets to forge valid JWT authentication tokens for any user_id, achieving complete platform administrative takeover and personal data exfiltration.

Recommended action:
1. Enforce strict configuration startup validation: in production (settings.ENVIRONMENT == "production"), fail fast and terminate application startup if JWT_SECRET_KEY or SECRET_KEY match default placeholder strings.
2. Remove DATABASE_CREDENTIALS.md from Git tracking and add it to .gitignore.
3. Rotate all database passwords and API keys.

Business/legal decision required:
Establish a formal secrets management policy (e.g. AWS Secrets Manager or HashiCorp Vault) for production deployments.
```

---

```text
Finding ID: GDPR-TRK-001

Severity: HIGH

Category:
Cookies / Tracking / PECR Regulation 6 & UK GDPR Art. 5(1)(a)

Title:
Third-party CDN scripts and interactive 3D iframes load prior to user consent

Evidence:
apps/web/components/landing/SplineHeroBackground.tsx:57-61, 67-73
apps/web/components/auth/AuthLayout.tsx:19-25
apps/web/app/login/page.tsx:10
apps/web/app/register/page.tsx:10

Observed behavior:
On the public home page (/), /login, and /register, the application automatically loads:
1. An external JavaScript script from a public third-party CDN:
   https://unpkg.com/@splinetool/viewer@1.12.98/build/spline-viewer.js
2. An embedded iframe pointing to:
   https://my.spline.design/flow-vD4AAB4End71ev0QfMLT00qI/
3. Remote assets from:
   https://prod.spline.design/E6eFCzHp4BkxYnO7/scene.splinecode
These requests execute immediately during page rendering, transmitting visitor IP addresses, browser fingerprints, and referrers to Unpkg (Cloudflare) and Spline (US-based company) without prior notice or consent.

Risk:
Violation of Regulation 6 of PECR and ICO guidance on third-party scripts. Non-essential third-party technologies are placed and accessed on user terminal equipment without prior consent.

Recommended action:
1. Bundle the @splinetool/viewer library locally via npm instead of loading scripts from unpkg.com.
2. For aesthetic 3D visual scenes, implement a local fallback visual by default and gate third-party 3D canvas connections behind the user consent management banner.

Business/legal decision required:
Confirm whether 3D visual scenes from Spline are deemed strictly necessary (unlikely under ICO guidance) or require consent under PECR.
```

---

```text
Finding ID: GDPR-CONS-001

Severity: HIGH

Category:
Consent Management / PECR Regulation 6 & UK GDPR Art. 7

Title:
Complete absence of cookie consent banner, category preferences, and consent withdrawal controls

Evidence:
apps/web/app/layout.tsx:1-24
apps/web/components/landing/Footer.tsx:96-102
apps/web/services/axios.ts:43

Observed behavior:
No cookie banner or consent management platform (CMP) is implemented. The footer links for "Privacy policy" and "Terms of service" are dead anchors (<a href="#">). The client-side application sets and reads cookies (logged_in, active_org_id) and localStorage items without recording user consent.

Risk:
Direct non-compliance with PECR and ICO cookie enforcement standards. Under UK law, organizations must provide clear information about all cookies and tracking mechanisms and obtain consent for all non-strictly-necessary technologies.

Recommended action:
1. Implement a lightweight Cookie Consent Banner component in apps/web.
2. Categorize cookies into "Strictly Necessary" (access_token, refresh_token, oauth_state) and "Functional / Preferences" (active_org_id).
3. Provide granular Accept / Reject / Manage Preferences options.
4. Persist consent timestamps and categories in a cookie or localStorage and provide a persistent "Cookie Settings" link in the footer to allow consent withdrawal at any time.

Business/legal decision required:
Approve the cookie inventory categorization and formal Cookie Policy text.
```

---

```text
Finding ID: GDPR-NOT-001

Severity: HIGH

Category:
Transparency / Privacy Notice / UK GDPR Art. 12 & 13

Title:
Complete absence of Privacy Notice at points of personal data collection

Evidence:
apps/web/components/auth/RegisterForm.tsx:1-175
apps/web/components/auth/LoginForm.tsx:1-143
apps/web/components/auth/GoogleAuthButton.tsx:1-56
apps/web/app/forgot-password/page.tsx

Observed behavior:
When users register an account, sign in, or initiate password recovery, personal data (name, email address, password, Google profile data) is collected without presenting a Privacy Notice, link to terms, or identification of the data controller.

Risk:
Violation of UK GDPR Article 13 (Information to be provided where personal data are collected from the data subject). Data subjects are not informed of who is processing their data, why it is being processed, how long it is retained, or what rights they have.

Recommended action:
1. Create a dedicated /privacy route hosting a comprehensive Privacy Notice.
2. Add a clear, accessible notice below the registration and login forms:
   "By registering, you acknowledge that your personal data will be processed in accordance with our [Privacy Notice](/privacy) and [Terms of Service](/terms)."
3. Display clear controller identity and DPO/privacy contact email.

Business/legal decision required:
Draft and approve the statutory UK GDPR Privacy Notice with legal counsel.
```

---

```text
Finding ID: GDPR-AI-001

Severity: HIGH

Category:
AI Privacy / International Data Transfers / UK GDPR Art. 5(1)(c), Art. 28, Art. 44-46

Title:
Raw database exception traces leaking customer row data into external AI prompts and LangSmith tracing

Evidence:
apps/api/app/modules/execution/execution_services.py:859-860
apps/api/app/modules/migration_plans/migration_plans_engine/migration_plans_llm.py:305-307
docker-compose.yml:49-56
apps/api/app/core/config.py:7-8, 55-59

Observed behavior:
1. In execution_services.py:859-860, during failure diagnosis, the raw error string ({err_msg}) is formatted directly into the LLM prompt without credential or PII sanitization:
   llm_prompt = f"... Raw Error Trace:\n{err_msg} ..."
   Database exception messages (e.g. unique constraint or foreign key violations) frequently echo unredacted row values (such as email addresses, phone numbers, or national identifiers).
2. User-provided custom instructions (custom_instructions) in migration_plans_llm.py are concatenated directly into the prompt sent to Google Gemini or OpenAI.
3. LangSmith tracing is active by default (LANGSMITH_TRACING=true, LANGCHAIN_TRACING_V2=true), sending all prompt strings and model responses to https://api.smith.langchain.com in the United States.

Risk:
Customer database records and personal data are transmitted to external third-party AI companies and cloud observability platforms without filtering, violating data minimisation (Art. 5(1)(c)), processor oversight (Art. 28), and international transfer restrictions (Chapter V).

Recommended action:
1. Apply CredentialSanitizer.mask_credentials() and regex-based PII masking to {err_msg} before inserting it into LLM diagnosis prompts.
2. Sanitize user custom instructions to strip out raw database connection URIs and credentials.
3. Configure LangSmith tracing to be disabled by default (LANGCHAIN_TRACING_V2=false, LANGSMITH_TRACING=false) unless explicitly enabled in dedicated enterprise environments with executed DPAs.

Business/legal decision required:
Execute formal Data Processing Agreements (DPAs) with Google Cloud, OpenAI, and LangChain Inc., incorporating the UK International Data Transfer Agreement (IDTA) or Addendum.
```

---

```text
Finding ID: GDPR-SEC-004

Severity: HIGH

Category:
Session Security / Token Exposure / UK GDPR Art. 32

Title:
Sensitive JWT authentication tokens accepted in WebSocket query parameters and fallback reading from LocalStorage

Evidence:
apps/api/app/modules/agents/agents_routes.py:168-178
apps/web/components/agents/DockerCommandOutput.tsx:80
apps/web/components/agents/AgentStatusBanner.tsx:44

Observed behavior:
1. The WebSocket endpoint /agents/ws/{agent_id} accepts authentication tokens in URL query strings:
   @router.websocket("/ws/{agent_id}")
   async def agent_websocket_endpoint(websocket: WebSocket, agent_id: uuid.UUID, token: Optional[str] = Query(None)...)
2. In frontend components (DockerCommandOutput.tsx:80 and AgentStatusBanner.tsx:44), the code attempts to read user session tokens from localStorage:
   const token = agent.api_token || localStorage.getItem('access_token');

Risk:
Tokens passed via URL query strings are captured in web server access logs, load balancer logs, browser history, and HTTP Referer headers. Furthermore, attempting to use user JWTs as agent tokens confuses identity boundaries and encourages storing sensitive JWTs in localStorage (vulnerable to XSS).

Recommended action:
1. Disallow passing JWT tokens in WebSocket URL query parameters. Rely strictly on the established first-frame JSON auth message: { "type": "auth", "token": "<jwt>" } or cookie headers.
2. Remove all localStorage.getItem('access_token') fallback calls in frontend agent components. Agent tokens and user JWTs must remain strictly segregated.

Business/legal decision required:
None (technical security fix).
```

---

```text
Finding ID: GDPR-LOG-001

Severity: HIGH

Category:
Logging & Monitoring / UK GDPR Art. 5(1)(f) & Art. 32

Title:
Plaintext user email addresses logged to standard output during password reset requests

Evidence:
apps/api/app/core/email.py:54, 57

Observed behavior:
When sending transactional emails, the application logs:
logger.info(f"Password reset email successfully sent to {to_email}")
logger.error(f"Failed to send email to {to_email} via Google SMTP: {exc}")

Risk:
User email addresses are written to container stdout logs in plaintext. These logs are stored unencrypted in Docker log files and cloud log aggregators (e.g. AWS CloudWatch), where they may be retained indefinitely and accessed by personnel without authorization to view customer personal data.

Recommended action:
Mask the email address before logging (e.g., j***e@domain.co.uk) or log only the associated user_id or a hashed identifier.

Business/legal decision required:
Establish a logging retention and minimization policy.
```

---

```text
Finding ID: GDPR-RIGHTS-001

Severity: MEDIUM

Category:
Data Subject Rights / UK GDPR Art. 15, 16, 17, 20

Title:
Missing technical mechanism for Data Portability and lack of user interface for Rectification and Erasure

Evidence:
apps/api/app/modules/users/users_routes.py:536-575
apps/web/app/
apps/web/components/

Observed behavior:
1. No API endpoint or UI mechanism exists to export user personal data in a structured, machine-readable format (JSON/CSV) under Article 20.
2. Although the backend exposes PUT /users/me (rectification) and DELETE /users/me (erasure), the Next.js web application provides NO settings page, profile management screen, or account deletion button. Users cannot exercise these rights directly within the application.

Risk:
Inability to satisfy data subject requests within statutory time limits (one month under UK GDPR Art. 12(3)), leading to potential ICO complaints or enforcement action.

Recommended action:
1. Implement a dedicated GET /api/v1/users/me/export endpoint returning an aggregated JSON archive of the user's profile, registered agents, data sources, migration plans, and job history.
2. Build an Account Settings page (/settings) in apps/web allowing users to update their profile and request self-service account deletion.

Business/legal decision required:
Approve the Data Subject Request (DSR) operational handling procedure and standard response timelines.
```

---

```text
Finding ID: GDPR-SEC-005

Severity: MEDIUM

Category:
Session Security / UK GDPR Art. 32

Title:
Insecure default cookie configuration (COOKIE_SECURE=False) allows transmission over plain HTTP

Evidence:
apps/api/app/core/config.py:21
apps/api/app/modules/users/users_routes.py:55, 66

Observed behavior:
In Settings (config.py:21), COOKIE_SECURE is set to False by default:
COOKIE_SECURE: bool = False
When _set_auth_cookies() writes access_token and refresh_token cookies, the Secure attribute is omitted unless the administrator manually configures COOKIE_SECURE=True in environment variables.

Risk:
If deployed over HTTP or behind a reverse proxy that misforwards headers, authentication cookies will be transmitted in cleartext, exposing session tokens to interception via Man-in-the-Middle (MitM) network attacks.

Recommended action:
Change the default in config.py so that COOKIE_SECURE automatically evaluates to True unless settings.ENVIRONMENT.lower() in ("development", "test", "local").

Business/legal decision required:
Ensure SSL/TLS certificates (HTTPS) are provisioned on all public-facing endpoints.
```

---

```text
Finding ID: GDPR-SEC-006

Severity: MEDIUM

Category:
Information Disclosure / Privacy / UK GDPR Art. 32

Title:
Account enumeration vulnerability via differing password reset error responses

Evidence:
apps/api/app/modules/users/users_routes.py:437-440, 444-447

Observed behavior:
In POST /api/v1/auth/forgot-password:
user = await UserService.get_user_by_email(db, payload.email)
if not user:
    raise HTTPException(status_code=404, detail="No account found with this email address. Please check your email or register.")
if user.google_id and not user.password_hash:
    raise HTTPException(status_code=400, detail="This account was created using Google Sign-In. Please sign in with Google.")

Risk:
An external attacker can probe the endpoint with arbitrary email addresses and determine with certainty whether an individual is a registered customer of the platform, facilitating targeted phishing and reconnaissance.

Recommended action:
Normalize responses to return an identical generic HTTP 200 response regardless of whether the email exists:
"If an account associated with this email exists, a password reset link has been dispatched."

Business/legal decision required:
Accept user experience change on password reset form.
```

---

```text
Finding ID: GDPR-OBS-001

Severity: MEDIUM

Category:
Access Control / Tenant Isolation / UK GDPR Art. 5(1)(f) & Art. 32

Title:
Missing tenant isolation and user filtering in observability traces and LLM call logs

Evidence:
apps/api/app/modules/observability/observability_routes.py:36-50, 67-83

Observed behavior:
1. In GET /observability/traces:
   stmt = select(ExecutionTrace).order_by(ExecutionTrace.started_at.desc()).limit(limit)
   if job_id:
       stmt = stmt.where(ExecutionTrace.migration_job_id == job_id)
   res = await session.execute(stmt)
   return list(res.scalars().all())
2. In GET /observability/llm-calls:
   stmt = select(LLMCallRecord).order_by(LLMCallRecord.request_timestamp.desc()).limit(limit)
   ...
Neither endpoint validates that the queried traces or LLM call records belong to migration jobs owned by current_user.id.

Risk:
Any authenticated user can inspect execution traces, error messages, and LLM call metadata generated by other platform customers.

Recommended action:
Join ExecutionTrace and LLMCallRecord against MigrationJob -> MigrationPlan -> User and filter strictly by MigrationPlan.user_id == current_user.id, or restrict endpoints to administrative roles.

Business/legal decision required:
Confirm whether observability endpoints are customer-facing features or internal admin-only diagnostic tools.
```

---

```text
Finding ID: GDPR-RET-001

Severity: MEDIUM

Category:
Data Retention & Deletion / UK GDPR Art. 5(1)(e) (Storage Limitation)

Title:
Indefinite personal data retention across control-plane database and unpurged staging files on local agents

Evidence:
apps/api/app/modules/users/users_models.py
apps/api/app/modules/metadata/metadata_models.py
apps/agent/engine/orchestrator.py:67-83

Observed behavior:
1. No TTL or scheduled retention cleanup jobs exist for user accounts, metadata schemas, execution logs, traces, or audit events.
2. In apps/agent/engine/orchestrator.py:67-83, DuckDB staging files (/tmp/staging_{job_id}_{target_table}.duckdb) are only purged when a subsequent migration job runs. If a job fails or the agent is decommissioned, customer records remain on disk in /tmp indefinitely.

Risk:
Violation of UK GDPR Article 5(1)(e) (personal data kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the personal data are processed).

Recommended action:
1. Implement an automated background retention purge task in the backend API to clean up historical traces, completed jobs, and snapshots older than a defined retention threshold (e.g. 90 days).
2. Enhance agent orchestrator to add a finally block ensuring local /tmp/staging_*.duckdb files are deleted immediately upon job completion or termination.

Business/legal decision required:
Define and legally approve the data retention schedule for migration execution records and audit traces.
```

---

```text
Finding ID: GDPR-MIN-001

Severity: LOW

Category:
Data Minimisation / UK GDPR Art. 5(1)(c)

Title:
Raw customer data row sampling in CSV and Excel file loaders

Evidence:
apps/api/app/modules/sources/sources_loaders/sources_loaders_csv.py:86
apps/api/app/modules/sources/sources_loaders/sources_loaders_excel.py:95-97
apps/api/app/modules/metadata/metadata_models.py:172

Observed behavior:
CSVFileLoader and ExcelFileLoader extract and store the top 10 rows of real data:
sample_rows = df_sample.to_dicts()
return FileSchemaMetadata(... sample_rows=sample_rows[:10])
The database model MetadataColumn also reserves a JSONB column sample_values.

Risk:
Storing actual row data in schema catalog tables conflicts with the platform's core architectural claim ("metadata only, never your data") and risks collecting unnecessary personal data.

Recommended action:
Remove sample_rows extraction or replace it with synthetic type representation / masked previews unless explicitly requested by the user.

Business/legal decision required:
Confirm whether sample value inspection is an essential business feature or if column metadata (data type, nullable, precision) is sufficient.
```

---

```text
Finding ID: GDPR-PWD-001

Severity: LOW

Category:
Security / Password Policy / UK GDPR Art. 32

Title:
Restrictive 12-character maximum password limit in frontend registration

Evidence:
apps/web/components/auth/RegisterForm.tsx:138-140

Observed behavior:
In RegisterForm.tsx, the password input validation restricts passwords to a maximum of 12 characters:
maxLength: { value: 12, message: 'Password must not exceed 12 characters' }

Risk:
Enforcing a 12-character maximum prevents users from using secure, high-entropy passphrases, conflicting with NCSC (UK National Cyber Security Centre) and OWASP password security guidelines.

Recommended action:
Increase the maximum password length to at least 128 characters (or remove the client-side upper constraint, leaving reasonable limits like 255 on backend).

Business/legal decision required:
None (technical usability and security fix).
```

---

```text
Finding ID: GDPR-DOC-001

Severity: INFORMATIONAL

Category:
Compliance Documentation & Governance / UK GDPR Art. 28, 30, 35

Title:
Absence of statutory compliance documentation in source repository

Evidence:
Repository-wide file search (no ROPA, DPIA, or DPA templates found)

Observed behavior:
No Records of Processing Activities (ROPA, Art. 30), Data Protection Impact Assessments (DPIA, Art. 35), or processor agreement templates were discovered within documentation directories.

Risk:
Demonstrating accountability under UK GDPR Article 5(2) requires maintaining appropriate internal documentation of processing activities and risk assessments.

Recommended action:
Create a compliance documentation pack in docs/compliance/ containing ROPA, DPIA, Vendor DPA registry, and Data Subject Request standard operating procedures.

Business/legal decision required:
Legal and compliance teams must produce and approve organizational accountability documents.
```
