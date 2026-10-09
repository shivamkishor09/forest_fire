"""Domain enumerations for cellular automata fire spread simulation."""

from enum import IntEnum, Enum


class CellState(IntEnum):
    """Discrete state of a spatial grid cell in Cellular Automata."""
    UNBURNED = 0
    BURNING = 1
    BURNED = 2
    NON_BURNABLE = 3

    @property
    def is_combustible(self) -> bool:
        """Return True if cell can catch fire."""
        return self == CellState.UNBURNED

    @property
    def is_active(self) -> bool:
        """Return True if cell is actively spreading fire."""
        return self == CellState.BURNING

    @property
    def has_burned(self) -> bool:
        """Return True if cell is currently burning or already burned."""
        return self in (CellState.BURNING, CellState.BURNED)


class FuelClass(str, Enum):
    """Canonical fuel flammability classes for Indian forest terrain."""
    CONIFER_HIGH_FLAMMABILITY = "CONIFER_HIGH_FLAMMABILITY"
    CONIFER_MODERATE_FLAMMABILITY = "CONIFER_MODERATE_FLAMMABILITY"
    PINE_MODERATE_FLAMMABILITY = "PINE_MODERATE_FLAMMABILITY"
    BROADLEAF_HIGH_LITTER = "BROADLEAF_HIGH_LITTER"
    BROADLEAF_MODERATE_LITTER = "BROADLEAF_MODERATE_LITTER"
    DECIDUOUS_LOW_FLAMMABILITY = "DECIDUOUS_LOW_FLAMMABILITY"
    GRASSLAND_FAST_SPREAD = "GRASSLAND_FAST_SPREAD"
    GRASSLAND_RAPID_SPREAD = "GRASSLAND_RAPID_SPREAD"
    SHRUB_COMPACT = "SHRUB_COMPACT"
    AGRICULTURE_SEASONAL = "AGRICULTURE_SEASONAL"
    NON_FOREST_LOW_FUEL = "NON_FOREST_LOW_FUEL"
    NON_BURNABLE_WATER = "NON_BURNABLE_WATER"
    NON_BURNABLE_BARREN = "NON_BURNABLE_BARREN"
    UNKNOWN = "UNKNOWN"
