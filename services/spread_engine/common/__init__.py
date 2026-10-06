"""Common utilities, configurations, and exception hierarchy for spread-engine."""

from .exceptions import (
    SpreadEngineError,
    InvalidSimulationInputError,
    GridValidationError,
    IgnitionOutsideGridError,
    UnsupportedDurationError,
    InvalidEnvironmentalDataError,
    SimulationNumericalError,
    BoundaryExtractionError,
)
from .config import SpreadEngineSettings, ENGINE_VERSION, DEFAULT_GRID_RESOLUTION_M
from .logging import get_logger
from .validation import validate_simulation_inputs

__all__ = [
    "SpreadEngineError",
    "InvalidSimulationInputError",
    "GridValidationError",
    "IgnitionOutsideGridError",
    "UnsupportedDurationError",
    "InvalidEnvironmentalDataError",
    "SimulationNumericalError",
    "BoundaryExtractionError",
    "SpreadEngineSettings",
    "ENGINE_VERSION",
    "DEFAULT_GRID_RESOLUTION_M",
    "get_logger",
    "validate_simulation_inputs",
]
