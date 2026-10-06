"""Typed output contracts and serialization schemas for simulation results."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SpreadTimestepSnapshot:
    """Detailed hourly or sub-step state snapshot."""
    step_hour: int
    burned_area_ha: float
    spread_velocity_kmh: float
    spread_direction_deg: float
    intensity_mw: float
    boundary_polygon: Dict[str, Any]  # GeoJSON Polygon / MultiPolygon
    active_burning_cells: int = 0
    total_burned_cells: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to standard dictionary representation."""
        return {
            "step_hour": self.step_hour,
            "burned_area_ha": self.burned_area_ha,
            "spread_velocity_kmh": self.spread_velocity_kmh,
            "spread_direction_deg": self.spread_direction_deg,
            "intensity_mw": self.intensity_mw,
            "boundary_polygon": self.boundary_polygon,
            "active_burning_cells": self.active_burning_cells,
            "total_burned_cells": self.total_burned_cells,
        }

    def to_geojson_feature(self) -> Dict[str, Any]:
        """Convert snapshot boundary to GeoJSON Feature with properties."""
        return {
            "type": "Feature",
            "properties": {
                "step_hour": self.step_hour,
                "burned_area_ha": self.burned_area_ha,
                "spread_velocity_kmh": self.spread_velocity_kmh,
                "spread_direction_deg": self.spread_direction_deg,
                "intensity_mw": self.intensity_mw,
                "active_burning_cells": self.active_burning_cells,
            },
            "geometry": self.boundary_polygon,
        }


@dataclass
class SpreadSimulationSummary:
    """Summary metrics of complete simulation run."""
    simulation_id: str
    total_area_burned_ha: float
    duration_hours: int
    peak_spread_velocity_kmh: float
    final_spread_direction_deg: float
    timesteps_count: int
    engine_version: str


@dataclass
class SpreadSimulationOutput:
    """Container holding full simulation run and all hourly snapshots."""
    simulation_id: str
    total_area_burned_ha: float
    duration_hours: int
    peak_spread_velocity_kmh: float
    timesteps: List[SpreadTimestepSnapshot]
    engine_version: str = "spread-ca-v001"

    def to_dict(self) -> Dict[str, Any]:
        """Convert simulation output to dictionary representation."""
        return {
            "simulation_id": self.simulation_id,
            "total_area_burned_ha": self.total_area_burned_ha,
            "duration_hours": self.duration_hours,
            "peak_spread_velocity_kmh": self.peak_spread_velocity_kmh,
            "engine_version": self.engine_version,
            "timesteps": [ts.to_dict() for ts in self.timesteps],
        }

    def to_geojson(self) -> Dict[str, Any]:
        """Format as GeoJSON FeatureCollection of timestep perimeters."""
        return {
            "type": "FeatureCollection",
            "properties": {
                "simulation_id": self.simulation_id,
                "total_area_burned_ha": self.total_area_burned_ha,
                "duration_hours": self.duration_hours,
                "peak_spread_velocity_kmh": self.peak_spread_velocity_kmh,
                "engine_version": self.engine_version,
            },
            "features": [ts.to_geojson_feature() for ts in self.timesteps],
        }
