import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import UserFactory


@pytest.fixture
async def auth_client(async_client: AsyncClient, session: AsyncSession) -> AsyncClient:
    # Generate a user in memory and save it to the database
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    # Authorize to get the token
    response = await async_client.post(
        "/auth/login", data={"username": user.email, "password": "password123"}
    )
    token = response.json()["access_token"]

    # Set the default token for this client
    async_client.headers.update({"Authorization": f"Bearer {token}"})
    return async_client


async def test_create_workspace(auth_client: AsyncClient):
    response = await auth_client.post(
        "/workspaces",
        json={"title": "Test Workspace", "description": "A workspace for testing"},
    )

    assert response.status_code in (200, 201)

    data = response.json()
    assert data["title"] == "Test Workspace"
    assert "id" in data
