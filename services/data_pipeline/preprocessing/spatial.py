"""Spatial normalization and 500m x 500m grid resampling interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SpatialResampler(ABC):
    """Abstract resampler for harmonizing heterogeneous rasters onto the 500m common grid."""

    def __init__(self, target_resolution_meters: int = 500):
        self.target_resolution_meters = target_resolution_meters

    @abstractmethod
    def resample_raster_to_grid(self, raster_path: str, grid_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Resample source raster array to 500m grid cells."""
        pass
