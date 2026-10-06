"""Simulation metrics calculation: burned area, spread velocity, direction, and intensity."""

import math
from typing import Optional, Tuple
import numpy as np

from ..models.enums import CellState
from .grid import SimulationGrid


def calculate_burned_area_ha(grid: SimulationGrid) -> float:
    """Calculate cumulative area burned (BURNING + BURNED) in hectares."""
    burned_count = np.count_nonzero(
        (grid.state == CellState.BURNING.value) | (grid.state == CellState.BURNED.value)
    )
    cell_area_ha = (grid.resolution_meters ** 2) / 10000.0
    return round(float(burned_count * cell_area_ha), 2)


def calculate_active_burning_cells(grid: SimulationGrid) -> int:
    """Count actively BURNING cells."""
    return int(np.count_nonzero(grid.state == CellState.BURNING.value))


def calculate_spread_velocity_kmh(
    grid: SimulationGrid,
    ignition_row: int,
    ignition_col: int,
    elapsed_hours: float,
) -> float:
    """
    Calculate maximum spread velocity from ignition source to furthest fire perimeter front.
    """
    if elapsed_hours <= 0.0:
        return 0.0

    burned_mask = (grid.state == CellState.BURNING.value) | (grid.state == CellState.BURNED.value)
    burned_indices = np.argwhere(burned_mask)

    if len(burned_indices) <= 1:
        # Initial cell: spread within single cell
        cell_radius_km = (grid.resolution_meters / 2.0) / 1000.0
        return round(cell_radius_km / elapsed_hours, 2)

    dr = burned_indices[:, 0] - ignition_row
    dc = burned_indices[:, 1] - ignition_col
    distances_m = np.sqrt((dr * grid.resolution_meters) ** 2 + (dc * grid.resolution_meters) ** 2)
    max_dist_km = float(np.max(distances_m)) / 1000.0

    velocity = max_dist_km / elapsed_hours
    return round(float(velocity), 2)


def calculate_dominant_spread_direction_deg(
    grid: SimulationGrid,
    ignition_row: int,
    ignition_col: int,
    fallback_direction_deg: float = 0.0,
) -> float:
    """
    Compute dominant compass heading of the fire spread wavefront from ignition point.
    Uses center-of-mass vector from ignition point.
    """
    burned_mask = (grid.state == CellState.BURNING.value) | (grid.state == CellState.BURNED.value)
    burned_indices = np.argwhere(burned_mask)

    if len(burned_indices) <= 1:
        return round(float(fallback_direction_deg), 1)

    mean_r = float(np.mean(burned_indices[:, 0]))
    mean_c = float(np.mean(burned_indices[:, 1]))

    delta_r = mean_r - ignition_row
    delta_c = mean_c - ignition_col

    # In grid coords: North is -delta_r, East is +delta_c
    y = -delta_r
    x = delta_c

    if abs(x) < 1e-4 and abs(y) < 1e-4:
        return round(float(fallback_direction_deg), 1)

    # Compass heading: 0=N, 90=E, 180=S, 270=W
    angle_rad = math.atan2(x, y)
    bearing_deg = (math.degrees(angle_rad) + 360.0) % 360.0
    return round(float(bearing_deg), 1)


def calculate_fire_intensity_mw(
    active_burning_count: int,
    wind_speed_ms: Optional[float] = None,
    base_intensity_mw: float = 4.0,
    intensity_per_cell_mw: float = 0.35,
) -> float:
    """
    Estimate aggregate fire radiative power (MW).
    """
    wind_multiplier = 1.0 + (0.05 * wind_speed_ms) if wind_speed_ms else 1.0
    intensity = (base_intensity_mw + active_burning_count * intensity_per_cell_mw) * wind_multiplier
    return round(float(intensity), 2)
