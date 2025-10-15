from __future__ import annotations
import zlib
import numpy as np

MAGIC = b"VSTEGO1"
HEADER_LEN = len(MAGIC) + 4 + 4  # magic + u32 length + u32 crc32

def u32_to_bytes(x: int) -> bytes:
    return x.to_bytes(4, "big")

def u32_from_bytes(b: bytes) -> int:
    return int.from_bytes(b, "big")

def payload_from_text(text: str) -> bytes:
    data = text.encode("utf-8")
    crc = zlib.crc32(data) & 0xFFFFFFFF
    return MAGIC + u32_to_bytes(len(data)) + u32_to_bytes(crc) + data

def parse_payload(raw: bytes) -> str:
    if len(raw) < HEADER_LEN:
        raise ValueError("Payload trop court")
    magic = raw[: len(MAGIC)]
    if magic != MAGIC:
        raise ValueError("Magic incorrect")
    msg_len = u32_from_bytes(raw[len(MAGIC): len(MAGIC)+4])
    crc = u32_from_bytes(raw[len(MAGIC)+4: len(MAGIC)+8])
    data = raw[len(MAGIC)+8 : len(MAGIC)+8+msg_len]
    if len(data) != msg_len:
        raise ValueError("Longueur incohérente")
    if (zlib.crc32(data) & 0xFFFFFFFF) != crc:
        raise ValueError("CRC32 invalide (message altéré)")
    return data.decode("utf-8")

def bytes_to_bits(b: bytes) -> np.ndarray:
    arr = np.frombuffer(b, dtype=np.uint8)
    bits = np.unpackbits(arr)
    return bits  # shape (len*8,)

def bits_to_bytes(bits: np.ndarray) -> bytes:
    # Ensure length multiple of 8
    pad = (-len(bits)) % 8
    if pad:
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
    arr = np.packbits(bits.astype(np.uint8))
    return arr.tobytes()
