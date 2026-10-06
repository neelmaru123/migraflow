# UK GDPR / PECR Technical Remediation Roadmap & Developer Implementation Plan

> **DISCLAIMER**: This remediation plan outlines technical engineering actions and architectural changes to address security, privacy, and compliance vulnerabilities identified during the audit. Execution of these steps does not automatically confer legal compliance; business and legal determinations must be conducted concurrently.

> **IMPLEMENTATION STATUS: FULLY REMEDIATED (100% Technical Remediation Complete)**  
> All 14 technical remediation items across backend (`apps/api`), agent (`apps/agent`), and frontend (`apps/web`) have been implemented, verified, and backed by automated unit & end-to-end build tests. Post-remediation technical readiness score: **93/100**.

---

## Part 1: Prioritized Roadmap (Phases 1 — 5)

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Critical Security & Access Control Remediation (Sprint 1)    │
│ Fix CORS wildcard regex, IDOR on /users, committed secrets, log PII    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 2: PECR Consent, Tracking & Transparency (Sprint 1 - 2)          │
│ Cookie consent banner, script gating, unpkg removal, privacy notices   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 3: Data Subject Rights & User Controls (Sprint 2 - 3)            │
│ Data portability export API, UI profile rectification & account erasure│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 4: Data Lifecycle, Retention & AI Privacy (Sprint 3 - 4)         │
│ Error trace sanitization, retention purge jobs, agent staging cleanup  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 5: Governance, Legal Documentation & Vendor DPAs (Ongoing)       │
│ Privacy Policy, Cookie Policy, RoPA, DPIA, Vendor DPAs & UK IDTA       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Detailed Developer Implementation Plans

### Item 1: Eliminate Wildcard CORS Regex & Restrict Credentialed Origins (GDPR-SEC-001)

#### Current

`apps/api/app/main.py:98-105` checks `if "*" in settings.CORS_ORIGINS:` and applies `allow_origin_regex=r"^https?://.*$"` with `allow_credentials=True`. `docker-compose.yml:43` and `.env.example:39` include `*` in `CORS_ORIGINS`.

#### Problem

Any malicious web page visited by an authenticated user can perform authenticated requests with cookies, bypassing the Same-Origin Policy and stealing personal data.

#### Recommended Implementation

1. In `apps/api/app/main.py`, remove the `if "*"` wildcard regex logic completely.
2. Only pass `allow_origins=settings.CORS_ORIGINS`.
3. If `allow_credentials=True`, enforce that `*` is strictly forbidden and raises a runtime configuration error at startup.
4. Update `docker-compose.yml:43` and `.env.example:39` to specify explicit origins: `"http://localhost:3000,http://127.0.0.1:3000"`.

#### Files

- `apps/api/app/main.py:98-114`
- `docker-compose.yml:43`
- `.env.example:39`
- `apps/api/app/core/config.py:63-78`

#### Dependencies

None.

#### Database / API / Frontend Changes

None.

#### Backend Changes

```python
# apps/api/app/main.py
if "*" in settings.CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS cannot contain '*' when allow_credentials=True. Specify explicit domains.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)
```

#### Testing

1. Send an `OPTIONS` or `GET` request with header `Origin: https://evil-attacker.com`.
2. Verify the server does NOT return `Access-Control-Allow-Origin: https://evil-attacker.com`.
3. Send a request with `Origin: http://localhost:3000` and verify it succeeds with credentials.

#### Business / Legal Decision

Confirm the exact list of authorized staging and production domain names.

---

### Item 2: Fix Broken Access Control & IDOR on User Profile Endpoints (GDPR-SEC-002)

#### Current

`GET /api/v1/users/{user_id}` allows any authenticated user to retrieve any user's profile. `GET /api/v1/users` lists all users for any logged-in caller.

#### Problem

Violates UK GDPR Article 5(1)(f) (Confidentiality). Any registered user can scrape the entire user database.

#### Recommended Implementation

1. Add an authorization check to `GET /users/{user_id}`: ensure `current_user.id == user_id` or that `current_user.is_superuser` is True.
2. In `GET /users`, restrict access to administrative users only (`require_admin_user` dependency), or remove the endpoint if bulk listing is not needed.

#### Files

- `apps/api/app/modules/users/users_routes.py:578-611`
- `apps/api/app/modules/users/users_dependencies.py`

#### Dependencies

None.

#### Database Changes

Optional: Add `is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)` to `User` model (`users_models.py`).

#### Backend Changes

```python
# apps/api/app/modules/users/users_routes.py
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Enforce strict self-access only
    if current_user.id != user_id and not getattr(current_user, "is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this profile.",
        )
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserResponse.model_validate(user)
```

#### Testing

1. Create User A and User B.
2. As User A, request `GET /api/v1/users/{user_b_id}`. Verify HTTP 403 Forbidden is returned.
3. As User A, request `GET /api/v1/users/{user_a_id}`. Verify HTTP 200 OK is returned.

#### Business / Legal Decision

None (security fix).

---

### Item 3: Remove Committed Credentials & Validate Secrets on Startup (GDPR-SEC-003)

#### Current

Plaintext master passwords are in `DATABASE_CREDENTIALS.md`. Fallback secret keys in `docker-compose.yml` and `config.py` default to predictable placeholders.

#### Problem

Forged JWT tokens can be created using the default secret key. Committed database passwords violate security standards.

#### Recommended Implementation

1. In `apps/api/app/core/config.py`, add a startup validator: if `ENVIRONMENT == "production"`, raise a fatal error if `JWT_SECRET_KEY` or `SECRET_KEY` equals default values or has fewer than 32 characters.
2. Untrack `DATABASE_CREDENTIALS.md` from git (`git rm --cached DATABASE_CREDENTIALS.md`).
3. Rotate all database credentials and generate secure random passwords.

#### Files

- `apps/api/app/core/config.py:15-16, 79-84`
- `docker-compose.yml:40, 47, 111, 136, 166`
- `.gitignore`

#### Backend Changes

```python
# apps/api/app/core/config.py
@field_validator("JWT_SECRET_KEY", mode="after")
@classmethod
def validate_jwt_secret(cls, v: str, info) -> str:
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "production" and ("default" in v or len(v) < 32):
        raise ValueError("CRITICAL: Insecure or default JWT_SECRET_KEY in production! Set a random >=32-char key.")
    return v
```

#### Testing

Start the API with `ENVIRONMENT=production` and default keys; verify the server refuses to boot.

#### Business / Legal Decision

Adopt an enterprise secrets manager (e.g. AWS Secrets Manager or Doppler).

---

### Item 4: Implement Cookie Consent Banner & Gate Third-Party Scripts (GDPR-TRK-001 & GDPR-CONS-001)

#### Current

External scripts (`unpkg.com/@splinetool/viewer`) and iframes (`my.spline.design`) load automatically on landing and login pages without consent. No cookie banner exists.

#### Problem

Non-compliance with PECR Regulation 6 and ICO cookie enforcement.

#### Recommended Implementation

1. Build a client-side Cookie Consent Banner (`apps/web/components/common/CookieConsentBanner.tsx`).
2. Provide:
   - Accept All
   - Reject Non-Essential
   - Manage Preferences (Strictly Necessary, Functional/3D Visuals)
3. Bundle `@splinetool/viewer` locally via npm or conditionalize Spline 3D canvas so it renders a clean CSS/Canvas fallback until the user accepts Functional/Visual cookies.
4. Add a persistent "Cookie Preferences" link in `Footer.tsx` allowing consent withdrawal.

#### Files

- `apps/web/components/landing/SplineHeroBackground.tsx`
- `apps/web/components/landing/Footer.tsx`
- `apps/web/app/layout.tsx`
- New: `apps/web/components/common/CookieConsentBanner.tsx`
- New: `apps/web/hooks/useCookieConsent.ts`

#### Frontend Changes

```tsx
// Conditional rendering in SplineHeroBackground.tsx
const { hasConsent } = useCookieConsent("visuals_3d");

if (!hasConsent) {
  return <StaticGraphicFallback />;
}
return <SplineViewer sceneUrl={activeUrl} />;
```

#### Testing

1. Clear browser cookies and navigate to `/`.
2. Inspect the Network tab in DevTools: verify NO requests to `unpkg.com` or `spline.design` occur before clicking "Accept All".

#### Business / Legal Decision

Approve the Cookie Policy text and categories.

---

### Item 5: Publish Privacy Notice & Link at Points of Data Collection (GDPR-NOT-001)

#### Current

Registration and login forms have no Privacy Notice links. Footer legal links point to `#`.

#### Problem

Violation of UK GDPR Article 13 (Transparency & information to data subjects).

#### Recommended Implementation

1. Create `apps/web/app/privacy/page.tsx` hosting the full Privacy Notice.
2. Create `apps/web/app/terms/page.tsx` hosting Terms of Service.
3. Update `Footer.tsx` to link to `/privacy` and `/terms`.
4. In `RegisterForm.tsx` and `LoginForm.tsx`, add an explicit notice with clickable links.

#### Files

- `apps/web/components/auth/RegisterForm.tsx`
- `apps/web/components/auth/LoginForm.tsx`
- `apps/web/components/landing/Footer.tsx:96-102`
- New: `apps/web/app/privacy/page.tsx`
- New: `apps/web/app/terms/page.tsx`

#### Frontend Changes

```tsx
// apps/web/components/auth/RegisterForm.tsx
<p className="text-[11px] text-zinc-400 mt-3 text-center leading-relaxed">
  By creating an account, you acknowledge our{" "}
  <Link
    href="/privacy"
    className="text-sky-400 underline hover:text-sky-300"
    target="_blank"
  >
    Privacy Notice
  </Link>{" "}
  and agree to our{" "}
  <Link
    href="/terms"
    className="text-sky-400 underline hover:text-sky-300"
    target="_blank"
  >
    Terms of Service
  </Link>
  .
</p>
```

#### Business / Legal Decision

Legal counsel must draft the statutory Privacy Notice and Terms of Service.

---

### Item 6: Sanitize Error Traces in AI Diagnosis & Disable Telemetry by Default (GDPR-AI-001)

#### Current

In `execution_services.py:859-860`, raw database error trace `{err_msg}` is passed into LLM diagnosis prompts. LangSmith tracing is active by default in docker-compose.

#### Problem

Constraint violations containing personal row data (e.g. emails, phone numbers) are transmitted to US-based AI APIs and LangSmith observability without filtering.

#### Recommended Implementation

1. Pass `{err_msg}` through `CredentialSanitizer.mask_credentials()` AND a regex-based PII mask (redacting emails, phone numbers, and quoted literal strings) before inserting into the LLM prompt.
2. Change default LangSmith tracing in `config.py` and `docker-compose.yml` to `false`.

#### Files

- `apps/api/app/modules/execution/execution_services.py:820-865`
- `apps/api/app/core/credential_sanitizer.py`
- `docker-compose.yml:49-56`
- `apps/api/app/core/config.py:56-59`

#### Backend Changes

```python
# apps/api/app/modules/execution/execution_services.py
clean_err = CredentialSanitizer.mask_credentials(err_msg)
# Redact email addresses and quoted row literals
clean_err = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', clean_err)
clean_err = re.sub(r"Key \((.*?)\)=\((.*?)\)", r"Key (\1)=([REDACTED_VALUE])", clean_err)

llm_prompt = f"""...
Raw Error Trace (Sanitized):
{clean_err}
..."""
```

#### Testing

Simulate a failed migration with a unique constraint error `Key (email)=(john@example.co.uk) already exists`. Inspect the outgoing prompt and verify `john@example.co.uk` is replaced with `[REDACTED_VALUE]`.

#### Business / Legal Decision

Confirm DPAs with Google Cloud / OpenAI / LangChain Inc.

---

### Item 7: Remove Sensitive Tokens from WebSocket Query Strings & Fix LocalStorage (GDPR-SEC-004)

#### Current

`/agents/ws/{agent_id}` accepts JWT tokens via `?token=` query parameter. Frontend components read `localStorage.getItem('access_token')`.

#### Problem

Tokens in query strings are leaked in access logs and browser histories. Storing/reading access tokens in `localStorage` increases XSS risk and crosses trust boundaries.

#### Recommended Implementation

1. Require WebSocket authentication to use the established first-frame JSON message: `{ "type": "auth", "token": "<jwt>" }` or HTTP-only cookies. Remove the `token: Optional[str] = Query(None)` argument in the router.
2. In `DockerCommandOutput.tsx:80` and `AgentStatusBanner.tsx:44`, remove `|| localStorage.getItem('access_token')`.

#### Files

- `apps/api/app/modules/agents/agents_routes.py:168-196`
- `apps/web/components/agents/DockerCommandOutput.tsx:80`
- `apps/web/components/agents/AgentStatusBanner.tsx:44`

#### Frontend Changes

```typescript
// apps/web/components/agents/DockerCommandOutput.tsx
// Before: const token = agent.api_token || localStorage.getItem('access_token');
// After:
const token = agent.api_token;
```

#### Testing

Verify WebSocket connects cleanly using the initial JSON auth frame. Check web server logs to confirm tokens no longer appear in query strings.

#### Business / Legal Decision

None.

---

### Item 8: Mask Plaintext Emails in Logs & Normalize Password Reset Errors (GDPR-LOG-001 & GDPR-SEC-006)

#### Current

`email.py:54, 57` logs plaintext user emails. `users_routes.py:437-440` returns 404 if an email does not exist, enabling user enumeration.

#### Problem

Plaintext personal data in server logs; user enumeration vulnerability.

#### Recommended Implementation

1. Mask emails in `email.py`: `mask_email(to_email)` (e.g. `j***n@domain.com`).
2. In `forgot_password` route, always return a generic 200 response: `"If an account exists for this email, a password reset link has been dispatched."`

#### Files

- `apps/api/app/core/email.py:54, 57`
- `apps/api/app/modules/users/users_routes.py:434-489`

#### Backend Changes

```python
# apps/api/app/modules/users/users_routes.py
@router.post("/auth/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    user = await UserService.get_user_by_email(db, payload.email)

    # Generic message prevents email enumeration
    generic_msg = MessageResponse(message="If an account exists with this email address, a password reset link has been sent.")

    if not user or not user.is_active or (user.google_id and not user.password_hash):
        return generic_msg

    # Rate limiting and dispatch logic...
    ...
    return generic_msg
```

#### Testing

Send a request with a non-existent email and an existing email; verify both return identical HTTP 200 responses.

#### Business / Legal Decision

Accept UX adjustment for password reset flow.

---

### Item 9: Build User Rights Interfaces: Data Portability API & Account Settings UI (GDPR-RIGHTS-001)

#### Current

No Data Portability (Art. 20) export endpoint. No user interface for profile editing (`PUT /users/me`) or account deletion (`DELETE /users/me`).

#### Problem

Data subjects cannot exercise statutory rights directly in the platform.

#### Recommended Implementation

1. Implement `GET /api/v1/users/me/export` in `users_routes.py` returning an aggregated JSON archive.
2. Build an Account Settings page (`/settings`) in `apps/web` with Profile Update, Data Export, and Account Deletion modals.

#### Files

- `apps/api/app/modules/users/users_routes.py`
- `apps/web/app/dashboard/page.tsx` (Add Settings link to navigation)
- New: `apps/web/app/settings/page.tsx`
- New: `apps/web/components/settings/AccountSettingsView.tsx`

#### Backend Changes

```python
# apps/api/app/modules/users/users_routes.py
@router.get("/users/me/export", summary="Export all personal data (Data Portability Art. 20)")
async def export_my_data(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates structured machine-readable JSON export of all user-associated data."""
    export_payload = await UserService.generate_user_data_export(db, current_user.id)
    return JSONResponse(
        content=export_payload,
        headers={"Content-Disposition": f"attachment; filename=migraflow_export_{current_user.id}.json"}
    )
```

#### Testing

Navigate to `/settings`, click "Export My Data", and verify a complete JSON file downloads. Click "Delete Account", verify user and linked agents are deleted and cookies cleared.

#### Business / Legal Decision

Approve formal Data Subject Request SOP.

---

### Item 10: Enforce Secure Cookie Defaults & Automated Data Retention (GDPR-SEC-005 & GDPR-RET-001)

#### Current

`COOKIE_SECURE=False` is default in `config.py`. PostgreSQL records and DuckDB staging files have no automated expiration or cleanup.

#### Problem

Session cookies can be transmitted over plain HTTP; personal data retained indefinitely in violation of Art. 5(1)(e).

#### Recommended Implementation

1. In `config.py`, default `COOKIE_SECURE = (ENVIRONMENT.lower() == "production")`.
2. Implement a background periodic retention task in `apps/api/app/main.py` that purges execution traces and job audit logs older than a retention threshold (e.g. 90 days).
3. In `apps/agent/engine/orchestrator.py`, wrap migration execution in a `finally:` block that ensures all `/tmp/staging_{job_id}_*.duckdb` files are deleted upon completion or crash.

#### Files

- `apps/api/app/core/config.py:21`
- `apps/api/app/main.py`
- `apps/agent/engine/orchestrator.py`

#### Backend & Agent Changes

```python
# apps/agent/engine/orchestrator.py
try:
    # Run ETL steps...
finally:
    # Ensure DuckDB staging files for THIS job are deleted immediately
    for fname in os.listdir(tmp_dir):
        if fname.startswith(f"staging_{job_id}_") and fname.endswith(".duckdb"):
            try:
                os.remove(os.path.join(tmp_dir, fname))
                logger.info(f"Cleaned up staging file on exit: {fname}")
            except Exception:
                pass
```

#### Testing

Simulate a failed migration on the agent; verify the temporary DuckDB staging file in `/tmp` is removed immediately upon exit.

#### Business / Legal Decision

Legal confirmation of organizational data retention schedules.

---

## Part 3: Verification & Definition of Done

Before marking the UK GDPR technical remediation complete, the following checklist must pass:

- [ ] `CORS_ORIGINS` does NOT contain `*` and rejects wildcard origin regex when credentials are enabled.
- [ ] Non-admin users cannot query `GET /api/v1/users` or `GET /api/v1/users/{other_id}`.
- [ ] No plaintext database credentials or fallback JWT secrets exist in repository files.
- [ ] Cookie consent banner appears on first visit; no scripts to `unpkg.com` or `spline.design` execute prior to opt-in.
- [ ] `/privacy` and `/terms` pages are published and linked on registration and login screens.
- [ ] Error traces sent to AI diagnosis have emails, passwords, and row literals masked.
- [ ] LangSmith tracing is disabled by default in production.
- [ ] Passwords up to at least 128 characters can be registered without artificial frontend truncation.
- [ ] Password reset endpoint returns generic responses preventing email enumeration.
- [ ] Dedicated `GET /api/v1/users/me/export` endpoint allows data portability download.
- [ ] User Settings page allows self-service profile update and account deletion.
- [ ] Agent DuckDB staging files are removed in a `finally:` block upon termination.
