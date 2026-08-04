from __future__ import annotations


class TestHealthApi:
    def test_root_returns_success(self, client):
        response = client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["domain"] == "Retail"

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "healthy"
