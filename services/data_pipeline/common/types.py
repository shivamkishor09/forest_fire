"""Canonical domain models, schemas, and pipeline artifacts for Phase 4."""

from datetime import datetime, date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DataLeakageError(Exception):
    """Raised when an observation timestamp exceeds the prediction reference time (T_obs > T_ref)."""
    pass


class BoundingBox(BaseModel):
    """Geographic bounding box in EPSG:4326."""
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    @field_validator("max_lat")
    @classmethod
    def validate_latitude_order(cls, v: float, info) -> float:
        min_lat = info.data.get("min_lat")
        if min_lat is not None and v <= min_lat:
            raise ValueError(f"max_lat ({v}) must be greater than min_lat ({min_lat})")
        return v

    @field_validator("max_lon")
    @classmethod
    def validate_longitude_order(cls, v: float, info) -> float:
        min_lon = info.data.get("min_lon")
        if min_lon is not None and v <= min_lon:
            raise ValueError(f"max_lon ({v}) must be greater than min_lon ({min_lon})")
        return v


class CanonicalFireObservation(BaseModel):
    """Canonical active fire / thermal anomaly detection."""
    source: str = Field(..., description="Provider/instrument, e.g. MODIS, VIIRS, INSAT_3D")
    detection_time: datetime = Field(..., description="UTC detection timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    confidence_pct: float = Field(..., ge=0.0, le=100.0, description="Confidence percentage")
    frp_mw: Optional[float] = Field(None, ge=0.0, description="Fire Radiative Power in MW")
    brightness_temp_k: Optional[float] = Field(None, ge=150.0, le=600.0, description="Brightness temperature in Kelvin")
    scan_track: Optional[str] = Field(None, description="Instrument scan / track resolution")
    geometry: Dict[str, Any] = Field(default_factory=dict, description="GeoJSON Point")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific metadata")

    def model_post_init(self, __context: Any) -> None:
        if not self.geometry:
            self.geometry = {
                "type": "Point",
                "coordinates": [round(self.longitude, 6), round(self.latitude, 6)],
            }


class CanonicalWeatherObservation(BaseModel):
    """Canonical gridded or station meteorological observation."""
    source: str = Field(..., description="Provider, e.g. ERA5, IMD")
    timestamp: datetime = Field(..., description="UTC observation timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    temperature_c: Optional[float] = Field(None, ge=-60.0, le=70.0, description="Ambient surface temperature in Celsius")
    relative_humidity_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity %")
    wind_speed_ms: Optional[float] = Field(None, ge=0.0, le=100.0, description="Wind speed in m/s")
    wind_direction_deg: Optional[float] = Field(None, ge=0.0, le=360.0, description="Wind direction azimuth (0=N, 90=E)")
    precipitation_mm: Optional[float] = Field(None, ge=0.0, description="Accumulated rainfall in mm")
    u_wind_ms: Optional[float] = Field(None, description="Zonal wind component m/s")
    v_wind_ms: Optional[float] = Field(None, description="Meridional wind component m/s")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalVegetationObservation(BaseModel):
    """Canonical vegetation index and fuel observation."""
    source: str = Field(..., description="Provider/sensor, e.g. SENTINEL_2, BHUVAN")
    observation_time: datetime = Field(..., description="UTC observation timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    ndvi: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Normalized Difference Vegetation Index")
    ndwi: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Normalized Difference Water Index")
    fuel_type: Optional[str] = Field(None, description="Fuel/LULC classification category")
    cloud_cover_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalTerrainObservation(BaseModel):
    """Canonical topographical elevation, slope, and aspect observation."""
    source: str = Field(..., description="Provider/sensor, e.g. CARTODEM, SRTM_30M")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    elevation_m: float = Field(..., ge=-500.0, le=9000.0, description="Elevation in meters AMSL")
    slope_deg: float = Field(..., ge=0.0, le=90.0, description="Slope gradient in degrees")
    aspect_deg: float = Field(..., ge=0.0, le=360.0, description="Aspect azimuth in degrees (0=N, 90=E)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GridCellDefinition(BaseModel):
    """Standardized 500m x 500m spatial partition cell definition."""
    cell_id: str = Field(..., description="Deterministic unique identifier (e.g. CELL_0012_0034)")
    region_id: str = Field(..., description="Associated forest division / region ID")
    cell_code: str = Field(..., description="Human-readable cell code")
    centroid_lat: float = Field(..., ge=-90.0, le=90.0)
    centroid_lon: float = Field(..., ge=-180.0, le=180.0)
    geometry: Dict[str, Any] = Field(..., description="GeoJSON Polygon boundary in EPSG:4326")
    resolution_meters: int = Field(500, description="Cell spatial dimension in meters")
    row_idx: int = Field(0, description="Spatial grid row index")
    col_idx: int = Field(0, description="Spatial grid column index")


class CanonicalFeatureRecord(BaseModel):
    """
    Standardized model-ready feature row aligned to a 500m grid cell for reference date T.
    Guaranteed to contain zero future data (T_obs <= T_ref).
    """
    grid_cell_id: str
    cell_code: str
    region_id: str
    reference_date: str = Field(..., description="YYYY-MM-DD prediction date")
    centroid_lat: float
    centroid_lon: float

    # Topographical features
    elevation_m: Optional[float] = None
    slope_deg: Optional[float] = None
    aspect_deg: Optional[float] = None
    aspect_sin: Optional[float] = None
    aspect_cos: Optional[float] = None

    # Fuel / Vegetation features
    fuel_type: str = Field(default="UNKNOWN", description="Standardized fuel class")
    ndvi: Optional[float] = None
    ndwi: Optional[float] = None

    # Weather features (reference window T_obs <= T_ref)
    temperature_c: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    wind_u_ms: Optional[float] = None
    wind_v_ms: Optional[float] = None
    precipitation_24h_mm: Optional[float] = None
    precipitation_7d_mm: Optional[float] = None

    # Fire Weather Index
    fwi: Optional[float] = None

    # Historical fire features (strictly <= T_ref)
    fire_count_7d: int = Field(default=0)
    fire_count_30d: int = Field(default=0)
    days_since_last_fire: Optional[float] = None
    dist_to_recent_fire_m: Optional[float] = None

    # Target label: strictly separated. Optional, only populated for training/eval datasets
    # Evaluates T_ref < T_fire <= T_ref + 24h
    target_fire_next_24h: Optional[int] = Field(default=None, ge=0, le=1)

    # Imputation and quality auditing
    imputed_fields: List[str] = Field(default_factory=list)
    quality_flag: str = Field(default="CLEAN", description="CLEAN, PARTIALLY_IMPUTED, DEGRADED")


class DataManifest(BaseModel):
    """Reproducible manifest recording pipeline run provenance and dataset metadata."""
    run_id: str
    created_at: str
    region_id: str
    region_name: str
    reference_date: str
    lookback_days: int
    resolution_meters: int
    grid_cells_count: int
    feature_records_count: int
    feature_columns: List[str]
    target_column: Optional[str] = None
    sources_ingested: Dict[str, Dict[str, Any]]
    output_files: Dict[str, str]
    pipeline_version: str = "phase-04-v1.0"


class QualityReport(BaseModel):
    """Automated data quality and missingness report."""
    run_id: str
    created_at: str
    total_records: int
    clean_records_pct: float
    imputed_records_pct: float
    feature_completeness_pct: Dict[str, float]
    imputed_fields_breakdown: Dict[str, int]
    out_of_bound_counts: Dict[str, int]
    summary_statistics: Dict[str, Dict[str, float]]
    warnings: List[str] = Field(default_factory=list)
