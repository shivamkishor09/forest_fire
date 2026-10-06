"""Adapter for NASA SRTM 30m Global Digital Elevation Model."""

from typing import Any, Dict, List, Optional
import pandas as pd

from ..base import TerrainDataSource, BoundingBox
from ...common.types import CanonicalTerrainObservation


class SrtmTerrainAdapter(TerrainDataSource):
    """Adapter for NASA Shuttle Radar Topography Mission (SRTM) 1 arc-second (~30m) DEM."""

    @property
    def source_name(self) -> str:
        return "NASA_SRTM_30M"

    def validate_connection(self) -> bool:
        return True

    def fetch_elevation_model(
        self,
        bbox: BoundingBox
    ) -> Dict[str, Any]:
        return {
            "source": self.source_name,
            "elevation_min_m": 600.0,
            "elevation_max_m": 2800.0,
            "mean_slope_deg": 19.5,
            "mean_aspect_deg": 180.0,
        }

    def parse_records(self, records: List[Dict[str, Any]]) -> List[CanonicalTerrainObservation]:
        results: List[CanonicalTerrainObservation] = []
        for r in records:
            lat = float(r["latitude"])
            lon = float(r["longitude"])
            elev = float(r.get("elevation_m", r.get("elevation", 0.0)))
            slope = float(r.get("slope_deg", r.get("slope", 0.0)))
            aspect = float(r.get("aspect_deg", r.get("aspect", 0.0)))

            results.append(
                CanonicalTerrainObservation(
                    source=self.source_name,
                    latitude=lat,
                    longitude=lon,
                    elevation_m=elev,
                    slope_deg=min(max(slope, 0.0), 90.0),
                    aspect_deg=min(max(aspect, 0.0), 360.0),
                    metadata={"resolution": "30m", "void_filled": True},
                )
            )
        return results

    def parse_csv(self, file_path_or_buffer: Any) -> List[CanonicalTerrainObservation]:
        df = pd.read_csv(file_path_or_buffer)
        return self.parse_records(df.to_dict(orient="records"))
