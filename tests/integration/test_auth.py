from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import UserFactory


async def test_register_user(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/auth/register",
        json={
            "email": "new_test_user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new_test_user@example.com"


async def test_register_existing_user(
    async_client: AsyncClient, session: AsyncSession
) -> None:
    user = UserFactory.build(email="existing@example.com")
    session.add(user)
    await session.commit()

    response = await async_client.post(
        "/auth/register",
        json={
            "email": "existing@example.com",
            "password": "StrongPassword123!",
            "full_name": "Existing User",
        },
    )
    assert response.status_code == 400


async def test_login_user(async_client: AsyncClient, session: AsyncSession) -> None:
    user = UserFactory.build(email="login_test@example.com")
    session.add(user)
    await session.commit()

    response = await async_client.post(
        "/auth/login",
        data={"username": "login_test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"


async def test_login_wrong_password(
    async_client: AsyncClient, session: AsyncSession
) -> None:
    user = UserFactory.build(email="wrong_pass@example.com")
    session.add(user)
    await session.commit()

    response = await async_client.post(
        "/auth/login",
        data={"username": "wrong_pass@example.com", "password": "wrongpassword!"},
    )
    assert response.status_code == 401


async def test_login_non_existent_user(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401
