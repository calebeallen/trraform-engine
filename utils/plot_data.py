
import json
import struct
from typing import List

class PlotData:
   

    def __init__(
        self,  
        name: str,
        description: str,
        link: str,
        link_title: str,
        owner: str,
        verified: bool,
        build_data: List[int]
    ):
        self.name = name
        self.description = description
        self.link = link
        self.link_title = link_title
        self.owner = owner
        self.verified = verified
        self.build_data = build_data

    def encode(self) -> bytes:
        j = {
            "ver": 0,
            "name": self.name,
            "desc": self.description,
            "link": self.link,
            "linkTitle": self.link_title,
            "owner": self.owner,
            "verified": self.verified,
        }
        json_bytes = json.dumps(j, separators=(",", ":")).encode()
        build_bytes = struct.pack(f"<{len(self.build_data)}H", *self.build_data)

        # allocate bytes
        out = bytearray(len(json_bytes) + len(build_bytes) + 8)

        # set json part
        struct.pack_into("<I", out, 0, len(json_bytes))
        out[4 : 4 + len(json_bytes)] = json_bytes
        p = 4 + len(json_bytes)

        # set build data part
        struct.pack_into("<I", out, p, len(build_bytes))
        out[p + 4 : p + 4 + len(build_bytes)] = build_bytes
        
        return bytes(out)

    @classmethod
    def decode(cls, data: bytes) -> "PlotData":

        if len(data) < 8:
            raise ValueError("bad data")

        json_len = struct.unpack_from("<I", data, 0)[0]
        json_end = 4 + json_len
        if len(data) < json_end + 4:
            raise ValueError("bad data")

        jb = data[4:json_end]
        build_len = struct.unpack_from("<I", data, json_end)[0]
        build_end = json_end + 4 + build_len
        if len(data) < build_end:
            raise ValueError("bad data")

        build_bytes = data[json_end + 4 : build_end]
        j = json.loads(jb)
        build = list(struct.unpack(f"<{len(build_bytes) // 2}H", build_bytes))

        return cls(
            name=j["name"],
            description=j["desc"],
            link=j["link"],
            link_title=j["linkTitle"],
            verified=j["verified"],
            owner=j["owner"],
            build_data=build,
        )
