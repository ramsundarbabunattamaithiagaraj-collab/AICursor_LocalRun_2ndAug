"""RetailIQ Platform - Streamlit frontend entrypoint."""
from __future__ import annotations

import streamlit as st

from utils.api_client import is_backend_reachable
from utils.auth_state import init_session_state, is_authenticated

st.set_page_config(page_title="RetailIQ Platform", page_icon="🛍️", layout="wide")
init_session_state()

st.title("🛍️ RetailIQ Platform")
st.caption("AI-powered retail operations platform - catalog, inventory, orders, RAG knowledge assistant, and multi-agent SDLC toolkit.")

if not is_backend_reachable():
    st.warning(
        "Cannot reach the backend API right now. If it's hosted on a free-tier "
        "service, it may be **cold-starting after a period of inactivity** - "
        "this can take up to a minute. Locally, start it with:\n\n"
        "`uvicorn app.main:app --reload` (from the `backend` folder)."
    )
    if st.button("🔄 Retry"):
        is_backend_reachable.clear()
        st.rerun()
else:
    st.success("Backend API is reachable.")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Domain", "Retail")
with col2:
    st.metric("Authenticated", "Yes" if is_authenticated() else "No")
with col3:
    st.metric("AI Framework", "CrewAI")

st.divider()

st.subheader("What's inside")
st.markdown(
    """
- **Product Catalog** — browse, search, and manage SKUs, brands, categories, and pricing.
- **Inventory** — view stock across stores/warehouses and adjust quantities.
- **Orders** — place orders and track their lifecycle (cart → placed → paid → shipped → delivered → returns/refunds).
- **RAG Assistant** — ingest retail PDFs (catalogs, price lists, planograms) and ask natural-language questions with cited sources.
- **AI Agents Studio** — run the CrewAI Business Analyst / Architect / Developer / Tester / Documentation agents against a project brief.
- **Admin Login** — authenticate to unlock write operations across the platform.
"""
)

st.info("Use the sidebar to navigate between pages.")
