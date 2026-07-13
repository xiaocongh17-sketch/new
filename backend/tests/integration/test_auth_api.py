"""Integration tests for authentication API endpoints.

Endpoints tested:
    POST /api/v1/auth/login    - WeCom user login
    GET  /api/v1/auth/me       - Current user profile
    POST /api/v1/auth/refresh  - Token refresh

Note: These tests require manual testing with running PostgreSQL;
      rate limiting middleware adds complexity to the test transport setup.
"""

import pytest
from httpx import AsyncClient
from jose import jwt

from app.infrastructure.config.settings import settings
from app.domain.entities.user import User


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------
class TestLogin:
    async def test_login_success(self, test_client: AsyncClient, test_user: User):
        """Should return access and refresh tokens for an existing user."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"wecom_userid": test_user.wecom_userid},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == settings.jwt_access_token_expire_minutes * 60

        # Verify the access token is valid and contains the correct user
        payload = jwt.decode(
            data["access_token"],
            settings.jwt_secret_key,
            algorithms=["HS256"],
        )
        assert payload["sub"] == str(test_user.id)
        assert payload["role"] == test_user.role.value
        assert payload["type"] == "access"

    async def test_login_user_not_found(self, test_client: AsyncClient):
        """Should return 404 when the wecom_userid does not exist."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"wecom_userid": "nonexistent_user"},
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert "detail" in data

    async def test_login_invalid_payload(self, test_client: AsyncClient):
        """Should return 422 for missing required fields."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={},
        )
        assert response.status_code == 422, response.text

        response = await test_client.post(
            "/api/v1/auth/login",
            json={"wecom_userid": ""},
        )
        # Empty string fails the "must provide" guard in the endpoint
        assert response.status_code == 422, response.text


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------
class TestGetMe:
    async def test_get_me_authenticated(
        self, test_client: AsyncClient, auth_headers: dict[str, str], test_user: User
    ):
        """Should return the current user profile when authenticated."""
        response = await test_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["wecom_userid"] == test_user.wecom_userid
        assert data["name"] == test_user.name
        assert data["role"] == test_user.role.value
        assert data["store_id"] == str(test_user.store_id)
        assert data["is_active"] is True

    async def test_get_me_unauthenticated(self, test_client: AsyncClient):
        """Should return 401 when no auth token is provided."""
        response = await test_client.get("/api/v1/auth/me")
        assert response.status_code == 401, response.text

    async def test_get_me_invalid_token(self, test_client: AsyncClient):
        """Should return 401 when an invalid token is provided."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = await test_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401, response.text

    async def test_get_me_expired_token(self, test_client: AsyncClient, test_user: User):
        """Should return 401 when the token is expired."""
        from datetime import datetime, timedelta, timezone

        payload = {
            "sub": str(test_user.id),
            "role": test_user.role.value,
            "store_id": str(test_user.store_id) if test_user.store_id else None,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # expired
            "type": "access",
        }
        expired_token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await test_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401, response.text


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh
# ---------------------------------------------------------------------------
class TestRefreshToken:
    async def test_refresh_success(
        self, test_client: AsyncClient, test_user: User
    ):
        """Should return a new access token given a valid refresh token."""
        # First, obtain a refresh token via login
        login_resp = await test_client.post(
            "/api/v1/auth/login",
            json={"wecom_userid": test_user.wecom_userid},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == settings.jwt_access_token_expire_minutes * 60

        # The new access token should be usable
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        me_resp = await test_client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200, me_resp.text

    async def test_refresh_invalid_token(self, test_client: AsyncClient):
        """Should return 401 for an invalid refresh token."""
        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not_a_valid_token"},
        )
        assert response.status_code == 401, response.text

    async def test_refresh_with_access_token(self, test_client: AsyncClient, test_user: User):
        """Should return 401 when using an access token (not a refresh token)."""
        login_resp = await test_client.post(
            "/api/v1/auth/login",
            json={"wecom_userid": test_user.wecom_userid},
        )
        access_token = login_resp.json()["access_token"]

        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401, response.text

    async def test_refresh_missing_field(self, test_client: AsyncClient):
        """Should return 422 when refresh_token is missing."""
        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={},
        )
        assert response.status_code == 422, response.text
