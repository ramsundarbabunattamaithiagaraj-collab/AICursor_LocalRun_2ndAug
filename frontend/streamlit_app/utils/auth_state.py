"""Session-state helpers for authentication in the Streamlit app."""
from __future__ import annotations

import streamlit as st


def init_session_state() -> None:
    st.session_state.setdefault("access_token", None)
    st.session_state.setdefault("current_user", None)


def is_authenticated() -> bool:
    return st.session_state.get("access_token") is not None


def is_admin() -> bool:
    user = st.session_state.get("current_user")
    return bool(user and user.get("role") == "admin")


def logout() -> None:
    st.session_state["access_token"] = None
    st.session_state["current_user"] = None
