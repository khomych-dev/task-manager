from uuid import UUID

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.config import settings
from app.websocket_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    workspace_id: UUID = Query(...),
    token: str = Query(...),
) -> None:
    # Validate JWT token
    try:
        # Using the SECRET_KEY from the config
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except jwt.PyJWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connect to workspace
    await manager.connect(websocket, workspace_id)
    try:
        while True:
            # The client is mostly just listening, but we're keeping the connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, workspace_id)
