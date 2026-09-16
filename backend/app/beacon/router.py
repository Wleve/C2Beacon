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
        await ws.send_text(pack(message, settings.XOR_KEY))
        
    

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
                await task_manager.store_result(tr)
            if hasattr(ops_broadcast, 'broadcast'):
                await ops_broadcast.broadcast(
                    {
                        "type" : "task.result",
                        "payload": tr.model_dump(),
                    }
                )
        elif MessageType == 'HEARTBEAT':
            async with get_db as db:
                await registry.update_last_seen(beacon_id)
            if hasattr(ops_broadcast, 'broadcast'):
                    await ops_broadcast.broadcast(
                        {
                            "type" : "heartbeat",
                            "payload": {"id": beacon_id},
                        }
                    )

@router.websocket("/beacon")
async def beacon_websocket(ws: WebSocket) -> None:
    await ws.accept
        
    registry :BeaconRegistry = ws.app.state.registry
    task_manager: TaskManager = ws.app.state.ask_manager
    ops_manager = ws.app.state.ops_manager    
    beacon_id = str | None = None
    
    try:
        raw = await ws.receive_text
        message = unpack(raw, settings.XOR_KEY)
        if MessageType != MessageType.REGISTER:
            await ws.close(code = 4001, reason ='Error 4001, excpected register message')
            return
        meta = BeaconMeta.model_validate(message.payload)
        beacon_id = message.payload.get("id", str(uuid.uuid4()))
    
        async with get_db as db:
            await registry.register(beacon_id, meta, ws, db)
        logger.info("Beacon registered with beacon ID: %s (%s)", (beacon_id, meta.hostname))
    
        if hasattr(ops_manager, 'broadcast'):
            beacon_record = meta.model_dump()
            beacon_record['id'] = beacon_id
        
            await ops_manager.broadcast(
            {
                "type" : "beacon_connected",
                "payload": beacon_record,
            })
        
        send_task = asyncio.create_task(_send_tasks(ws, beacon_id, task_manager,))
        receive_msg= asyncio.create_task(_receive_messages(ws, beacon_id, registry,task_manager, ops_manager))
        

    
        done, pending = await asyncio.wait(
            [send_task, receive_msg],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        for task in done:
            if (exc := task.exception()) is not None:
                raise exc
        

    except WebSocketDisconnect:
        logger.info("WebSocket Disconnected for Beacon %s (%s)", (beacon_id, meta))
    
    except ValueError:
        logger.info("Protocol error for Beacon %s (%s)", (beacon_id, meta))
        
    
    finally:
        if beacon_id:
            async with get_db as db:
                await registry.unregister(beacon_id, db)
            task_manager.remove_queue(beacon_id)
        
        if hasattr(ops_manager, "broadcast"):
            await ops_manager.broadcast(
                        {
                            "type" : "beacon_disconnected",
                            "payload": {"id" : beacon_id}
                        })
    



