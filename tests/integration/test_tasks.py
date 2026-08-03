from httpx import AsyncClient


async def test_create_task(auth_client: AsyncClient):
    # 1. First, create a workspace
    ws_response = await auth_client.post(
        "/workspaces",
        json={"title": "Task Workspace", "description": "For testing tasks"},
    )
    ws_id = ws_response.json()["id"]

    # 2. Create a task in this workspace
    task_response = await auth_client.post(
        f"/workspaces/{ws_id}/tasks",
        json={
            "title": "First Test Task",
            "description": "Task description",
            "status": "todo",
            "priority": "high",
        },
    )

    assert task_response.status_code in (200, 201)
    data = task_response.json()
    assert data["title"] == "First Test Task"
    assert data["workspace_id"] == ws_id


async def test_update_task_status(auth_client: AsyncClient):
    # 1. Create a workspace
    ws_response = await auth_client.post(
        "/workspaces",
        json={
            "title": "Status Update Workspace",
            "description": "Testing status changes",
        },
    )
    ws_id = ws_response.json()["id"]

    # 2. Create a task
    task_response = await auth_client.post(
        f"/workspaces/{ws_id}/tasks",
        json={
            "title": "Task to update",
            "description": "Will change status",
            "status": "todo",
            "priority": "medium",
        },
    )
    task_id = task_response.json()["id"]

    # 3. Change task status
    update_response = await auth_client.patch(
        f"/workspaces/{ws_id}/tasks/{task_id}/status", json={"status": "in_progress"}
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "in_progress"
