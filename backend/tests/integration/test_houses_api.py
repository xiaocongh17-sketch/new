"""Integration tests for houses API endpoints.

Endpoints tested:
    POST   /api/v1/houses          - Create a house (201)
    GET    /api/v1/houses          - List / search houses
    GET    /api/v1/houses/{id}     - Get single house
    PUT    /api/v1/houses/{id}     - Update house
    DELETE /api/v1/houses/{id}     - Delete house
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.domain.entities.house import House
from app.domain.entities.user import User


# ===================================================================
# POST /api/v1/houses  -  Create house
# ===================================================================
class TestCreateHouse:
    """Tests for creating a house listing."""

    CREATE_PAYLOAD = {
        "community": "融创文旅城",
        "area": 120.00,
        "room_type": "4室2厅2卫",
        "rent_price": 5000,
        "decoration": "精装",
        "floor_info": "15/30",
        "address": "无锡市融创文旅城A区1栋1501",
    }

    async def test_create_house_success(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
        test_landlord: User,
    ):
        """Should create a house and return 201 with the house data."""
        payload = {**self.CREATE_PAYLOAD, "owner_id": str(test_landlord.id)}
        response = await test_client.post(
            "/api/v1/houses",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["community"] == payload["community"]
        assert float(data["area"]) == payload["area"]
        assert data["room_type"] == payload["room_type"]
        assert float(data["rent_price"]) == payload["rent_price"]
        assert data["decoration"] == payload["decoration"]
        assert data["floor_info"] == payload["floor_info"]
        assert data["owner_id"] == payload["owner_id"]
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
        # Unit price should be auto-calculated
        assert float(data["unit_price"]) == pytest.approx(
            payload["rent_price"] / payload["area"], 0.01
        )

    async def test_create_house_requires_auth(
        self,
        test_client: AsyncClient,
        test_landlord: User,
    ):
        """Should return 401 when no auth token is provided."""
        payload = {**self.CREATE_PAYLOAD, "owner_id": str(test_landlord.id)}
        response = await test_client.post("/api/v1/houses", json=payload)
        assert response.status_code == 401, response.text

    async def test_create_house_missing_required_fields(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Should return 422 when required fields are missing."""
        # Missing community (required, min_length=1)
        response = await test_client.post(
            "/api/v1/houses",
            json={"area": 100, "room_type": "3室", "rent_price": 3000, "owner_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
        assert response.status_code == 422, response.text

        # Missing owner_id
        response = await test_client.post(
            "/api/v1/houses",
            json={"community": "test", "area": 100, "room_type": "3室", "rent_price": 3000},
            headers=auth_headers,
        )
        assert response.status_code == 422, response.text

    async def test_create_house_invalid_rent_price(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
        test_landlord: User,
    ):
        """Should return 422 when rent_price is zero or negative."""
        payload = {**self.CREATE_PAYLOAD, "owner_id": str(test_landlord.id), "rent_price": 0}
        response = await test_client.post(
            "/api/v1/houses", json=payload, headers=auth_headers,
        )
        assert response.status_code == 422, response.text

        payload["rent_price"] = -100
        response = await test_client.post(
            "/api/v1/houses", json=payload, headers=auth_headers,
        )
        assert response.status_code == 422, response.text


# ===================================================================
# GET /api/v1/houses  -  List houses
# ===================================================================
class TestListHouses:
    """Tests for listing / searching houses."""

    async def test_list_houses_empty(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Should return an empty list when no houses exist."""
        response = await test_client.get("/api/v1/houses", headers=auth_headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 0

    async def test_list_houses_with_data(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
        test_house: House,
    ):
        """Should return a paginated list of houses."""
        response = await test_client.get("/api/v1/houses", headers=auth_headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["total"] >= 1
        item = data["items"][0]
        assert item["community"] == test_house.community
        assert float(item["area"]) == float(test_house.area)

    async def test_list_houses_requires_auth(self, test_client: AsyncClient):
        """Should return 401 without auth."""
        response = await test_client.get("/api/v1/houses")
        assert response.status_code == 401, response.text

    async def test_search_by_community(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
        test_house: House,
    ):
        """Should filter houses by community name (partial match)."""
        response = await test_client.get(
            "/api/v1/houses",
            params={"community": test_house.community[:2]},  # partial match
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert test_house.community[:2].lower() in item["community"].lower()

    async def test_search_by_community_no_match(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Should return empty results when community does not match."""
        response = await test_client.get(
            "/api/v1/houses",
            params={"community": "不存在的社区名称"},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_search_by_price_range(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
        test_house: House,
    ):
        """Should filter houses within a price range."""
        # Within range
        response = await test_client.get(
            "/api/v1/houses",
            params={"min_price": 3000, "max_price": 4000},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] >= 1

        # Outside range
        response = await test_client.get(
            "/api/v1/houses",
            params={"min_price": 50000, "max_price": 100000},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data2 = response.json()
        assert data2["total"] == 0

    async def test_list_houses_pagination(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Should respect page and page_size parameters."""
        response = await test_client.get(
            "/api/v1/houses",
            params={"page": 1, "page_size": 5},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


# ===================================================================
# GET /api/v1/houses/{id}  -  Get single house
# ===================================================================
class TestGetHouse:
    """Tests for fetching a single house."""

    async def test_get_house_found(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
        test_house: House,
    ):
        """Should return the house when it exists."""
        response = await test_client.get(
            f"/api/v1/houses/{test_house.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == str(test_house.id)
        assert data["community"] == test_house.community
        assert float(data["area"]) == float(test_house.area)
        assert data["room_type"] == test_house.room_type
        assert float(data["rent_price"]) == float(test_house.rent_price)

    async def test_get_house_not_found(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Should return 404 when the house does not exist."""
        fake_id = uuid.uuid4()
        response = await test_client.get(
            f"/api/v1/houses/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404, response.text

    async def test_get_house_requires_auth(
        self,
        test_client: AsyncClient,
        test_house: House,
    ):
        """Should return 401 without auth."""
        response = await test_client.get(f"/api/v1/houses/{test_house.id}")
        assert response.status_code == 401, response.text

    async def test_get_house_invalid_uuid(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Should return 422 for an invalid UUID format."""
        response = await test_client.get(
            "/api/v1/houses/not-a-uuid",
            headers=auth_headers,
        )
        assert response.status_code == 422, response.text


# ===================================================================
# PUT /api/v1/houses/{id}  -  Update house
# ===================================================================
class TestUpdateHouse:
    """Tests for updating a house."""

    async def test_update_house_success(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
        test_house: House,
    ):
        """Should update house fields and return the updated house."""
        response = await test_client.put(
            f"/api/v1/houses/{test_house.id}",
            json={"rent_price": 4000, "decoration": "豪华装修"},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert float(data["rent_price"]) == 4000
        assert data["decoration"] == "豪华装修"
        # Unit price should be recalculated
        assert float(data["unit_price"]) == pytest.approx(4000 / float(test_house.area), 0.01)

    async def test_update_house_partial(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
        test_house: House,
    ):
        """Should allow partial update (only specified fields change)."""
        response = await test_client.put(
            f"/api/v1/houses/{test_house.id}",
            json={"community": "更新后的小区名"},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["community"] == "更新后的小区名"
        # Other fields should remain unchanged
        assert data["room_type"] == test_house.room_type

    async def test_update_house_not_found(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Should return 404 when the house does not exist."""
        fake_id = uuid.uuid4()
        response = await test_client.put(
            f"/api/v1/houses/{fake_id}",
            json={"community": "新小区"},
            headers=auth_headers,
        )
        assert response.status_code == 404, response.text

    async def test_update_house_requires_auth(
        self,
        test_client: AsyncClient,
        test_house: House,
    ):
        """Should return 401 without auth."""
        response = await test_client.put(
            f"/api/v1/houses/{test_house.id}",
            json={"community": "新小区"},
        )
        assert response.status_code == 401, response.text

    async def test_update_house_invalid_price(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],
        test_house: House,
    ):
        """Should return 422 for invalid price values."""
        response = await test_client.put(
            f"/api/v1/houses/{test_house.id}",
            json={"rent_price": -100},
            headers=auth_headers,
        )
        assert response.status_code == 422, response.text


# ===================================================================
# DELETE /api/v1/houses/{id}  -  Delete house
# ===================================================================
class TestDeleteHouse:
    """Tests for deleting a house (RBAC: ADMIN or STORE_MANAGER only)."""

    async def test_delete_house_forbidden_for_agent(
        self,
        test_client: AsyncClient,
        auth_headers: dict[str, str],  # AGENT role
        test_house: House,
    ):
        """AGENT role should receive 403 when trying to delete."""
        response = await test_client.delete(
            f"/api/v1/houses/{test_house.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403, response.text

    async def test_delete_house_success_as_admin(
        self,
        test_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        test_house: House,
    ):
        """ADMIN role should be able to delete and receive 204."""
        response = await test_client.delete(
            f"/api/v1/houses/{test_house.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 204, response.text

        # Verify it's actually gone
        get_resp = await test_client.get(
            f"/api/v1/houses/{test_house.id}",
            headers=admin_auth_headers,
        )
        assert get_resp.status_code == 404, get_resp.text

    async def test_delete_house_not_found(
        self,
        test_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ):
        """Should return 404 when house does not exist."""
        fake_id = uuid.uuid4()
        response = await test_client.delete(
            f"/api/v1/houses/{fake_id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404, response.text

    async def test_delete_house_requires_auth(
        self,
        test_client: AsyncClient,
        test_house: House,
    ):
        """Should return 401 without auth."""
        response = await test_client.delete(f"/api/v1/houses/{test_house.id}")
        assert response.status_code == 401, response.text
