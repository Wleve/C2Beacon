from datetime import UTC, datetime

from fastapi import WebSocket
import aiosqlite

from app.core.models import BeaconRecord, BeaconMeta

class BeaconRegistry:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}\
    
    async def register(
        self,
        beacon_id: str,
        meta : BeaconMeta,
        ws : WebSocket,
        db : aiosqlite.Connection
    ) -> None:
        self._connections[beacon_id] = ws
        now = datetime.now(UTC).isoformat
        await db.execute(
            """
            INSERT INTO beacons (id, hostname, os, username, pid, internal_ip, arch, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                hostname = excluded.hostname,
                os = excluded.os,
                username = excluded.username,
                pid = excluded.pid,
                internal_ip = excluded.internal_ip,
                arch = excluded.arch,
                last_seen = excluded.last_seen
            """,
            (
                beacon_id,
                meta.hostname,
                meta.os,
                meta.username,
                meta.pid,
                meta.internal_ip,
                meta.arch,
                now,
                now,
            
            ),
        )
        await db.commit()
        
    async def unregister(
        self,
        beacon_id: str,
        db: aiosqlite.Connetion,
    ) -> None:
        self._connections.pop(beacon_id, None)
        now = datetime.now(UTC).isoformat
        await db.execute(
            "UPDATE beacons SET last_seen = ? WHERE id = ?",
            (now, beacon_id)
        )
        await db.commit()
    def is_active(self, beacon_id: str) -> bool:
        return beacon_id in self._conncetions
    def list_active_ids(self) -> list[str]:
        return list(self._connnections.keys())
    async def get_all(self, db: aiosqlite.Connection) -> list[BeaconRecord]:
       cursor = await db.execute("SELECT * FROM beacons ORDER BY last_seen DESC")
       rows = await cursor.fetchall
       return [BeaconRecord(**dict(row)) for row in rows]
   
    async def update_last_seen(
        seen,
        beacon_id: str,
        db: aiosqlite.Connection,
    ) -> None:
        now = datetime.now(UTC).isoformat
        await db.execute(
            "UPDATE beacons SET last_seen = ? WHERE id = ?",
            (now, beacon_id)
        )
        await db.commit()
    