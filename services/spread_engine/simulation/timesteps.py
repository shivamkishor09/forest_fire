"""Simulation timestep and complete result output contracts."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TimestepResult:
    """Snapshot metrics and spatial boundary for a single simulation hour."""
    step_hour: int
    burned_area_ha: float
    spread_velocity_kmh: float
    spread_direction_deg: float
    intensity_mw: float
    boundary_polygon: Dict[str, Any]  # GeoJSON Polygon or MultiPolygon
    active_burning_cells: int = 0
    total_burned_cells: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert timestep to serializable dictionary."""
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
        """Convert timestep perimeter to GeoJSON Feature."""
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
class SimulationResult:
    """Complete 12-hour simulation result container."""
    simulation_id: str
    total_area_burned_ha: float
    duration_hours: int
    peak_spread_velocity_kmh: float
    timesteps: List[TimestepResult]
    engine_version: str = "spread-ca-v001"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result container to serializable dictionary."""
        return {
            "simulation_id": self.simulation_id,
            "total_area_burned_ha": self.total_area_burned_ha,
            "duration_hours": self.duration_hours,
            "peak_spread_velocity_kmh": self.peak_spread_velocity_kmh,
            "engine_version": self.engine_version,
            "timesteps": [ts.to_dict() for ts in self.timesteps],
        }

    def to_geojson(self) -> Dict[str, Any]:
        """Format as GeoJSON FeatureCollection of all timestep perimeters."""
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
