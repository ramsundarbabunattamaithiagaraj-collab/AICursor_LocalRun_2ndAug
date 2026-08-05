"""Thin HTTP client wrapper around the RetailIQ backend API."""
from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is only needed to read a local .env file during local
    # development. Deployed environments (Streamlit Community Cloud, Docker)
    # supply config via real environment variables / secrets instead, so a
    # missing dotenv package should never crash the app.
    pass

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _auth_headers() -> dict[str, str]:
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _handle_response(response: requests.Response) -> Any:
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(response.status_code, detail)
    if response.status_code == 204:
        return None
    return response.json()


def api_get(path: str, params: dict | None = None) -> Any:
    response = requests.get(f"{API_BASE_URL}{path}", params=params, headers=_auth_headers(), timeout=30)
    return _handle_response(response)


def api_get_paginated(path: str, params: dict | None = None) -> tuple[Any, int]:
    """Like `api_get`, but also returns the total record count reported via
    the `X-Total-Count` response header (falling back to the page length if
    the header is absent), for building pagination controls."""
    response = requests.get(f"{API_BASE_URL}{path}", params=params, headers=_auth_headers(), timeout=30)
    data = _handle_response(response)
    total = int(response.headers.get("X-Total-Count", len(data) if data else 0))
    return data, total


def api_post(path: str, json_body: dict | None = None, files: dict | None = None) -> Any:
    response = requests.post(
        f"{API_BASE_URL}{path}", json=json_body, files=files, headers=_auth_headers(), timeout=60
    )
    return _handle_response(response)


def api_patch(path: str, json_body: dict | None = None) -> Any:
    response = requests.patch(f"{API_BASE_URL}{path}", json=json_body, headers=_auth_headers(), timeout=30)
    return _handle_response(response)


def api_delete(path: str) -> Any:
    response = requests.delete(f"{API_BASE_URL}{path}", headers=_auth_headers(), timeout=30)
    return _handle_response(response)


@st.cache_data(ttl=15, show_spinner=False)
def is_backend_reachable() -> bool:
    """Checks backend health, cached for a short window.

    Streamlit re-runs the entire script on every widget interaction, so an
    uncached network call here would hit the backend on every single rerun -
    a major contributor to sluggishness, especially against a backend host
    that has a cold-start delay (e.g. a free-tier service waking from sleep).
    A short TTL keeps the app responsive between page interactions while
    still detecting backend recovery within ~15 seconds.
    """
    try:
        requests.get(f"{API_BASE_URL}/health", timeout=5)
        return True
    except requests.exceptions.RequestException:
        return False
