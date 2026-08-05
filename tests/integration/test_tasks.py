import json

from httpx import AsyncClient
from httpx_ws import aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport

from app.main import app


async def test_create_task(auth_client: AsyncClient) -> None:
    # 1. Create workspace
    ws_response = await auth_client.post(
        "/workspaces",
        json={"title": "Task Workspace", "description": "For testing tasks"},
    )
    ws_id = ws_response.json()["id"]

    # Create task
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


async def test_get_tasks_list(auth_client: AsyncClient) -> None:
    ws_response = await auth_client.post(
        "/workspaces", json={"title": "List Workspace"}
    )
    ws_id = ws_response.json()["id"]

    # Create two tasks with different statuses
    await auth_client.post(
        f"/workspaces/{ws_id}/tasks",
        json={"title": "Task 1", "status": "todo", "priority": "low"},
    )
    await auth_client.post(
        f"/workspaces/{ws_id}/tasks",
        json={"title": "Task 2", "status": "done", "priority": "high"},
    )

    # Get all tasks
    get_all = await auth_client.get(f"/workspaces/{ws_id}/tasks")
    assert get_all.status_code == 200
    assert len(get_all.json()) == 2

    # Get tasks with filter by status
    get_filtered = await auth_client.get(f"/workspaces/{ws_id}/tasks?status=done")
    assert get_filtered.status_code == 200
    filtered_data = get_filtered.json()
    assert len(filtered_data) == 1
    assert filtered_data[0]["title"] == "Task 2"


async def test_update_task(auth_client: AsyncClient) -> None:
    ws_response = await auth_client.post(
        "/workspaces", json={"title": "Update Task WS"}
    )
    ws_id = ws_response.json()["id"]

    task_response = await auth_client.post(
        f"/workspaces/{ws_id}/tasks",
        json={"title": "Old Title", "status": "todo", "priority": "low"},
    )
    task_id = task_response.json()["id"]

    # Update task
    update_response = await auth_client.patch(
        f"/workspaces/{ws_id}/tasks/{task_id}",
        json={"title": "New Title", "priority": "high"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "New Title"
    assert update_response.json()["priority"] == "high"


async def test_update_task_status(auth_client: AsyncClient) -> None:
    ws_response = await auth_client.post(
        "/workspaces",
        json={
            "title": "Status Update Workspace",
            "description": "Testing status changes",
        },
    )
    ws_id = ws_response.json()["id"]

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

    update_response = await auth_client.patch(
        f"/workspaces/{ws_id}/tasks/{task_id}/status", json={"status": "in_progress"}
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "in_progress"


async def test_delete_task(auth_client: AsyncClient) -> None:
    ws_response = await auth_client.post(
        "/workspaces", json={"title": "Delete Task WS"}
    )
    ws_id = ws_response.json()["id"]

    task_response = await auth_client.post(
        f"/workspaces/{ws_id}/tasks",
        json={"title": "Task to delete", "status": "todo", "priority": "low"},
    )
    task_id = task_response.json()["id"]

    # Delete task
    delete_response = await auth_client.delete(f"/workspaces/{ws_id}/tasks/{task_id}")
    assert delete_response.status_code == 204

    # Check that task is deleted
    get_response = await auth_client.get(f"/workspaces/{ws_id}/tasks/{task_id}")
    assert get_response.status_code == 404


async def test_task_comments(auth_client: AsyncClient) -> None:
    ws_response = await auth_client.post("/workspaces", json={"title": "Comments WS"})
    ws_id = ws_response.json()["id"]

    task_response = await auth_client.post(
        f"/workspaces/{ws_id}/tasks",
        json={"title": "Task with comments", "status": "todo", "priority": "low"},
    )
    task_id = task_response.json()["id"]

    # 1. Add comment
    comment_resp = await auth_client.post(
        f"/workspaces/{ws_id}/tasks/{task_id}/comments",
        json={"text": "This is a test comment with @mention@example.com"},
    )
    assert comment_resp.status_code in (200, 201)
    comment_id = comment_resp.json()["id"]

    # 2. Get list of comments
    get_comments = await auth_client.get(
        f"/workspaces/{ws_id}/tasks/{task_id}/comments"
    )
    assert get_comments.status_code == 200
    assert len(get_comments.json()) == 1
    assert (
        get_comments.json()[0]["text"]
        == "This is a test comment with @mention@example.com"
    )

    # 3. Delete the comment (use the correct path without the workspace_id)
    delete_resp = await auth_client.delete(f"/tasks/{task_id}/comments/{comment_id}")
    assert delete_resp.status_code == 204

    get_comments_after = await auth_client.get(
        f"/workspaces/{ws_id}/tasks/{task_id}/comments"
    )
    assert len(get_comments_after.json()) == 0


async def test_websocket_task_status_notification(auth_client: AsyncClient) -> None:
    ws_response = await auth_client.post(
        "/workspaces",
        json={
            "title": "WS Status Workspace",
            "description": "Testing WebSocket status changes",
        },
    )
    ws_id = ws_response.json()["id"]

    task_response = await auth_client.post(
        f"/workspaces/{ws_id}/tasks",
        json={
            "title": "Task for WS test",
            "description": "Will trigger WS message",
            "status": "todo",
            "priority": "high",
        },
    )
    task_id = task_response.json()["id"]

    token = auth_client.headers["Authorization"].replace("Bearer ", "")
    ws_url = f"/ws?workspace_id={ws_id}&token={token}"

    async with (
        ASGIWebSocketTransport(app) as transport,
        AsyncClient(transport=transport, base_url="http://test") as ws_client,
        aconnect_ws(ws_url, client=ws_client) as ws,
    ):
        update_response = await auth_client.patch(
            f"/workspaces/{ws_id}/tasks/{task_id}/status",
            json={"status": "done"},
        )
        assert update_response.status_code == 200

        message_str = await ws.receive_text()
        message_data = json.loads(message_str)

        assert isinstance(message_data, dict)
        assert str(task_id) in message_str
        assert "done" in message_str


async def test_task_filters_and_errors(auth_client: AsyncClient) -> None:
    # Additional test for increased coverage: checking filters and 404 errors
    ws_response = await auth_client.post("/workspaces", json={"title": "Filter WS"})
    ws_id = ws_response.json()["id"]

    task_response = await auth_client.post(
        f"/workspaces/{ws_id}/tasks",
        json={"title": "Unique Searchable Task", "status": "todo", "priority": "high"},
    )
    task_id = task_response.json()["id"]

    # 1. Query with all possible filters (runs a large block of code in the repository)
    filters_resp = await auth_client.get(
        f"/workspaces/{ws_id}/tasks?status=todo&priority=high&search=Unique&my=true&sort=created_at&order=desc"
    )
    assert filters_resp.status_code == 200

    # 2. Getting a non-existent task (404)
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    not_found_resp = await auth_client.get(f"/workspaces/{ws_id}/tasks/{fake_uuid}")
    assert not_found_resp.status_code == 404

    # 3. Deleting a non-existent comment (404)
    del_comment_resp = await auth_client.delete(
        f"/tasks/{task_id}/comments/{fake_uuid}"
    )
    assert del_comment_resp.status_code == 404
