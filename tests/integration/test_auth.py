from httpx import AsyncClient


async def test_register_user(async_client: AsyncClient):
    response = await async_client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
