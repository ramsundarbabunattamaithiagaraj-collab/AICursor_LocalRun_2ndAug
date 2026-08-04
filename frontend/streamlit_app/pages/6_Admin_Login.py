from __future__ import annotations

import streamlit as st

from utils.api_client import ApiError, api_post
from utils.auth_state import init_session_state, is_authenticated, logout

st.set_page_config(page_title="Admin Login - RetailIQ", page_icon="🔐", layout="wide")
init_session_state()

st.title("🔐 Admin / Staff Login")

if is_authenticated():
    user = st.session_state.get("current_user") or {}
    st.success(f"Logged in as **{user.get('username')}** ({user.get('role')}).")
    if st.button("Log out"):
        logout()
        st.rerun()
    st.stop()

tab_login, tab_register = st.tabs(["Login", "Register"])

with tab_login:
    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="Admin@123")
        submitted = st.form_submit_button("Log in")
    if submitted:
        try:
            response = api_post("/api/v1/auth/login", {"username": username, "password": password})
            st.session_state["access_token"] = response["access_token"]
            st.session_state["current_user"] = response["user"]
            st.success("Logged in successfully.")
            st.rerun()
        except ApiError as exc:
            st.error(f"Login failed: {exc.detail}")

    st.caption("Default seeded admin: username `admin`, password `Admin@123` (change in production).")

with tab_register:
    with st.form("register_form"):
        reg_username = st.text_input("Username", key="reg_username")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_role = st.selectbox("Role", ["customer", "staff", "admin"], key="reg_role")
        reg_submitted = st.form_submit_button("Register")
    if reg_submitted:
        try:
            api_post(
                "/api/v1/auth/register",
                {"username": reg_username, "email": reg_email, "password": reg_password, "role": reg_role},
            )
            st.success("Registered successfully. You can now log in.")
        except ApiError as exc:
            st.error(f"Registration failed: {exc.detail}")
