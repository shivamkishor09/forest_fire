"""Typed input schemas for cellular automata fire spread simulation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np

from .config import SimulationInput, EnvironmentalConditions
from .enums import FuelClass
from ..common.exceptions import IgnitionOutsideGridError


@dataclass
class IgnitionPoint:
    """Geographical ignition coordinate."""
    lat: float
    lon: float
    row: Optional[int] = None
    col: Optional[int] = None


@dataclass
class WindCondition:
    """Meteorological wind vector."""
    speed_ms: float
    direction_deg: float  # Meteorological FROM direction (0=N, 90=E, 180=S, 270=W)

    @property
    def heading_deg(self) -> float:
        """Compass heading towards which the wind blows."""
        return (self.direction_deg + 180.0) % 360.0


@dataclass
class TerrainCondition:
    """Uniform or default terrain characteristics."""
    slope_deg: float = 0.0
    aspect_deg: float = 180.0  # South-facing default
    elevation_m: float = 1000.0
    fuel_type: str = FuelClass.BROADLEAF_MODERATE_LITTER.value


@dataclass
class TerrainGridData:
    """Spatially varying 2D terrain rasters."""
    elevation_matrix: Optional[np.ndarray] = None
    slope_matrix: Optional[np.ndarray] = None
    aspect_matrix: Optional[np.ndarray] = None
    fuel_matrix: Optional[np.ndarray] = None


@dataclass
class SpreadSimulationInput:
    """Comprehensive input payload driving the Cellular Automata spread engine."""
    simulation_id: str
    ignition: IgnitionPoint
    duration_hours: int = 12
    grid_rows: int = 50
    grid_cols: int = 50
    grid_resolution_meters: float = 500.0
    wind: Optional[WindCondition] = None
    terrain: TerrainCondition = field(default_factory=TerrainCondition)
    terrain_grid: Optional[TerrainGridData] = None
    deterministic: bool = True
    random_seed: Optional[int] = 42

    @classmethod
    def from_legacy_input(cls, sim_input: SimulationInput) -> "SpreadSimulationInput":
        """Convert a Phase 1 SimulationInput into a SpreadSimulationInput."""
        wind = None
        if sim_input.environment is not None:
            wind = WindCondition(
                speed_ms=sim_input.environment.wind_speed_ms,
                direction_deg=sim_input.environment.wind_direction_deg,
            )

        terrain = TerrainCondition(
            slope_deg=sim_input.slope_deg if sim_input.slope_deg is not None else 0.0,
            aspect_deg=sim_input.aspect_deg if sim_input.aspect_deg is not None else 180.0,
            elevation_m=sim_input.elevation_m if sim_input.elevation_m is not None else 1000.0,
            fuel_type=sim_input.fuel_type if sim_input.fuel_type is not None else FuelClass.BROADLEAF_MODERATE_LITTER.value,
        )

        return cls(
            simulation_id=sim_input.simulation_id,
            ignition=IgnitionPoint(lat=sim_input.ignition_lat, lon=sim_input.ignition_lon),
            duration_hours=sim_input.duration_hours,
            grid_rows=sim_input.grid_rows,
            grid_cols=sim_input.grid_cols,
            grid_resolution_meters=float(sim_input.grid_resolution_meters),
            wind=wind,
            terrain=terrain,
            deterministic=sim_input.deterministic,
            random_seed=sim_input.random_seed,
        )
