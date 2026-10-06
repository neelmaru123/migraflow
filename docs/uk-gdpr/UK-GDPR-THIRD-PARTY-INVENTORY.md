# UK GDPR Third-Party Data Processor & Service Inventory

> **LEGAL NOTICE**: This inventory documents third-party entities, sub-processors, and external API providers identified during code inspection of the Migraflow repository. Under UK GDPR Article 28, a formal written Data Processing Agreement (DPA) incorporating appropriate transfer safeguards (such as the UK International Data Transfer Agreement or Addendum) must be executed with every data processor.

---

## 1. Third-Party Processor Inventory Table

| Provider | Purpose of Processing | Data Shared / Received | Technical Evidence in Code | Location / Region | DPA Status / Transfer Mechanism | Risk Rating |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Google LLC**<br>(Google Cloud / Gemini API) | AI-driven transformation plan formulation, AST generation, and migration failure root-cause diagnosis. | Database schema names, table names, column names, constraints, foreign keys, user custom instructions, and raw database failure exception traces (`err_msg`). | `apps/api/app/modules/migration_plans/migration_plans_engine/migration_plans_llm.py:336-343`<br>`apps/api/app/modules/execution/execution_services.py:871-877` | United States / Global | `UNKNOWN - LEGAL/VENDOR REVIEW REQUIRED`<br>Requires Google Cloud DPA with UK IDTA / SCCs. | **HIGH**<br>(Failure traces may contain unredacted database row data) |
| **OpenAI, LLC**<br>(OpenAI API) | Alternative LLM provider for transformation planning and failure diagnosis when `LLM_PROVIDER="openai"`. | Same as Google Gemini above. | `apps/api/app/modules/migration_plans/migration_plans_engine/migration_plans_llm.py:348-350`<br>`apps/api/app/modules/execution/execution_services.py:879-886` | United States | `UNKNOWN - LEGAL/VENDOR REVIEW REQUIRED`<br>Requires OpenAI Business DPA with UK International Transfer Addendum. | **HIGH**<br>(Same error trace data leakage risk) |
| **LangChain, Inc.**<br>(LangSmith Observability) | External AI telemetry, tracing, token cost monitoring, and LLM prompt/response logging. | Complete LLM prompts, serialized schema trees, user instructions, completion payloads, execution latencies, and metadata. | `apps/api/app/core/config.py:7-8, 55-59`<br>`docker-compose.yml:49-56`<br>`.env:1-9` (`api.smith.langchain.com`) | United States | `UNKNOWN - LEGAL/VENDOR REVIEW REQUIRED`<br>Requires LangChain DPA; should be disabled by default under privacy by design. | **HIGH**<br>(Transmits operational prompts and metadata to US SaaS) |
| **Google LLC**<br>(Gmail SMTP Service) | Dispatching transactional password reset emails containing 5-minute cryptographic tokens. | Recipient email address, recipient full name, password reset URLs and tokens. | `apps/api/app/core/email.py:43-55`<br>`apps/api/app/modules/users/users_routes.py:480-485` | United States / Global (`smtp.gmail.com:587`) | `UNKNOWN - LEGAL/VENDOR REVIEW REQUIRED`<br>Google Workspace / Consumer Gmail terms. Dedicated enterprise transactional email provider recommended. | **MEDIUM**<br>(Logs emails in stdout; personal data transmitted to US) |
| **Google LLC**<br>(Google OAuth 2.0 / Identity) | User single sign-on authentication and profile verification. | Client authorization code, Google ID token verification claims (subject ID, email address, full name, email verified status), client IP address. | `apps/api/app/modules/users/users_routes.py:140-347`<br>`apps/web/components/auth/GoogleAuthButton.tsx:1-56` | United States / Global (`accounts.google.com`) | `UNKNOWN - LEGAL/VENDOR REVIEW REQUIRED`<br>Standard Google Identity Terms; covered by user consent/contract at sign-in. | **LOW / MEDIUM** |
| **Spline, Inc.** | Rendering interactive 3D WebGL scenes for hero and authentication page backgrounds. | Visitor IP address, browser user-agent, screen resolution, referrer URL. | `apps/web/components/landing/SplineHeroBackground.tsx:11`<br>`apps/web/components/auth/AuthLayout.tsx:19`<br>`apps/web/app/login/page.tsx:10` | United States (`my.spline.design`, `prod.spline.design`) | `UNKNOWN - LEGAL/VENDOR REVIEW REQUIRED`<br>PECR violation: loads prior to consent. Vendor DPA required if retained. | **HIGH**<br>(PECR non-compliance; external iframe on auth pages) |
| **Cloudflare, Inc. / Unpkg** | Public CDN delivery of `@splinetool/viewer` web component runtime script. | Visitor IP address, browser headers, requested script URL. | `apps/web/components/landing/SplineHeroBackground.tsx:57` (`unpkg.com/@splinetool/viewer`) | Global Edge CDN / United States | `UNKNOWN - INFRASTRUCTURE REVIEW REQUIRED`<br>Public unauthenticated CDN. Best practice: vendor script self-hosting. | **MEDIUM**<br>(External script injection without integrity hash or consent) |
| **Amazon Web Services (AWS)** | Cloud infrastructure hosting production Docker Compose services, PostgreSQL database, and Redis. | Entire application database (users, agents, plans, execution events), container logs, and system backups. | `.github/workflows/deploy-ec2.yml:15-30`<br>`docs/BACKUP_AND_DISASTER_RECOVERY.md:24` | AWS EC2 (Region unconfirmed in code; e.g. `us-east-1` or `eu-west-2`) | `UNKNOWN - INFRASTRUCTURE/LEGAL REVIEW REQUIRED`<br>Requires AWS GDPR Addendum; confirmation of AWS Region (UK `eu-west-2` vs US). | **HIGH**<br>(Core system of record hosting all personal data) |
| **Docker Inc. / GitHub Container Registry** | Public container image distribution for the on-premise Docker migration agent. | Compiled container image binaries (`data-migration-agent:latest`), public image pull IP logs. | `apps/api/app/core/config.py:30`<br>`docker-compose.yml:48`<br>`.github/workflows/publish-agent.yml:30-38` | United States / Global | Standard developer terms. (Contains no personal data; code artifact only). | **LOW** |

---

## 2. International Data Transfers Assessment (UK GDPR Chapter V)

Under UK GDPR Articles 44–49, transferring personal data outside the United Kingdom to a third country requires either:
1. An **Adequacy Decision** by the UK Government (Data Protection Act 2018), or
2. **Appropriate Safeguards** (such as the UK International Data Transfer Agreement (IDTA), the UK Addendum to the EU Standard Contractual Clauses (SCCs), or Binding Corporate Rules), or
3. An explicit **Derogation** under Article 49.

### Transfer Breakdown by Third Country:

```text
[United Kingdom (Application Users)]
       │
       ▼
[AWS Infrastructure Hosting]
       ├── If deployed in UK (eu-west-2 London) ──► Domestic Processing (No transfer)
       └── If deployed in US (us-east-1 / etc.)  ──► International Transfer (UK IDTA / SCCs Required)
       │
       ▼ Third-Party SaaS Integrations (All US-Based):
       ├── Google LLC (Gemini AI, OAuth, Gmail SMTP) ──► United States (UK IDTA / DPA Required)
       ├── OpenAI, LLC (Alternative LLM API)         ──► United States (UK IDTA / DPA Required)
       ├── LangChain, Inc. (LangSmith Tracing)        ──► United States (UK IDTA / DPA Required)
       ├── Spline, Inc. (3D WebGL / Embeds)          ──► United States (Vendor DPA Required)
       └── Cloudflare / Unpkg (Script Delivery)       ──► Global Edge (Self-hosting recommended)
```

### Action Items for Business & Legal Owners:
1. **AWS Region Confirmation**: Verify the physical AWS Region hosting the EC2 instance in `.github/workflows/deploy-ec2.yml`. If hosted in `eu-west-2` (London), data storage remains domestic. If hosted outside the UK, execute the AWS UK GDPR Addendum.
2. **AI Provider DPAs**: Formally execute DPAs with Google Cloud and OpenAI ensuring that customer prompt data is not used for model training and is covered by the UK Extension to the EU-US Data Privacy Framework or UK IDTA.
3. **LangSmith Governance**: Disable LangSmith tracing in production by default. If enabled for enterprise debugging, execute a formal DPA with LangChain Inc.
4. **Spline Script Elimination / Self-Hosting**: Replace the third-party Unpkg CDN script with a locally bundled npm package, and gate or remove third-party Spline iframes to avoid cross-border transfers on authentication screens.
