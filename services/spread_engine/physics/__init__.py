"""Physics modules modeling wind, slope, aspect, and fuel propagation factors."""

from .factors import SpreadFactors, StandardSpreadFactors
from .wind import calculate_wind_factor, calculate_circular_angle_diff
from .slope import calculate_slope_factor, calculate_elevation_slope_factor
from .aspect import calculate_aspect_factor
from .fuel import calculate_fuel_factor, normalize_fuel_type, FUEL_FLAMMABILITY_FACTORS

__all__ = [
    "SpreadFactors",
    "StandardSpreadFactors",
    "calculate_wind_factor",
    "calculate_circular_angle_diff",
    "calculate_slope_factor",
    "calculate_elevation_slope_factor",
    "calculate_aspect_factor",
    "calculate_fuel_factor",
    "normalize_fuel_type",
    "FUEL_FLAMMABILITY_FACTORS",
]
