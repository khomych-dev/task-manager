from httpx_ws.transport import ASGIWebSocketTransport
from app.main import app
import json
from httpx_ws import aconnect_ws
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


async def test_websocket_task_status_notification(auth_client: AsyncClient):
    # 1. Create a workspace
    ws_response = await auth_client.post(
        "/workspaces",
        json={
            "title": "WS Status Workspace",
            "description": "Testing WebSocket status changes",
        },
    )
    ws_id = ws_response.json()["id"]

    # 2. Create a task
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

    # 3. Extract JWT token
    token = auth_client.headers["Authorization"].replace("Bearer ", "")
    ws_url = f"/ws?workspace_id={ws_id}&token={token}"

    # 4. Use async with for proper initialization of transport and client
    async with ASGIWebSocketTransport(app) as transport:
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as ws_client:
            # 5. Connect to WebSocket
            async with aconnect_ws(ws_url, client=ws_client) as ws:
                # Change task status through the main REST client
                update_response = await auth_client.patch(
                    f"/workspaces/{ws_id}/tasks/{task_id}/status",
                    json={"status": "done"},
                )
                assert update_response.status_code == 200

                # Wait for message
                message_str = await ws.receive_text()
                message_data = json.loads(message_str)

                # Check that we received a valid JSON object and it contains the required data
                assert isinstance(message_data, dict)
                assert str(task_id) in message_str
                assert "done" in message_str
