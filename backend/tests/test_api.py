"""Tests for API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "naijavibecheck"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NaijaVibeCheck"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_create_celebrity(client: AsyncClient, sample_celebrity_data):
    """Test creating a new celebrity."""
    response = await client.post("/api/v1/celebrities", json=sample_celebrity_data)
    assert response.status_code == 201
    data = response.json()
    assert data["instagram_username"] == sample_celebrity_data["instagram_username"]
    assert data["full_name"] == sample_celebrity_data["full_name"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_celebrity(client: AsyncClient, sample_celebrity_data):
    """Test creating a duplicate celebrity fails."""
    # Create first
    await client.post("/api/v1/celebrities", json=sample_celebrity_data)

    # Try to create duplicate
    response = await client.post("/api/v1/celebrities", json=sample_celebrity_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_celebrities(client: AsyncClient, sample_celebrity_data):
    """Test listing celebrities."""
    # Create a celebrity first
    await client.post("/api/v1/celebrities", json=sample_celebrity_data)

    response = await client.get("/api/v1/celebrities")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_celebrity(client: AsyncClient, sample_celebrity_data):
    """Test getting a specific celebrity."""
    # Create first
    create_response = await client.post("/api/v1/celebrities", json=sample_celebrity_data)
    celebrity_id = create_response.json()["id"]

    # Get by ID
    response = await client.get(f"/api/v1/celebrities/{celebrity_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["instagram_username"] == sample_celebrity_data["instagram_username"]


@pytest.mark.asyncio
async def test_update_celebrity(client: AsyncClient, sample_celebrity_data):
    """Test updating a celebrity."""
    # Create first
    create_response = await client.post("/api/v1/celebrities", json=sample_celebrity_data)
    celebrity_id = create_response.json()["id"]

    # Update
    update_data = {"scrape_priority": 10}
    response = await client.patch(f"/api/v1/celebrities/{celebrity_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["scrape_priority"] == 10


@pytest.mark.asyncio
async def test_delete_celebrity(client: AsyncClient, sample_celebrity_data):
    """Test deleting a celebrity."""
    # Create first
    create_response = await client.post("/api/v1/celebrities", json=sample_celebrity_data)
    celebrity_id = create_response.json()["id"]

    # Delete
    response = await client.delete(f"/api/v1/celebrities/{celebrity_id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/v1/celebrities/{celebrity_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_stats(client: AsyncClient):
    """Test dashboard statistics endpoint."""
    response = await client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "celebrities" in data
    assert "posts" in data
    assert "content" in data


@pytest.mark.asyncio
async def test_content_queue(client: AsyncClient):
    """Test content queue endpoint."""
    response = await client.get("/api/v1/content/queue")
    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    assert "approved" in data
    assert "published" in data
