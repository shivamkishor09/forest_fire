"""Canonical feature ordering for risk prediction models."""

from typing import Dict, List

# Exact, immutable ordering of continuous numerical features fed into ML models
NUMERICAL_FEATURES: List[str] = [
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "aspect_sin",
    "aspect_cos",
    "ndvi",
    "ndwi",
    "temperature_c",
    "relative_humidity_pct",
    "wind_speed_ms",
    "wind_direction_deg",
    "wind_u_ms",
    "wind_v_ms",
    "precipitation_24h_mm",
    "precipitation_7d_mm",
    "fwi",
    "fire_count_7d",
    "fire_count_30d",
    "days_since_last_fire",
    "dist_to_recent_fire_m",
]

# Categorical features requiring encoding
CATEGORICAL_FEATURES: List[str] = [
    "fuel_type",
]

# Standard fuel classes recognized by the model (used for encoded matrix columns)
KNOWN_FUEL_CLASSES: List[str] = [
    "CONIFER_HIGH_FLAMMABILITY",
    "CONIFER_MODERATE_FLAMMABILITY",
    "BROADLEAF_HIGH_LITTER",
    "BROADLEAF_MODERATE_LITTER",
    "GRASSLAND_FAST_SPREAD",
    "SHRUB_COMPACT",
    "AGRICULTURE_SEASONAL",
    "NON_BURNABLE_WATER",
    "NON_BURNABLE_BARREN",
    "UNKNOWN",
]

# Raw Indian forest classes mapped to standardized categories
RAW_TO_STANDARDIZED_FUEL_MAPPING: Dict[str, str] = {
    "CHIR_PINE": "CONIFER_HIGH_FLAMMABILITY",
    "TEMPERATE_CONIFER": "CONIFER_MODERATE_FLAMMABILITY",
    "SAL_DECIDUOUS": "BROADLEAF_HIGH_LITTER",
    "DRY_DECIDUOUS": "BROADLEAF_MODERATE_LITTER",
    "DECIDUOUS_FOREST": "BROADLEAF_MODERATE_LITTER",
    "SCRUB_GRASSLAND": "GRASSLAND_FAST_SPREAD",
    "SHRUB_HEATH": "SHRUB_COMPACT",
    "AGRICULTURE_CROPLAND": "AGRICULTURE_SEASONAL",
    "WATER_RIVER": "NON_BURNABLE_WATER",
    "BARREN_ROCK_SNOW": "NON_BURNABLE_BARREN",
}

ALL_VALID_FUEL_CLASSES: List[str] = sorted(list(set(KNOWN_FUEL_CLASSES + list(RAW_TO_STANDARDIZED_FUEL_MAPPING.keys()))))


def normalize_fuel_class(raw_fuel: str) -> str:
    """Normalize any raw Indian or standardized fuel class string."""
    clean = str(raw_fuel).strip().upper()
    if clean in RAW_TO_STANDARDIZED_FUEL_MAPPING:
        return RAW_TO_STANDARDIZED_FUEL_MAPPING[clean]
    if clean in KNOWN_FUEL_CLASSES:
        return clean
    return "UNKNOWN"


# Complete set of raw input features expected from Phase 4 pipeline
CANONICAL_RAW_FEATURES: List[str] = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
