from httpx import AsyncClient


async def test_create_workspace(auth_client: AsyncClient):
    response = await auth_client.post(
        "/workspaces",
        json={"title": "Test Workspace", "description": "A workspace for testing"},
    )

    assert response.status_code in (200, 201)

    data = response.json()
    assert data["title"] == "Test Workspace"
    assert "id" in data
