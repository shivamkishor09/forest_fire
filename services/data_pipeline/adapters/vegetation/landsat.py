"""Adapter for USGS/NASA Landsat-8/9 OLI surface reflectance."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from ..base import VegetationDataSource, BoundingBox
from ...common.types import CanonicalVegetationObservation


class LandsatVegetationAdapter(VegetationDataSource):
    """Adapter for Landsat-8/9 Operational Land Imager (OLI)."""

    @property
    def source_name(self) -> str:
        return "LANDSAT_8"

    def validate_connection(self) -> bool:
        return True

    def fetch_vegetation_indices(
        self,
        bbox: BoundingBox,
        target_date: Any
    ) -> Dict[str, Any]:
        return {
            "source": self.source_name,
            "target_date": str(target_date),
            "mean_ndvi": 0.45,
            "mean_ndwi": -0.15,
            "cloud_cover_pct": 8.0,
        }

    def parse_records(self, records: List[Dict[str, Any]]) -> List[CanonicalVegetationObservation]:
        results: List[CanonicalVegetationObservation] = []
        for r in records:
            lat = float(r["latitude"])
            lon = float(r["longitude"])

            if "observation_time" in r:
                dt = pd.to_datetime(r["observation_time"]).to_pydatetime()
            elif "target_date" in r:
                dt = pd.to_datetime(r["target_date"]).to_pydatetime()
            else:
                dt = datetime.now(timezone.utc)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            # Landsat 8: Band 4 = Red, Band 5 = NIR, Band 6 = SWIR1
            ndvi = None
            if "ndvi" in r and pd.notnull(r["ndvi"]):
                ndvi = float(r["ndvi"])
            elif "b5" in r and "b4" in r and pd.notnull(r["b5"]) and pd.notnull(r["b4"]):
                nir = float(r["b5"])
                red = float(r["b4"])
                if (nir + red) != 0:
                    ndvi = (nir - red) / (nir + red)

            ndwi = None
            if "ndwi" in r and pd.notnull(r["ndwi"]):
                ndwi = float(r["ndwi"])
            elif "b5" in r and "b6" in r and pd.notnull(r["b5"]) and pd.notnull(r["b6"]):
                nir = float(r["b5"])
                swir = float(r["b6"])
                if (nir + swir) != 0:
                    ndwi = (nir - swir) / (nir + swir)

            results.append(
                CanonicalVegetationObservation(
                    source=self.source_name,
                    observation_time=dt,
                    latitude=lat,
                    longitude=lon,
                    ndvi=round(ndvi, 4) if ndvi is not None else None,
                    ndwi=round(ndwi, 4) if ndwi is not None else None,
                    fuel_type=r.get("fuel_type", "PINE_FOREST"),
                    cloud_cover_pct=float(r.get("cloud_cover_pct", 0.0)),
                    metadata={"path_row": r.get("path_row", "146/039")},
                )
            )
        return results
