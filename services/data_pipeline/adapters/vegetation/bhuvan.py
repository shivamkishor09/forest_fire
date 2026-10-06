"""Adapter for ISRO Bhuvan LULC (Land Use / Land Cover 1:50,000) Indian Fuel Categories."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from ..base import VegetationDataSource, BoundingBox
from ...common.types import CanonicalVegetationObservation


# Standard fuel classification map for Indian forests (FSI / Rothermel / ISRO classes)
BHUVAN_FUEL_MAPPING = {
    1: "SAL_DECIDUOUS",       # Tropical Moist Deciduous (Sal-dominated)
    2: "DRY_DECIDUOUS",       # Tropical Dry Deciduous (Teak / Mixed)
    3: "CHIR_PINE",           # Subtropical Pine (Pinus roxburghii - high resin/combustibility)
    4: "TEMPERATE_CONIFER",   # Himalayan Moist/Dry Temperate (Deodar, Spruce, Fir)
    5: "SCRUB_GRASSLAND",     # Subtropical Scrub & Degraded Savanna
    6: "SHRUB_HEATH",         # Alpine & Subalpine Scrub
    7: "AGRICULTURE_CROPLAND",# Crop fields / stubble residue
    8: "WATER_RIVER",         # Rivers / water bodies (non-burnable)
    9: "BARREN_ROCK_SNOW",    # Bare soil / rock / permanent snow (non-burnable)
}


class BhuvanVegetationAdapter(VegetationDataSource):
    """Adapter for ISRO Bhuvan Indian Land Use / Land Cover & fuel type datasets."""

    @property
    def source_name(self) -> str:
        return "ISRO_BHUVAN"

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
            "dominant_fuel_type": "CHIR_PINE",
            "mean_ndvi": 0.52,
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

            # Map numeric class to standardized fuel category
            raw_class = r.get("lulc_class", r.get("fuel_class_id"))
            if raw_class in BHUVAN_FUEL_MAPPING:
                fuel_str = BHUVAN_FUEL_MAPPING[raw_class]
            else:
                fuel_str = str(r.get("fuel_type", "CHIR_PINE"))

            ndvi = float(r["ndvi"]) if "ndvi" in r and pd.notnull(r["ndvi"]) else None
            ndwi = float(r["ndwi"]) if "ndwi" in r and pd.notnull(r["ndwi"]) else None

            results.append(
                CanonicalVegetationObservation(
                    source=self.source_name,
                    observation_time=dt,
                    latitude=lat,
                    longitude=lon,
                    ndvi=ndvi,
                    ndwi=ndwi,
                    fuel_type=fuel_str,
                    cloud_cover_pct=0.0,
                    metadata={"provider": "NRSC/ISRO", "scale": "1:50,000"},
                )
            )
        return results
