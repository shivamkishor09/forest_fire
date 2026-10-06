"""Moore 8-neighbourhood spatial relationships and directional offsets."""

from dataclasses import dataclass
import math
from typing import List, Tuple

SQRT_2: float = math.sqrt(2.0)
INV_SQRT_2: float = 1.0 / SQRT_2


@dataclass(frozen=True)
class NeighbourOffset:
    """Relative offset and directional characteristics to an adjacent cell."""
    name: str
    delta_r: int
    delta_c: int
    angle_deg: float      # Compass heading (0=N, 90=E, 180=S, 270=W)
    distance_ratio: float # 1.0 for orthogonal, sqrt(2) for diagonal
    weight: float         # 1.0 for orthogonal, 1/sqrt(2) for diagonal


# Canonical 8-neighbour Moore neighbourhood indexed clockwise from North
MOORE_NEIGHBOURS: List[NeighbourOffset] = [
    NeighbourOffset("NORTH", -1, 0, 0.0, 1.0, 1.0),
    NeighbourOffset("NORTH_EAST", -1, 1, 45.0, SQRT_2, INV_SQRT_2),
    NeighbourOffset("EAST", 0, 1, 90.0, 1.0, 1.0),
    NeighbourOffset("SOUTH_EAST", 1, 1, 135.0, SQRT_2, INV_SQRT_2),
    NeighbourOffset("SOUTH", 1, 0, 180.0, 1.0, 1.0),
    NeighbourOffset("SOUTH_WEST", 1, -1, 225.0, SQRT_2, INV_SQRT_2),
    NeighbourOffset("WEST", 0, -1, 270.0, 1.0, 1.0),
    NeighbourOffset("NORTH_WEST", -1, -1, 315.0, SQRT_2, INV_SQRT_2),
]


def get_neighbour_cells(
    r: int,
    c: int,
    max_rows: int,
    max_cols: int,
) -> List[Tuple[int, int, NeighbourOffset]]:
    """
    Return all valid in-bounds neighbours of cell (r, c) along with directional metadata.
    """
    neighbours: List[Tuple[int, int, NeighbourOffset]] = []
    for offset in MOORE_NEIGHBOURS:
        nr = r + offset.delta_r
        nc = c + offset.delta_c
        if 0 <= nr < max_rows and 0 <= nc < max_cols:
            neighbours.append((nr, nc, offset))
    return neighbours
