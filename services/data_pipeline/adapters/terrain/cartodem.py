"""Adapter for ISRO CartoDEM (Cartosat-1 derived Indian DEM)."""

from typing import Any, Dict, List, Optional
import pandas as pd

from ..base import TerrainDataSource, BoundingBox
from ...common.types import CanonicalTerrainObservation


class CartoDemTerrainAdapter(TerrainDataSource):
    """Adapter for ISRO CartoDEM Version 3R (high accuracy Indian subcontinental DEM)."""

    @property
    def source_name(self) -> str:
        return "ISRO_CARTODEM"

    def validate_connection(self) -> bool:
        return True

    def fetch_elevation_model(
        self,
        bbox: BoundingBox
    ) -> Dict[str, Any]:
        return {
            "source": self.source_name,
            "elevation_min_m": 850.0,
            "elevation_max_m": 2400.0,
            "mean_slope_deg": 18.2,
            "mean_aspect_deg": 165.0,
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
                    metadata={"provider": "ISRO/NRSC", "version": "3R"},
                )
            )
        return results

    def parse_csv(self, file_path_or_buffer: Any) -> List[CanonicalTerrainObservation]:
        df = pd.read_csv(file_path_or_buffer)
        return self.parse_records(df.to_dict(orient="records"))
