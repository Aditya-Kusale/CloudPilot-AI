"""CloudPilot AI Streamlit dashboard."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx
import streamlit as st

API_URL = os.getenv("FRONTEND_API_URL", "http://127.0.0.1:8000").rstrip("/")
PROVIDER_NAMES = {"aws": "Amazon Web Services", "azure": "Microsoft Azure", "gcp": "Google Cloud"}

st.set_page_config(page_title="CloudPilot AI", page_icon="☁️", layout="wide")
st.title("☁️ CloudPilot AI")
st.caption("AI-Powered Multi-Cloud & DevOps Intelligence Platform")
st.info(
    "Phase 2 preview: session controls are simulated locally. No cloud account is connected "
    "and no AWS, Azure, or GCP resources are accessed."
)


def api_request(method: str, path: str):
    try:
        response = httpx.request(method, f"{API_URL}/api/v1{path}", timeout=5.0)
        response.raise_for_status()
        return response.json(), None
    except httpx.HTTPError as exc:
        return None, str(exc)


data, error = api_request("GET", "/sessions")
if error:
    st.error(f"Cannot reach the CloudPilot API at {API_URL}. Keep the FastAPI terminal running. Details: {error}")
    st.stop()

providers = data["providers"]
active_count = data["active_sessions"]
a, b, c = st.columns(3)
a.metric("Cloud providers", "3")
b.metric("Active sessions", active_count)
c.metric("Idle timeout", f'{data["idle_timeout_minutes"]} min')

st.subheader("Cloud Session Center")
st.caption(
    f'Sessions end after {data["idle_timeout_minutes"]} minutes without activity. '
    f'A warning appears during the final {data["warning_minutes"]} minutes.'
)

columns = st.columns(3)
for column, item in zip(columns, providers):
    provider = item["provider"]
    session = item["session"]
    with column:
        st.markdown(f"### {provider.upper()}")
        st.caption(PROVIDER_NAMES[provider])
        if session:
            st.success("CloudPilot session active")
            st.caption(f'Expires: {session["expires_at"].replace("T", " ")[:19]} UTC')
            remaining = session["seconds_until_expiry"]
            st.metric("Time remaining", f"{remaining // 60}m {remaining % 60}s")
            if session["warning"]:
                st.warning("Session inactivity timeout is approaching.")
            if st.button(f"End {provider.upper()} session", key=f"end_{provider}", use_container_width=True):
                _, err = api_request("POST", f"/sessions/{provider}/end")
                if err:
                    st.error(err)
                else:
                    st.rerun()
            if st.button(f"Record activity · {provider.upper()}", key=f"activity_{provider}", use_container_width=True):
                _, err = api_request("POST", f"/sessions/{provider}/activity")
                if err:
                    st.error(err)
                else:
                    st.rerun()
        else:
            st.info("No active session")
            if st.button(f"Start {provider.upper()} session", key=f"start_{provider}", use_container_width=True):
                _, err = api_request("POST", f"/sessions/{provider}/start")
                if err:
                    st.error(err)
                else:
                    st.rerun()

st.divider()
left, right = st.columns([2, 1])
with left:
    st.subheader("Session history")
    history = data["history"]
    if history:
        st.dataframe(
            [{
                "Provider": row["provider"].upper(),
                "Status": row["status"],
                "Started (UTC)": row["started_at"].replace("T", " ")[:19],
                "Ended (UTC)": (row["ended_at"] or "—").replace("T", " ")[:19] if row["ended_at"] else "—",
                "End reason": row["end_reason"] or "—",
            } for row in history],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No session activity recorded yet.")
with right:
    st.subheader("Safety controls")
    st.write("Ending one provider session does not affect the others.")
    if active_count and st.button("End All Sessions", type="primary", use_container_width=True):
        _, err = api_request("POST", "/sessions/end-all")
        if err:
            st.error(err)
        else:
            st.rerun()

st.caption("Prototype only · Provider authentication and real cloud access are not enabled.")
