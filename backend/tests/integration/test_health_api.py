"""Integration tests for the health-check endpoint.

Endpoints tested:
    GET /api/health
"""

from httpx import AsyncClient


class TestHealthEndpoint:
    async def test_health_returns_ok(self, test_client: AsyncClient):
        """Health endpoint should return 200 with status ok and version."""
        response = await test_client.get("/api/health")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"

    async def test_health_no_auth_required(self, test_client: AsyncClient):
        """Health endpoint should be accessible without authentication."""
        response = await test_client.get("/api/health")
        assert response.status_code == 200, response.text

    async def test_health_method_not_allowed(self, test_client: AsyncClient):
        """POST to health endpoint should return 405."""
        response = await test_client.post("/api/health")
        assert response.status_code == 405, response.text
