# CloudPilot AI — Master Roadmap

**AI-Powered Multi-Cloud & DevOps Intelligence Platform**

## Product principles
- One centralized workspace for AWS, Microsoft Azure, and Google Cloud.
- Independent provider sessions; users can start/end any combination.
- Banking-style inactivity timeout, pre-expiry warning, manual termination, and security-driven termination.
- Separate cloud-account connection state from active CloudPilot session state.
- Least privilege and read-only access initially.
- One centrally managed AI provider credential; cloud authentication remains provider-specific and tenant-scoped.
- Multi-tenant isolation for identities, connections, sessions, data, and audit events.
- Evidence-led AI that distinguishes observations from hypotheses.
- No automatic creation of billable cloud resources.

## Product modules
### Central Cloud Session Center
- Connect/manage AWS, Azure, and GCP accounts.
- Show connected state separately from active session state.
- Start one, two, or all provider sessions.
- End one provider session without affecting others; provide End All.
- Configure idle timeout and warning period.
- Enforce inactivity on the backend; background polling must not reset idle time.
- Show start time, last meaningful activity, expiry, and termination reason.
- Session history, concurrent-session limits, and reauthentication for sensitive actions.

### Cloud integrations
- AWS: IAM roles, STS, EC2, CloudWatch, S3, Cost Explorer.
- Azure: Entra ID, managed identity/service principal patterns, Virtual Machines, Azure Monitor, Log Analytics, Cost Management.
- GCP: OAuth/workload identity patterns, service accounts, Compute Engine, Cloud Logging, Monitoring, billing.
- Normalize provider data while retaining source/provider metadata.

### AI Log Intelligence
- Upload TXT, LOG, and CSV logs; parse timestamps, severity, source, and messages.
- Categorize errors/warnings and group recurring events.
- Evidence-based root-cause investigation with uncertainty.
- Safe troubleshooting recommendations and incident reports.

### Monitoring and Incident Management
- CPU, memory, uptime, service health, error rates where available.
- Unified and provider-specific monitoring.
- Incident severity, status, history, timelines, and reports.

### Cloud Cost Insights
- Analyze authorized billing/usage data or uploaded exports.
- Spending trends, unusual changes, underutilization, optimization suggestions, and cross-provider comparisons.
- Estimates only when source data supports them.

### Infrastructure Assistant
- Cloud/DevOps Q&A, log explanations, deployment troubleshooting.
- Diagnostic commands with explanations.
- Use retrieved documentation/account evidence when available.

### AI Agents and controlled automation
- Multi-step incident investigation, classification, correlation, and reporting.
- Proposed remediation workflows.
- Human approval before infrastructure-changing actions.
- Audit trail for approved actions.

### Security and governance
- Multi-tenant identity/authorization and strict tenant isolation.
- Encrypted secrets/token storage through an appropriate secrets manager.
- Short-lived credentials and provider-supported renewal.
- Least-privilege read-only scopes initially.
- Redact secrets before AI processing.
- Session revocation, audit events, and security monitoring.
- Never expose cloud credentials or AI API keys to the frontend.

## Development phases
| Phase | Deliverable |
|---|---|
| 1 | Modular foundation, settings, API/frontend shells, database foundation, tests, documentation |
| 2 | Central Cloud Session Center, independent session lifecycle, idle timeout, manual termination |
| 3 | AWS auth, temporary credentials, read-only EC2 and CloudWatch retrieval |
| 4 | Log upload/parsing, error detection, root-cause analysis, recommendations |
| 5 | Monitoring dashboard and incident management |
| 6 | Azure and GCP connectors and normalized data |
| 7 | Cloud cost insights |
| 8 | LangGraph AI agents and multi-step investigation |
| 9 | Multi-tenant security hardening, audit, observability, rate limits, threat review |
| 10 | Deployment, documentation, demos, portfolio release |

## Phase 1 acceptance criteria
- [ ] Modular repository structure and documentation.
- [ ] Environment-based configuration; no committed secrets.
- [ ] FastAPI starts and health endpoint responds.
- [ ] Streamlit frontend starts.
- [ ] Tests run without cloud credentials.
- [ ] Architecture and roadmap documented.

## Critical implementation notes
- Initial demos use synthetic/sample data. Do not claim a live cloud connection until provider auth and API retrieval are implemented and tested.
- CloudPilot application session lifetime differs from provider token lifetime. A provider token can expire or be revoked earlier.
- Backend inactivity enforcement uses meaningful authenticated user activity, not polling/telemetry.
- On termination, invalidate the CloudPilot session and revoke provider grants/credentials where supported. Document provider-side revocation limitations.
- Avoid long-lived refresh credentials where possible; prefer roles/workload identity and short-lived credentials.
- Redact tokens, keys, and sensitive data before external AI model calls.
