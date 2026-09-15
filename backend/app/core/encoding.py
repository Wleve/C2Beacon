import base64

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b^key[i%len(key)] for i, b in enumerate(data))

def encode(payload: str, key: str) -> str:
    raw = payload.encode("utf-8")
    xored = xor_bytes(raw)
    return base64.b64encode(xored).decode(ascii)

def decode(payload: str, key: str) -> str:
    xored = base64.b64decode(payload)
    raw = xor_bytes(xored)
    return raw.decode("utf-8")
    