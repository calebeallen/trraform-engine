
import struct
from io import BytesIO

def decode_chunk(data: bytes) -> dict[int, bytes]:

    result = {}

    if data is None:
        return result
    
    cursor = 0
    total_len = len(data)

    while cursor < total_len:
        if cursor + 4 + 8 > total_len:
            raise ValueError("Not enough bytes to read length + key")

        # Read 4-byte body length
        body_len = struct.unpack_from('<I', data, cursor)[0]
        cursor += 4

        # Read 8-byte key
        key = struct.unpack_from('<Q', data, cursor)[0]
        cursor += 8

        if cursor + body_len > total_len:
            raise ValueError("Body length exceeds remaining data")

        # Read body
        body = data[cursor:cursor + body_len]
        cursor += body_len

        result[key] = body

    return result


def encode_chunk(mapping: dict[int, bytes]) -> bytes:

    buf = BytesIO()

    for k, v in mapping.items():
        body_len = len(v)
        buf.write(struct.pack('<I', body_len))  # 4-byte body length
        buf.write(struct.pack('<Q', k))         # 8-byte key
        buf.write(v)                             # body content

    return buf.getvalue()
