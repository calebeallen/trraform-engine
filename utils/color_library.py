import numpy as np
from utils.constants import PLOT_COUNT

HPB = 8          
HUES = HPB * 6
GRID_SIZE = 25          
WHITE = np.array([1., 1., 1.], dtype=np.float32)
BLACK = np.array([0., 0., 0.], dtype=np.float32)
OFFSET = PLOT_COUNT + 1

# pre-allocate a *list* first (unknown final length)
palette = []

def lerp(t: float, c1: np.ndarray, c2: np.ndarray) -> np.ndarray:
    return (1.0 - t) * c1 + t * c2

gs2 = GRID_SIZE * GRID_SIZE
for i in range(gs2):
    palette.append(lerp(i / gs2, WHITE, BLACK))

c1i = c2i = 0
for i in range(6):
    c1 = np.zeros(3, dtype=np.float32)
    c2 = np.zeros(3, dtype=np.float32)
    c1[c1i % 3] = 1
    c2[c2i % 3] = 1

    if i & 1:
        c1i += 1
        c1[c1i % 3] = 1
    else:
        c2i += 1
        c2[c2i % 3] = 1

    for h in range(HPB):
        base = lerp(h / HPB, c1, c2)
        for s in range(GRID_SIZE):
            for r in range(GRID_SIZE):
                x = (r + 1) / (GRID_SIZE + 2)
                y = s / GRID_SIZE
                palette.append(
                    lerp(
                        y,
                        lerp(x, base, WHITE),
                        lerp(x, BLACK, BLACK),
                    )
                )

_colors = np.vstack(palette).astype(np.float32)   # immutable lookup table

def get_color(idx: int) -> np.ndarray:
    idx = idx - OFFSET
    if idx < 0:
        return None
    return _colors[idx]

#pre condition: only valid idxs passed in (i.e > PLOT_COUNT)
def get_color_vec(idxs: np.ndarray) -> np.ndarray:

    # gpt sub offset (PLOT_COUNT + 1)
    return _colors[idxs - OFFSET]
