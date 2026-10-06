"""Adapter for ESA Sentinel-2 MSI multispectral surface reflectance products."""

from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional
import pandas as pd

from ..base import VegetationDataSource, BoundingBox
from ...common.types import CanonicalVegetationObservation


class SentinelVegetationAdapter(VegetationDataSource):
    """Adapter for Sentinel-2 MSI L2A BOA (Bottom-Of-Atmosphere) reflectance."""

    @property
    def source_name(self) -> str:
        return "SENTINEL_2"

    def validate_connection(self) -> bool:
        return True

    def fetch_vegetation_indices(
        self,
        bbox: BoundingBox,
        target_date: date
    ) -> Dict[str, Any]:
        return {
            "source": self.source_name,
            "target_date": target_date.isoformat(),
            "mean_ndvi": 0.42,
            "mean_ndwi": -0.18,
            "cloud_cover_pct": 5.0,
        }

    def parse_records(self, records: List[Dict[str, Any]]) -> List[CanonicalVegetationObservation]:
        """Parse Sentinel-2 records or band reflectances into canonical vegetation observations."""
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

            # Band calculations if raw reflectances provided: B4=Red, B8=NIR, B11=SWIR
            ndvi = None
            if "ndvi" in r and pd.notnull(r["ndvi"]):
                ndvi = float(r["ndvi"])
            elif "b8" in r and "b4" in r and pd.notnull(r["b8"]) and pd.notnull(r["b4"]):
                nir = float(r["b8"])
                red = float(r["b4"])
                if (nir + red) != 0:
                    ndvi = (nir - red) / (nir + red)

            ndwi = None
            if "ndwi" in r and pd.notnull(r["ndwi"]):
                ndwi = float(r["ndwi"])
            elif "b8" in r and "b11" in r and pd.notnull(r["b8"]) and pd.notnull(r["b11"]):
                nir = float(r["b8"])
                swir = float(r["b11"])
                if (nir + swir) != 0:
                    ndwi = (nir - swir) / (nir + swir)

            fuel_type = r.get("fuel_type", "DECIDUOUS_FOREST")
            cloud_pct = float(r.get("cloud_cover_pct", r.get("cloud_cover", 0.0)))

            results.append(
                CanonicalVegetationObservation(
                    source=self.source_name,
                    observation_time=dt,
                    latitude=lat,
                    longitude=lon,
                    ndvi=round(ndvi, 4) if ndvi is not None else None,
                    ndwi=round(ndwi, 4) if ndwi is not None else None,
                    fuel_type=fuel_type,
                    cloud_cover_pct=cloud_pct,
                    metadata={"tile": r.get("tile", "T44RKR"), "sensor": "MSI"},
                )
            )
        return results

    def parse_csv(self, file_path_or_buffer: Any) -> List[CanonicalVegetationObservation]:
        df = pd.read_csv(file_path_or_buffer)
        return self.parse_records(df.to_dict(orient="records"))
