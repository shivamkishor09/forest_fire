"""Validation utilities for simulation input configurations."""

from typing import Optional
from .config import MIN_SIMULATION_HOURS, MAX_SIMULATION_HOURS
from .exceptions import (
    InvalidSimulationInputError,
    UnsupportedDurationError,
    GridValidationError,
    InvalidEnvironmentalDataError,
)


def validate_simulation_inputs(
    duration_hours: int,
    grid_rows: int,
    grid_cols: int,
    grid_resolution_meters: float,
    ignition_lat: float,
    ignition_lon: float,
    wind_speed_ms: Optional[float] = None,
    wind_direction_deg: Optional[float] = None,
) -> None:
    """Validate comprehensive simulation input parameters against domain invariants."""
    if not isinstance(duration_hours, int) or duration_hours < MIN_SIMULATION_HOURS or duration_hours > MAX_SIMULATION_HOURS:
        raise UnsupportedDurationError(
            f"Duration must be an integer between {MIN_SIMULATION_HOURS} and {MAX_SIMULATION_HOURS} hours, got {duration_hours}."
        )

    if grid_rows <= 0 or grid_cols <= 0:
        raise GridValidationError(
            f"Grid dimensions must be positive integers, got rows={grid_rows}, cols={grid_cols}."
        )

    if grid_resolution_meters <= 0:
        raise GridValidationError(
            f"Grid resolution must be greater than 0 meters, got {grid_resolution_meters}."
        )

    if not (-90.0 <= ignition_lat <= 90.0) or not (-180.0 <= ignition_lon <= 180.0):
        raise InvalidSimulationInputError(
            f"Ignition coordinates out of WGS 84 bounds: lat={ignition_lat}, lon={ignition_lon}."
        )

    if wind_speed_ms is not None:
        if wind_speed_ms < 0:
            raise InvalidEnvironmentalDataError(
                f"Wind speed cannot be negative, got {wind_speed_ms} m/s."
            )
        if wind_speed_ms > 100.0:
            raise InvalidEnvironmentalDataError(
                f"Wind speed exceeds maximum physical threshold (100 m/s), got {wind_speed_ms}."
            )

    if wind_direction_deg is not None:
        if not (0.0 <= wind_direction_deg <= 360.0):
            raise InvalidEnvironmentalDataError(
                f"Wind direction must be in range [0, 360] degrees, got {wind_direction_deg}."
            )
