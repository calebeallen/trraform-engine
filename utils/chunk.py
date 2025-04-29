import struct
from io import BytesIO

def decode_chunk(data: bytes) -> dict[str, bytes]:
    
    result = {}

    if data is None:
        return result

    cursor = 0
    total_len = len(data)

    while cursor < total_len:
        if cursor + 2 > total_len:
            raise ValueError("Not enough bytes to read key length")

        # Read 2-byte key length
        key_len = struct.unpack_from('<H', data, cursor)[0]
        cursor += 2

        if cursor + key_len > total_len:
            raise ValueError("Not enough bytes to read key")

        # Read key
        key_bytes = data[cursor:cursor + key_len]
        key = key_bytes.decode('utf-8')
        cursor += key_len

        if cursor + 4 > total_len:
            raise ValueError("Not enough bytes to read value length")

        # Read 4-byte value length
        value_len = struct.unpack_from('<I', data, cursor)[0]
        cursor += 4

        if cursor + value_len > total_len:
            raise ValueError("Not enough bytes to read value")

        # Read value
        value = data[cursor:cursor + value_len]
        cursor += value_len

        result[key] = value

    return result


def encode_chunk(mapping: dict[str, bytes]) -> bytes:
    buf = BytesIO()

    for k, v in mapping.items():
        key_bytes = k.encode('utf-8')
        key_len = len(key_bytes)
        value_len = len(v)

        buf.write(struct.pack('<H', key_len))  # 2-byte key length
        buf.write(key_bytes)                   # key bytes
        buf.write(struct.pack('<I', value_len)) # 4-byte value length
        buf.write(v)                            # value bytes

    return buf.getvalue()
