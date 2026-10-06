"""Domain models and data schemas for Cellular Automata fire spread."""

from .enums import CellState, FuelClass
from .config import SimulationInput, EnvironmentalConditions
from .inputs import (
    IgnitionPoint,
    WindCondition,
    TerrainCondition,
    TerrainGridData,
    SpreadSimulationInput,
)
from .outputs import (
    SpreadTimestepSnapshot,
    SpreadSimulationSummary,
    SpreadSimulationOutput,
)

__all__ = [
    "CellState",
    "FuelClass",
    "SimulationInput",
    "EnvironmentalConditions",
    "IgnitionPoint",
    "WindCondition",
    "TerrainCondition",
    "TerrainGridData",
    "SpreadSimulationInput",
    "SpreadTimestepSnapshot",
    "SpreadSimulationSummary",
    "SpreadSimulationOutput",
]
