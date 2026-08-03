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


async def test_login_user(async_client: AsyncClient):
    # First, let's create a user for this test
    await async_client.post(
        "/auth/register",
        json={
            "email": "login_test@example.com",
            "password": "strongpassword123",
            "full_name": "Login Test User",
        },
    )

    # Try to log in (here we use data and username)
    response = await async_client.post(
        "/auth/login",
        data={"username": "login_test@example.com", "password": "strongpassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(async_client: AsyncClient):
    # Try to log in with the wrong password (use data)
    response = await async_client.post(
        "/auth/login",
        data={"username": "login_test@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401
