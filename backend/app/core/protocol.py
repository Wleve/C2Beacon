import binascii
import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.encoding import decode, encode

class MessageType(StrEnum):
    REGISTER  = "REGISTER"
    HEARTBEAT = "HEARTBEAT"
    TASK = "TASK"
    RESULT = "RESULT"
    ERROR = "ERROR"

class Message(BaseModel):
    type: MessageType
    payload: dict[str, Any]
    
def pack(message: Message, key: str) -> str:
    rawJson = message.model_dump_json
    return encode(rawJson, key)

def unpack(raw: str, key: str) -> str:
    try:
        decodedJson = decode(raw, key)
        data = json.loads(decodedJson)
        return Message.model_validate(data)
    except (
        json.JSONDecodeError,
        ValidationError,
        UnicodeDecodeError,
        binascii.Error
    ) as exc:
        raise ValueError(f"Invalid protocol message: {exc}")
        
   