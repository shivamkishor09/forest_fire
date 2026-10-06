"""Feature engineering package."""

from .weather import (
    kelvin_to_celsius,
    compute_wind_vector_components,
    compute_wind_speed_and_direction,
)
from .vegetation import compute_ndvi, compute_ndwi, standardize_fuel_class
from .terrain import compute_cyclical_aspect, compute_slope_gradient_percent
from .fire_weather import FwiCalculator
from .fire_history import FireHistoryExtractor
from .target import TargetLabeler
from .pipeline import FeaturePipeline

__all__ = [
    "kelvin_to_celsius",
    "compute_wind_vector_components",
    "compute_wind_speed_and_direction",
    "compute_ndvi",
    "compute_ndwi",
    "standardize_fuel_class",
    "compute_cyclical_aspect",
    "compute_slope_gradient_percent",
    "FwiCalculator",
    "FireHistoryExtractor",
    "TargetLabeler",
    "FeaturePipeline",
]
