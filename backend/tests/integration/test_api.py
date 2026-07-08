"""Integration tests for API endpoints — require a running PostgreSQL/Docker stack."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealth:
    async def test_health_endpoint(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"


class TestOpenAPI:
    async def test_docs_available(self, client):
        response = await client.get("/api/docs")
        assert response.status_code == 200

    async def test_openapi_json(self, client):
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "AI Store Copilot API"


@pytest.mark.skip(reason="Requires running PostgreSQL (Docker stack)")
class TestAuth:
    async def test_login_missing_user(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"wecom_userid": "nonexistent"},
        )
        assert response.status_code == 404

    async def test_login_invalid_payload(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={},
        )
        assert response.status_code == 422


@pytest.mark.skip(reason="Requires running PostgreSQL (Docker stack)")
class TestHouses:
    async def test_list_houses_requires_auth(self, client):
        response = await client.get("/api/v1/houses")
        assert response.status_code == 401

    async def test_create_house_requires_auth(self, client):
        response = await client.post(
            "/api/v1/houses",
            json={"community": "test", "area": 100, "room_type": "3室", "rent_price": 3000, "owner_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 401


@pytest.mark.skip(reason="Requires running PostgreSQL (Docker stack)")
class TestAI:
    async def test_ai_chat_requires_auth(self, client):
        response = await client.post(
            "/api/v1/ai/chat",
            json={"query": "如何邀约房东？"},
        )
        assert response.status_code == 401


@pytest.mark.skip(reason="Requires running PostgreSQL (Docker stack)")
class TestKnowledge:
    async def test_list_knowledge_requires_auth(self, client):
        response = await client.get("/api/v1/knowledge")
        assert response.status_code == 401


@pytest.mark.skip(reason="Requires running PostgreSQL (Docker stack)")
class TestStores:
    async def test_list_stores_requires_auth(self, client):
        response = await client.get("/api/v1/stores")
        assert response.status_code == 401
