import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class OpsManager:
    def __init__(self):
        self._connections: set[WebSocket] = set()
    
    async def connect(self, ws: WebSocket) -> None:
        await ws.accept
        self._connections.add(ws)
        logger.info("Operator connected (%d total)", len(self._connections))
    
    async def disconnect(self, ws) -> None:
        self._connections.discard(ws)
        logger.info("Operator disconnected (%d remaining)", len(self._connections))
    async def broadcast(self, ws)-> None:
        stale: list[WebSocket] =[]
        payload = json.dumps(event)

        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except(ConnectionError, RuntimeError):
                stale.append(ws)
            
        for ws in stale:
            self._connections.discard(ws)
            
    @property
    def connection_count(self) -> int:
        return len(self._connections)
    