from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Invitation, WorkspaceMember
from tests.factories import UserFactory


async def test_create_workspace(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/workspaces",
        json={"title": "Test Workspace", "description": "A workspace for testing"},
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["title"] == "Test Workspace"
    assert "id" in data


async def test_get_user_workspaces(auth_client: AsyncClient) -> None:
    await auth_client.post("/workspaces", json={"title": "Workspace 1"})
    await auth_client.post("/workspaces", json={"title": "Workspace 2"})

    response = await auth_client.get("/workspaces")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 2
    titles = [ws["title"] for ws in data]
    assert "Workspace 1" in titles
    assert "Workspace 2" in titles


async def test_get_workspace_by_id(auth_client: AsyncClient) -> None:
    create_resp = await auth_client.post("/workspaces", json={"title": "Specific WS"})
    ws_id = create_resp.json()["id"]

    response = await auth_client.get(f"/workspaces/{ws_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Specific WS"


async def test_update_workspace(auth_client: AsyncClient) -> None:
    create_resp = await auth_client.post("/workspaces", json={"title": "Old Title"})
    ws_id = create_resp.json()["id"]

    update_resp = await auth_client.patch(
        f"/workspaces/{ws_id}",
        json={"title": "New Title", "description": "Updated description"},
    )
    assert update_resp.status_code == 200

    get_resp = await auth_client.get(f"/workspaces/{ws_id}")
    assert get_resp.json()["title"] == "New Title"
    assert get_resp.json()["description"] == "Updated description"


async def test_delete_workspace(auth_client: AsyncClient) -> None:
    create_resp = await auth_client.post("/workspaces", json={"title": "To Delete"})
    ws_id = create_resp.json()["id"]

    delete_resp = await auth_client.delete(f"/workspaces/{ws_id}")
    assert delete_resp.status_code == 204

    get_resp = await auth_client.get(f"/workspaces/{ws_id}")
    # After deletion, the user loses access, and the workspace disappears
    assert get_resp.status_code in (403, 404)


async def test_workspace_members_lifecycle(
    auth_client: AsyncClient, session: AsyncSession
) -> None:
    create_resp = await auth_client.post("/workspaces", json={"title": "Team WS"})
    ws_id = create_resp.json()["id"]

    # Create another user and add to DB
    user2 = UserFactory.build(email="teammate@example.com")
    session.add(user2)
    await session.commit()
    await session.refresh(user2)

    # Simulate invitation acceptance: add member directly to DB
    member = WorkspaceMember(workspace_id=ws_id, user_id=user2.id, role="viewer")
    session.add(member)
    await session.commit()

    # 1. Get the list of members
    members_resp = await auth_client.get(f"/workspaces/{ws_id}/members")
    assert members_resp.status_code == 200
    assert len(members_resp.json()) == 2

    # 2. Update member role
    update_role_resp = await auth_client.patch(
        f"/workspaces/{ws_id}/members/{user2.id}", json={"role": "admin"}
    )
    assert update_role_resp.status_code == 200
    assert update_role_resp.json()["role"] == "admin"

    # 3. Remove member
    remove_resp = await auth_client.delete(f"/workspaces/{ws_id}/members/{user2.id}")
    assert remove_resp.status_code == 204

    members_resp_after = await auth_client.get(f"/workspaces/{ws_id}/members")
    assert len(members_resp_after.json()) == 1


async def test_invite_and_accept_workflow(
    auth_client: AsyncClient, async_client: AsyncClient, session: AsyncSession
) -> None:
    create_resp = await auth_client.post("/workspaces", json={"title": "Invite WS"})
    ws_id = create_resp.json()["id"]

    invite_resp = await auth_client.post(
        f"/workspaces/{ws_id}/invite",
        json={"email": "invited@example.com", "role": "member"},
    )
    assert invite_resp.status_code == 204

    # Get invitation token from DB to accept
    stmt = select(Invitation).where(Invitation.workspace_id == ws_id)
    result = await session.execute(stmt)
    invitation = result.scalars().first()
    assert invitation is not None

    # Register and log in the invited user (simulate their client)
    user2 = UserFactory.build(email="invited@example.com")
    session.add(user2)
    await session.commit()
    await session.refresh(user2)

    login_resp = await async_client.post(
        "/auth/login", data={"username": user2.email, "password": "password123"}
    )
    token2 = login_resp.json()["access_token"]
    async_client.headers.update({"Authorization": f"Bearer {token2}"})

    # Invited user accepts the invitation
    accept_resp = await async_client.post(
        f"/workspaces/invitations/{invitation.token}/accept"
    )
    assert accept_resp.status_code == 204

    # Check that the invited user appears in the list of members
    members_resp = await auth_client.get(f"/workspaces/{ws_id}/members")
    user_ids = [m["user_id"] for m in members_resp.json()]
    assert str(user2.id) in user_ids
