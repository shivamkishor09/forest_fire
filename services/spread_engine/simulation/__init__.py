"""Simulation subpackage: grid, state, transitions, metrics, engine, runner."""

from .grid import FireGrid, SimulationGrid
from .state import GridStateBuffer
from .neighbourhood import MOORE_NEIGHBOURS, NeighbourOffset, get_neighbour_cells
from .transitions import TransitionEvaluator
from .boundary import extract_fire_boundary_geojson
from .metrics import (
    calculate_burned_area_ha,
    calculate_active_burning_cells,
    calculate_spread_velocity_kmh,
    calculate_dominant_spread_direction_deg,
    calculate_fire_intensity_mw,
)
from .timesteps import TimestepResult, SimulationResult
from .engine import SpreadSimulationEngine
from .runner import BaseSimulationRunner, CellularAutomataRunner

__all__ = [
    "FireGrid",
    "SimulationGrid",
    "GridStateBuffer",
    "MOORE_NEIGHBOURS",
    "NeighbourOffset",
    "get_neighbour_cells",
    "TransitionEvaluator",
    "extract_fire_boundary_geojson",
    "calculate_burned_area_ha",
    "calculate_active_burning_cells",
    "calculate_spread_velocity_kmh",
    "calculate_dominant_spread_direction_deg",
    "calculate_fire_intensity_mw",
    "TimestepResult",
    "SimulationResult",
    "SpreadSimulationEngine",
    "BaseSimulationRunner",
    "CellularAutomataRunner",
]
