"""Spatial indexing and efficient point-in-cell / nearest-neighbor queries."""

import math
from typing import Any, Dict, List, Optional, Tuple
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from ..common.types import GridCellDefinition


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the great-circle distance between two points in meters."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class SpatialGridIndex:
    """Spatial index wrapping grid cells using Shapely's STRtree."""

    def __init__(self, cells: List[GridCellDefinition]):
        self.cells = cells
        self.cell_map: Dict[str, GridCellDefinition] = {c.cell_id: c for c in cells}
        self.geometries = [shape(c.geometry) for c in cells]
        self.tree = STRtree(self.geometries)

    def find_cell_for_point(self, latitude: float, longitude: float) -> Optional[GridCellDefinition]:
        """Find the grid cell containing the given latitude and longitude."""
        pt = Point(longitude, latitude)
        # Query candidates from tree
        candidates = self.tree.query(pt)
        for idx in candidates:
            geom = self.geometries[idx]
            if geom.contains(pt) or geom.touches(pt):
                return self.cells[idx]
        return None

    def find_nearest_cell(self, latitude: float, longitude: float) -> Optional[GridCellDefinition]:
        """Find the geometrically nearest cell centroid."""
        if not self.cells:
            return None
        pt = Point(longitude, latitude)
        nearest_idx = self.tree.nearest(pt)
        return self.cells[nearest_idx]

    def distance_to_nearest_point(
        self,
        lat: float,
        lon: float,
        points: List[Tuple[float, float]]
    ) -> Optional[float]:
        """Compute the minimum distance in meters from (lat, lon) to a list of (lat, lon) points."""
        if not points:
            return None
        min_dist = float("inf")
        for p_lat, p_lon in points:
            d = haversine_distance_meters(lat, lon, p_lat, p_lon)
            if d < min_dist:
                min_dist = d
        return min_dist
