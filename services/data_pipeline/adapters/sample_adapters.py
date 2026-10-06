"""Concrete sample adapter implementations for Phase 1 verification."""

from datetime import datetime, date
from typing import Any, Dict, List, Optional
from .base import (
    BoundingBox,
    FireDataSource,
    WeatherDataSource,
    VegetationDataSource,
    TerrainDataSource,
)


class SampleModisFireAdapter(FireDataSource):
    """Sample adapter for NASA/MODIS active fire products (MCD14DL)."""

    @property
    def source_name(self) -> str:
        return "NASA_MODIS"

    def validate_connection(self) -> bool:
        return True

    def fetch_active_fires(
        self,
        bbox: BoundingBox,
        start_time: datetime,
        end_time: datetime,
        min_confidence: float = 50.0
    ) -> List[Dict[str, Any]]:
        # Phase 1 scaffolding: returns structured contract sample
        return [
            {
                "source": self.source_name,
                "latitude": (bbox.min_lat + bbox.max_lat) / 2.0,
                "longitude": (bbox.min_lon + bbox.max_lon) / 2.0,
                "detected_at": start_time.isoformat(),
                "confidence_pct": 85.0,
                "frp_mw": 32.5,
                "brightness_temp_k": 340.2,
            }
        ]


class SampleImdWeatherAdapter(WeatherDataSource):
    """Sample adapter for IMD (India Meteorological Department) weather observations."""

    @property
    def source_name(self) -> str:
        return "IMD_API"

    def validate_connection(self) -> bool:
        return True

    def fetch_weather_grid(
        self,
        bbox: BoundingBox,
        target_date: date,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        return {
            "source": self.source_name,
            "target_date": target_date.isoformat(),
            "metrics": {
                "temperature_c": 31.5,
                "relative_humidity_pct": 28.0,
                "wind_speed_ms": 6.2,
                "wind_direction_deg": 220.0,
                "precipitation_mm": 0.0,
            }
        }


class SampleSentinelVegetationAdapter(VegetationDataSource):
    """Sample adapter for ESA Sentinel-2 multispectral vegetation reflectance."""

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


class SampleCartoDemTerrainAdapter(TerrainDataSource):
    """Sample adapter for CartoDEM / SRTM 30m Digital Elevation Models."""

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
