"""CloudPilot AI Streamlit frontend shell."""
import streamlit as st

st.set_page_config(page_title="CloudPilot AI", page_icon="☁️", layout="wide")
st.title("☁️ CloudPilot AI")
st.caption("AI-Powered Multi-Cloud & DevOps Intelligence Platform")
st.info("Phase 1 foundation. Cloud-provider authentication, live integrations, and AI analysis will be implemented in later phases.")
a, b, c = st.columns(3)
a.metric("Cloud providers", "3 planned")
b.metric("Active cloud sessions", "0")
c.metric("AI analysis", "Not configured")
st.subheader("Cloud Session Center")
st.write("Centralized management for AWS, Azure, and GCP connections and independent sessions is planned for Phase 2.")
st.caption("No cloud account is connected in this development scaffold.")
