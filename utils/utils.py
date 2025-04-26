
import struct
import numpy as np


def i2p(idx, size):

    s2 = size * size
    return [ idx % size, int(idx / s2), int( (idx % s2 ) / size ) ]


def i2p_vec(idxs: np.ndarray, size: int) -> np.ndarray:

    idxs = np.asarray(idxs, dtype=np.int64)

    s2 = size * size
    x  = idxs % size
    y  = idxs // s2
    z  = (idxs % s2) // size

    return np.stack((x, y, z), axis=1).astype(np.float64)


def expand(compressed):

    expanded = []
    value = None

    for i in range(2, len(compressed)):
        if (compressed[i] & 1) == 1:
            value = compressed[i] >> 1
            expanded.append(value)
        else:
            repeat = compressed[i] >> 1
            for _ in range(repeat):
                expanded.append(value)
    
    return expanded


