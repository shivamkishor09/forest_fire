"""Fuel flammability factors for Indian forest vegetation models."""

from typing import Dict
from ..models.enums import FuelClass

# Flammability multipliers calibrated for Indian forest fuel beds
FUEL_FLAMMABILITY_FACTORS: Dict[str, float] = {
    FuelClass.CONIFER_HIGH_FLAMMABILITY.value: 1.80,    # Chir Pine: volatile resins, aerated needles
    FuelClass.GRASSLAND_FAST_SPREAD.value: 1.50,         # Scrub/Grassland: high surface-area-to-volume ratio
    FuelClass.GRASSLAND_RAPID_SPREAD.value: 1.50,        # Dry Grassland (Rapid)
    FuelClass.CONIFER_MODERATE_FLAMMABILITY.value: 1.00, # Temperate Conifer (Deodar, Spruce, Fir)
    FuelClass.PINE_MODERATE_FLAMMABILITY.value: 0.95,    # Pine Forest (Moderate): compact needle bed, moderate moisture
    FuelClass.BROADLEAF_HIGH_LITTER.value: 1.20,         # Sal Deciduous: heavy seasonal leaf litter
    FuelClass.BROADLEAF_MODERATE_LITTER.value: 1.00,     # Dry Deciduous / Mixed Forest (reference baseline)
    FuelClass.SHRUB_COMPACT.value: 0.90,                 # Compact Shrub / Heath
    FuelClass.AGRICULTURE_SEASONAL.value: 0.60,          # Agricultural Cropland / Fallow
    FuelClass.DECIDUOUS_LOW_FLAMMABILITY.value: 0.30,    # Moist Deciduous (Low): high moisture foliage, low spread
    FuelClass.NON_FOREST_LOW_FUEL.value: 0.15,           # Non-Forest / Sparse Vegetation (Extremely Low)
    FuelClass.UNKNOWN.value: 1.00,                       # Unknown fallback (baseline)
    FuelClass.NON_BURNABLE_WATER.value: 0.00,            # Water bodies: impermeable firebreak
    FuelClass.NON_BURNABLE_BARREN.value: 0.00,           # Barren rock/scree/snow: zero combustible fuel
}

# Mapping from raw classification identifiers
RAW_FUEL_ALIASES: Dict[str, str] = {
    "CHIR_PINE": FuelClass.CONIFER_HIGH_FLAMMABILITY.value,
    "TEMPERATE_CONIFER": FuelClass.CONIFER_MODERATE_FLAMMABILITY.value,
    "SAL_DECIDUOUS": FuelClass.BROADLEAF_HIGH_LITTER.value,
    "DRY_DECIDUOUS": FuelClass.BROADLEAF_MODERATE_LITTER.value,
    "DECIDUOUS_FOREST": FuelClass.BROADLEAF_MODERATE_LITTER.value,
    "SCRUB_GRASSLAND": FuelClass.GRASSLAND_FAST_SPREAD.value,
    "SHRUB_HEATH": FuelClass.SHRUB_COMPACT.value,
    "AGRICULTURE_CROPLAND": FuelClass.AGRICULTURE_SEASONAL.value,
    "WATER_RIVER": FuelClass.NON_BURNABLE_WATER.value,
    "BARREN_ROCK_SNOW": FuelClass.NON_BURNABLE_BARREN.value,
    "DECIDUOUS_LOW": FuelClass.DECIDUOUS_LOW_FLAMMABILITY.value,
    "DECIDUOUS_LOW_FLAMMABILITY": FuelClass.DECIDUOUS_LOW_FLAMMABILITY.value,
    "PINE_MODERATE": FuelClass.PINE_MODERATE_FLAMMABILITY.value,
    "PINE_MODERATE_FLAMMABILITY": FuelClass.PINE_MODERATE_FLAMMABILITY.value,
    "GRASSLAND_RAPID": FuelClass.GRASSLAND_RAPID_SPREAD.value,
    "GRASSLAND_RAPID_SPREAD": FuelClass.GRASSLAND_RAPID_SPREAD.value,
    "NON_FOREST": FuelClass.NON_FOREST_LOW_FUEL.value,
    "NON_FOREST_LOW_FUEL": FuelClass.NON_FOREST_LOW_FUEL.value,
    "LOW": FuelClass.DECIDUOUS_LOW_FLAMMABILITY.value,
    "LOW_FLAMMABILITY": FuelClass.DECIDUOUS_LOW_FLAMMABILITY.value,
}


def normalize_fuel_type(fuel_type: str) -> str:
    """Normalize raw or case-insensitive fuel string to canonical FuelClass value."""
    if not fuel_type:
        return FuelClass.UNKNOWN.value
    cleaned = fuel_type.strip().upper()
    if cleaned in RAW_FUEL_ALIASES:
        return RAW_FUEL_ALIASES[cleaned]
    if cleaned in FUEL_FLAMMABILITY_FACTORS:
        return cleaned
    return FuelClass.UNKNOWN.value


def calculate_fuel_factor(fuel_type: str) -> float:
    """
    Return the combustibility multiplier for a given fuel type.
    Returns 0.0 for non-burnable fuel classes.
    """
    canonical_type = normalize_fuel_type(fuel_type)
    return FUEL_FLAMMABILITY_FACTORS.get(canonical_type, 1.0)
