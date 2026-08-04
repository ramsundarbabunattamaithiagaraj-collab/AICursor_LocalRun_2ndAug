from __future__ import annotations


class TestAuthApi:
    def test_register_and_login_flow(self, client):
        register_response = client.post(
            "/api/v1/auth/register",
            json={"username": "jdoe", "email": "jdoe@example.com", "password": "StrongPass1"},
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login", json={"username": "jdoe", "password": "StrongPass1"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "jdoe"

    def test_login_wrong_password_returns_401(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"username": "jdoe", "email": "jdoe@example.com", "password": "StrongPass1"},
        )
        response = client.post("/api/v1/auth/login", json={"username": "jdoe", "password": "wrong"})
        assert response.status_code == 401

    def test_me_without_token_returns_401(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_register_short_password_returns_422(self, client):
        response = client.post(
            "/api/v1/auth/register", json={"username": "jdoe", "email": "jdoe@example.com", "password": "short"}
        )
        assert response.status_code == 422
