"""Shared domain data contracts for Forest Fire Platform."""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskClass(str, Enum):
    """Categorical fire susceptibility classification."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class SimulationStatus(str, Enum):
    """Lifecycle status of a 12-hour simulation job."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FireSource(str, Enum):
    """Origin sensor of active fire detection."""
    MODIS = "MODIS"
    VIIRS = "VIIRS"
    INSAT_3D = "INSAT_3D"
    GROUND_REPORT = "GROUND_REPORT"


@dataclass(frozen=True)
class GeoPoint:
    """WGS 84 Point representation [longitude, latitude]."""
    latitude: float
    longitude: float

    def to_geojson(self) -> Dict[str, Any]:
        return {
            "type": "Point",
            "coordinates": [self.longitude, self.latitude]
        }


@dataclass
class RegionContract:
    """Canonical forest division representation."""
    id: str
    code: str
    name: str
    state: str
    area_sqkm: float
    boundary: Dict[str, Any]
    created_at: Optional[datetime] = None


@dataclass
class GridCellContract:
    """Standardized 500m x 500m spatial partition."""
    id: str
    region_id: str
    cell_code: str
    centroid: Dict[str, Any]
    geometry: Dict[str, Any]
    resolution_meters: int = 500
    elevation_m: Optional[float] = None
    slope_deg: Optional[float] = None
    aspect_deg: Optional[float] = None
    fuel_type: Optional[str] = None


@dataclass
class FireEventContract:
    """Satellite thermal anomaly detection."""
    id: str
    source: FireSource
    detected_at: datetime
    location: Dict[str, Any]
    confidence_pct: float
    brightness_temp_k: Optional[float] = None
    frp_mw: Optional[float] = None
    grid_cell_id: Optional[str] = None


@dataclass
class EnvironmentalObservationContract:
    """Environmental and meteorological observation."""
    id: str
    grid_cell_id: str
    observation_time: datetime
    temperature_c: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    precipitation_mm: Optional[float] = None
    ndvi: Optional[float] = None
    ndwi: Optional[float] = None
    fwi: Optional[float] = None


@dataclass
class RiskPredictionContract:
    """24-Hour fire risk prediction."""
    grid_cell_id: str
    probability: float
    risk_class: RiskClass
    model_version: str
    id: Optional[str] = None
    region_id: Optional[str] = None
    valid_for_date: Optional[date] = None
    generated_at: Optional[datetime] = None


@dataclass
class SimulationTimestepContract:
    """1-Hour fire spread timestep snapshot."""
    simulation_id: str
    hour: int
    burned_area: float
    spread_velocity: float
    spread_direction: float
    intensity: float
    boundary: Dict[str, Any]


@dataclass
class SimulationContract:
    """12-Hour fire spread simulation session."""
    id: str
    region_id: str
    ignition_point: Dict[str, Any]
    ignition_time: datetime
    duration_hours: int = 12
    status: SimulationStatus = SimulationStatus.PENDING
    total_area_burned_ha: float = 0.0
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
