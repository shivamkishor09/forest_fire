"""Historical fire features: temporal frequencies and spatial proximity."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from ..common.types import CanonicalFireObservation, GridCellDefinition
from ..grid.indexing import haversine_distance_meters


class FireHistoryExtractor:
    """Computes spatial proximity and temporal frequencies for historical fires up to T_ref."""

    def __init__(self, reference_time: datetime):
        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)
        self.reference_time = reference_time

    def compute_proximity_to_recent_fires(
        self,
        cell: GridCellDefinition,
        historical_fires: List[CanonicalFireObservation],
        max_lookback_days: int = 14,
    ) -> Optional[float]:
        """
        Compute distance in meters from the cell centroid to the nearest active fire
        detected within the past max_lookback_days up to reference_time.
        """
        cutoff = self.reference_time - timedelta(days=max_lookback_days)
        min_dist = float("inf")

        for fire in historical_fires:
            t = fire.detection_time
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)

            # Strict guard: cutoff <= t <= reference_time
            if cutoff <= t <= self.reference_time:
                d = haversine_distance_meters(
                    cell.centroid_lat, cell.centroid_lon,
                    fire.latitude, fire.longitude
                )
                if d < min_dist:
                    min_dist = d

        return round(min_dist, 1) if min_dist != float("inf") else None
