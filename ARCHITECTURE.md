# CloudPilot AI — Architecture

## High-level flow
```text
Streamlit UI
    │ HTTPS
    ▼
FastAPI (user authn/authz and API)
    ├── Cloud Session Manager ── Session Store (tenant-scoped)
    ├── Cloud Connectors ─────── AWS / Azure / GCP APIs
    ├── Data Normalization ──── Logs / metrics / resource data
    ├── AI Intelligence ─────── Central AI provider API
    └── Database ────────────── Users / connections / sessions / incidents
```

## Key boundaries
### Human identity vs cloud identity
Authenticate the human user separately from provider authentication. Authorize every request against the user and tenant. Never send cloud secrets or AI provider keys to the browser.

### Connection vs active session
A connection is a configured, authorized cloud account. An active CloudPilot session is the user's current working window for that provider. A connection may remain configured while its CloudPilot session is inactive. Starting a session must validate provider authorization and obtain fresh short-lived credentials as appropriate.

### Independent provider sessions
AWS, Azure, and GCP sessions are independent. Ending one must not end another unless the user chooses End All or a security policy requires global termination.

### Banking-style inactivity
- Enforce idle timeout on the backend.
- Track meaningful authenticated user activity.
- Do not treat background polling or automatic refresh as activity.
- Warn before expiry where an interactive client is available.
- Terminate on timeout, manual logout, revocation, or security failure.
- Provider credential expiry is separate; an app session cannot override provider token expiry.

### Least privilege
Initial real integrations are read-only. Mutations require a later explicit design, authorization check, user confirmation, and audit event.

### Multi-tenancy
Every customer-owned record is tenant-scoped. Validate tenant membership server-side; never trust a tenant ID supplied by the browser.

### AI data handling
Redact secrets and sensitive identifiers; send minimum relevant context; keep AI keys server-side; separate evidence, uncertainty, and recommendations. AI is advisory initially.

## Phase 1 runtime
Streamlit UI, FastAPI API, Pydantic Settings, SQLAlchemy, SQLite local default, PostgreSQL planned, and Pytest. No real cloud credentials or AI key are required for the Phase 1 scaffold.
