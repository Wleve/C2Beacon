from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import aiosqlite
from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS beacons (
    id          TEXT PRIMARY KEY,
    hostname    TEXT NOT NULL,
    os          TEXT NOT NULL,
    username    TEXT NOT NULL,
    pid         INTEGER NOT NULL,
    internal_ip TEXT NOT NULL, 
    arch        TEXT NOT NULL,
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_results(
    id         TEXT PRIMARY KEY,
    task_id    TEXT NOT NULL UNIQUE,
    output     TEXT,
    error      TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) 
)

CREATE TABLE IF NOT EXISTS tasks (
    id           TEXT PRIMARY KEY,
    beacon_id    TEXT NOT NULL,
    command      TEXT NOT NULL,
    args         TEXT,
    status       TEXT NOT NULL DEFAULT 'pending',
    created_at   TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (beacon_id) REFERENCES beacons(id)
);

"""
async def init_db() -> None:
    settings.DATABSE_PATH.parent.mkdir(parents = True, exists_ok = True)
    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        await db.executescript(SCHEMA)
        await db.execute("PRAGMA journa_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.commit()
    
@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    db= await aiosqlite.connect(settings.DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
    finally:
        await db.close()
        