# ☁️ CloudPilot AI

**AI-Powered Multi-Cloud & DevOps Intelligence Platform**

CloudPilot AI is a modular, multi-tenant platform for managing independent AWS, Microsoft Azure, and Google Cloud sessions from one centralized workspace, analyzing operational logs, monitoring infrastructure, understanding cloud costs, and assisting DevOps troubleshooting with AI.

> **Status:** Phase 1 foundation. Provider authentication, live cloud integrations, and AI analysis are planned but are not active yet. No cloud account is connected by this scaffold.

## Product vision
- Central Cloud Session Center: connect providers, selectively start/end independent sessions, configure inactivity timeouts, and review session history.
- Multi-cloud support: AWS, Azure, and GCP with provider-specific authentication.
- AI log intelligence: parsing, error grouping, evidence-based root-cause investigation, and recommendations.
- Monitoring and incident management: service health, metrics, timelines, and reports.
- Cloud Cost Insights: spending trends and resource optimization suggestions.
- Infrastructure Assistant and AI agents: cloud/DevOps Q&A and multi-step investigation.
- Security-first design: tenant isolation, least privilege, short-lived credentials, secret redaction, and audit logging.

See [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

## Initial stack
Python 3.11+, Streamlit, FastAPI, Pydantic Settings, SQLAlchemy, SQLite (local), PostgreSQL (planned), and Pytest.

## Run locally
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Start the API:
```bash
uvicorn backend.main:app --reload
```
Health: http://127.0.0.1:8000/api/v1/health  
API docs: http://127.0.0.1:8000/docs

Start the frontend in another terminal:
```bash
streamlit run frontend/app.py
```

Run tests: `pytest -q`

## Security
Never commit `.env`, API keys, refresh tokens, private keys, or cloud credentials. Provider credentials and AI keys remain server-side. Initial cloud access is read-only. Do not upload production logs containing secrets.

## Author
**Aditya Kusale** · [GitHub](https://github.com/Aditya-Kusale) · [LinkedIn](https://www.linkedin.com/in/aditya-kusale/)
