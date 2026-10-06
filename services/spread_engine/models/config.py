"""Simulation configuration and input contracts."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class EnvironmentalConditions:
    """Atmospheric conditions driving spread velocity and heading."""
    wind_speed_ms: float
    wind_direction_deg: float  # Meteorological direction: 0 = North, 90 = East, 180 = South, 270 = West
    ambient_temperature_c: float = 30.0
    relative_humidity_pct: float = 25.0


@dataclass
class SimulationInput:
    """Input parameters to initialize a 12-hour simulation session."""
    simulation_id: str
    ignition_lat: float
    ignition_lon: float
    duration_hours: int = 12
    grid_resolution_meters: int = 500
    grid_rows: int = 50
    grid_cols: int = 50
    environment: Optional[EnvironmentalConditions] = None
    use_physics_layer: bool = False
    slope_deg: Optional[float] = None
    aspect_deg: Optional[float] = None
    fuel_type: Optional[str] = None
    elevation_m: Optional[float] = None
    custom_terrain_grid: Optional[Dict[str, Any]] = None
    deterministic: bool = True
    random_seed: Optional[int] = 42
