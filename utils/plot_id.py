

class PlotId:

    def __init__(self, id_: int):
        self.id = id_ & 0xFFFFFFFFFFFFFFFF

    @classmethod
    def from_hex(cls, s: str) -> "PlotId":
        return cls(int(s, 16))

    def to_hex(self) -> str:
        return f"{self.id:x}"

    def depth(self) -> int:
        n, d = self.id >> 24, 0
        while n:
            d += 1
            n >>= 12
        return d

    def split(self) -> list[int]:
        out = [self.id & 0xFFFFFF]
        n = self.id >> 24
        while n:
            out.append(n & 0xFFF)
            n >>= 12
        return out

    def parent(self) -> "PlotId | None":
        d = self.depth()
        if d == 0:
            return None
        mask = (1 << (24 + 12 * (d - 1))) - 1
        return PlotId(self.id & mask)

    def __str__(self) -> str:
        return self.to_hex()

    def __repr__(self) -> str:
        return f"PlotId(0x{self.to_hex()})"
