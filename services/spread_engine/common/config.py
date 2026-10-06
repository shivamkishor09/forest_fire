"""Configuration constants and runtime settings for the Spread Simulation Engine."""

from dataclasses import dataclass
import os

ENGINE_VERSION: str = "spread-ca-v001"
DEFAULT_GRID_RESOLUTION_M: float = 500.0
MAX_SIMULATION_HOURS: int = 12
MIN_SIMULATION_HOURS: int = 1


@dataclass
class SpreadEngineSettings:
    """Runtime configuration for cellular automata simulation execution."""
    engine_version: str = ENGINE_VERSION
    default_resolution_m: float = DEFAULT_GRID_RESOLUTION_M
    max_duration_hours: int = MAX_SIMULATION_HOURS
    min_duration_hours: int = MIN_SIMULATION_HOURS
    sub_steps_per_hour: int = int(os.getenv("SPREAD_SUB_STEPS_PER_HOUR", "2"))
    default_burning_duration_steps: int = int(os.getenv("SPREAD_BURNING_STEPS", "2"))
    log_level: str = os.getenv("SPREAD_LOG_LEVEL", "INFO")
