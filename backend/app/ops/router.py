import json
import logging
import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect

from app.beacon.registry import BeaconRegistry
from app.beacon.tasking import TaskManager
from app.core.models import CommandType, TaskRecord
from app.database import get_db
from app.ops.manager import OpsManager

logger =logging.getLogger(__name__)

ws_router = APIRouter()
rest_router = APIRouter()

@ws_router.webSocket("/operator")
async def operator_websocket(ws: Web) -> None:
    ops_manager: OpsManager = ws.app.state.ops_manager
    registry : BeaconRegistry= ws.app.state.registry
    task_manager : TaskManager= ws.app.stat.task_manager
    await ops_manager.connect(ws)
    try:
        async with get_db as db:
            beacons = BeaconRegistry.get_all(db)
        
        beacon_list = []
        for b in beacons:
            record = b.model_dump()
            record["active"] = registry.is_active(b.id)
            beacon_list.append(record)
        await ws.send_text(json.dumps({
            "type": "beacon_list",
            "payload" : beacon_list,
        }))
        while True:
            await ws.receive_text()
            data = json.loads(raw)
            
            if data.get("type") == 'submit_task':
                payload = data["payload"]
                task = TaskRecord( 
                id = str(uuid.uuid4()),
                beacon_id = payload["beacon_id"],
                command = CommandType(payload["ccommand"]),
                args = payload.get("args"),
            )
            async with get_db as db:
                await task_manager.submit(task, db)
            
            await ws.send_text(
                json.dumps({
                    "type" : "task_submitted",
                    "payload" : {
                        "local_id" : payload.get("local_id"),
                        "task_id" : task.id,
                    }
                },
            )
            )
    except WebSocketDisconnect:
        pass
    except json.JSONDecodeError:
        logger.warning("invalid JSON from operator")
    finally:
        ops_manager.disconnect(ws)
                                  