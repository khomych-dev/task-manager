from typing import Any
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # Stores active connections: dict[workspace_id, set[WebSocket]]
        self.active_connections: dict[UUID, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workspace_id: UUID) -> None:
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = set()
        self.active_connections[workspace_id].add(websocket)

    def disconnect(self, websocket: WebSocket, workspace_id: UUID) -> None:
        if workspace_id in self.active_connections:
            self.active_connections[workspace_id].discard(websocket)
            if not self.active_connections[workspace_id]:
                del self.active_connections[workspace_id]

    async def broadcast_to_workspace(
        self, workspace_id: UUID, message: dict[str, Any]
    ) -> None:
        if workspace_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[workspace_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # If the transmission failed (for example, the client disconnected), mark it for deletion
                    dead_connections.add(connection)

            for dead in dead_connections:
                self.disconnect(dead, workspace_id)


manager = ConnectionManager()
