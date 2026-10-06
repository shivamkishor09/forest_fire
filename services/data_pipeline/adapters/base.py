"""Abstract base interfaces and data source contracts for external adapters."""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from ..common.types import (
    BoundingBox as PydanticBoundingBox,
    CanonicalFireObservation,
    CanonicalWeatherObservation,
    CanonicalVegetationObservation,
    CanonicalTerrainObservation,
)


@dataclass
class BoundingBox:
    """Geographic bounding box in EPSG:4326."""
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def to_pydantic(self) -> PydanticBoundingBox:
        return PydanticBoundingBox(
            min_lon=self.min_lon,
            min_lat=self.min_lat,
            max_lon=self.max_lon,
            max_lat=self.max_lat,
        )

    def contains(self, lat: float, lon: float) -> bool:
        return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon


class BaseDataSource(ABC):
    """Abstract base class for all external data sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source provider."""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Check availability/credentials of the data source."""
        pass


class FireDataSource(BaseDataSource):
    """Interface for active fire / thermal anomaly satellite data."""

    @abstractmethod
    def fetch_active_fires(
        self,
        bbox: BoundingBox,
        start_time: datetime,
        end_time: datetime,
        min_confidence: float = 50.0
    ) -> List[Dict[str, Any]]:
        """Fetch active fire detections within geographic extent and time window."""
        pass

    def fetch_canonical_fires(
        self,
        bbox: BoundingBox,
        start_time: datetime,
        end_time: datetime,
        min_confidence: float = 50.0
    ) -> List[CanonicalFireObservation]:
        """Fetch active fires mapped into CanonicalFireObservation entities."""
        raw_list = self.fetch_active_fires(bbox, start_time, end_time, min_confidence)
        canonical_list = []
        for raw in raw_list:
            canonical_list.append(
                CanonicalFireObservation(
                    source=raw.get("source", self.source_name),
                    detection_time=raw.get("detected_at") or raw.get("detection_time") or datetime.now(),
                    latitude=raw["latitude"],
                    longitude=raw["longitude"],
                    confidence_pct=raw.get("confidence_pct", 50.0),
                    frp_mw=raw.get("frp_mw"),
                    brightness_temp_k=raw.get("brightness_temp_k"),
                    scan_track=raw.get("scan_track"),
                    metadata=raw.get("metadata", {}),
                )
            )
        return canonical_list


class WeatherDataSource(BaseDataSource):
    """Interface for meteorological observations and numerical forecasts."""

    @abstractmethod
    def fetch_weather_grid(
        self,
        bbox: BoundingBox,
        target_date: date,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Fetch meteorological metrics (temperature, humidity, wind, precipitation)."""
        pass

    def fetch_canonical_weather(
        self,
        bbox: BoundingBox,
        target_date: date,
        variables: Optional[List[str]] = None
    ) -> List[CanonicalWeatherObservation]:
        """Fetch weather observations mapped into CanonicalWeatherObservation entities."""
        raw = self.fetch_weather_grid(bbox, target_date, variables)
        metrics = raw.get("metrics", {})
        dt = datetime.combine(target_date, datetime.min.time())
        center_lat = (bbox.min_lat + bbox.max_lat) / 2.0
        center_lon = (bbox.min_lon + bbox.max_lon) / 2.0
        return [
            CanonicalWeatherObservation(
                source=raw.get("source", self.source_name),
                timestamp=dt,
                latitude=center_lat,
                longitude=center_lon,
                temperature_c=metrics.get("temperature_c"),
                relative_humidity_pct=metrics.get("relative_humidity_pct"),
                wind_speed_ms=metrics.get("wind_speed_ms"),
                wind_direction_deg=metrics.get("wind_direction_deg"),
                precipitation_mm=metrics.get("precipitation_mm", 0.0),
                metadata=raw,
            )
        ]


class VegetationDataSource(BaseDataSource):
    """Interface for multispectral optical satellite vegetation/fuel imagery."""

    @abstractmethod
    def fetch_vegetation_indices(
        self,
        bbox: BoundingBox,
        target_date: date
    ) -> Dict[str, Any]:
        """Fetch surface reflectance indices (NDVI, NDWI, land cover)."""
        pass

    def fetch_canonical_vegetation(
        self,
        bbox: BoundingBox,
        target_date: date
    ) -> List[CanonicalVegetationObservation]:
        """Fetch vegetation observations mapped into CanonicalVegetationObservation entities."""
        raw = self.fetch_vegetation_indices(bbox, target_date)
        dt = datetime.combine(target_date, datetime.min.time())
        center_lat = (bbox.min_lat + bbox.max_lat) / 2.0
        center_lon = (bbox.min_lon + bbox.max_lon) / 2.0
        return [
            CanonicalVegetationObservation(
                source=raw.get("source", self.source_name),
                observation_time=dt,
                latitude=center_lat,
                longitude=center_lon,
                ndvi=raw.get("mean_ndvi") or raw.get("ndvi"),
                ndwi=raw.get("mean_ndwi") or raw.get("ndwi"),
                fuel_type=raw.get("fuel_type", "DECIDUOUS_FOREST"),
                cloud_cover_pct=raw.get("cloud_cover_pct", 0.0),
                metadata=raw,
            )
        ]


class TerrainDataSource(BaseDataSource):
    """Interface for Digital Elevation Models (DEM)."""

    @abstractmethod
    def fetch_elevation_model(
        self,
        bbox: BoundingBox
    ) -> Dict[str, Any]:
        """Fetch elevation, slope gradient, and aspect rasters."""
        pass

    def fetch_canonical_terrain(
        self,
        bbox: BoundingBox
    ) -> List[CanonicalTerrainObservation]:
        """Fetch terrain observations mapped into CanonicalTerrainObservation entities."""
        raw = self.fetch_elevation_model(bbox)
        center_lat = (bbox.min_lat + bbox.max_lat) / 2.0
        center_lon = (bbox.min_lon + bbox.max_lon) / 2.0
        mean_elev = (raw.get("elevation_min_m", 0.0) + raw.get("elevation_max_m", 0.0)) / 2.0
        return [
            CanonicalTerrainObservation(
                source=raw.get("source", self.source_name),
                latitude=center_lat,
                longitude=center_lon,
                elevation_m=mean_elev,
                slope_deg=raw.get("mean_slope_deg", 0.0),
                aspect_deg=raw.get("mean_aspect_deg", 0.0),
                metadata=raw,
            )
        ]
