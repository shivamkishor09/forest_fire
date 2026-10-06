"""Strict 24-hour future fire target label generation (T_ref < T_fire <= T_ref + 24h)."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from ..common.types import CanonicalFireObservation, GridCellDefinition
from ..grid.indexing import SpatialGridIndex


class TargetLabeler:
    """
    Computes binary 24-hour future fire occurrence label strictly separated from feature records.
    Label = 1 if a fire is detected in cell within (T_ref, T_ref + 24h], else 0.
    """

    def __init__(self, reference_time: datetime, target_window_hours: int = 24):
        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)
        self.reference_time = reference_time
        self.target_window_hours = target_window_hours
        self.window_end = reference_time + timedelta(hours=target_window_hours)

    def extract_future_fires(
        self,
        all_fires: List[CanonicalFireObservation]
    ) -> List[CanonicalFireObservation]:
        """Extract only fires that fall in the strictly future window (T_ref, T_ref + 24h]."""
        future_fires = []
        for fire in all_fires:
            t = fire.detection_time
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if self.reference_time < t <= self.window_end:
                future_fires.append(fire)
        return future_fires

    def compute_labels_for_cells(
        self,
        cells: List[GridCellDefinition],
        all_fires: List[CanonicalFireObservation],
        spatial_index: SpatialGridIndex,
    ) -> Dict[str, int]:
        """
        Compute binary target label (0 or 1) for each cell_id.
        """
        future_fires = self.extract_future_fires(all_fires)
        fires_by_cell = defaultdict(int)

        for fire in future_fires:
            cell = spatial_index.find_cell_for_point(fire.latitude, fire.longitude)
            if cell is not None:
                fires_by_cell[cell.cell_id] += 1
            else:
                nearest = spatial_index.find_nearest_cell(fire.latitude, fire.longitude)
                if nearest is not None:
                    fires_by_cell[nearest.cell_id] += 1

        labels: Dict[str, int] = {}
        for cell in cells:
            count = fires_by_cell.get(cell.cell_id, 0)
            labels[cell.cell_id] = 1 if count > 0 else 0

        return labels
