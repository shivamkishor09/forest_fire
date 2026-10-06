"""Vegetation and fuel feature engineering: spectral indices and fuel categorization."""

from typing import Optional


def compute_ndvi(nir: Optional[float], red: Optional[float]) -> Optional[float]:
    """
    Compute Normalized Difference Vegetation Index: (NIR - Red) / (NIR + Red).
    Valid output range: [-1.0, 1.0].
    """
    if nir is None or red is None:
        return None
    denom = nir + red
    if denom == 0.0:
        return 0.0
    ndvi = (nir - red) / denom
    return round(max(min(ndvi, 1.0), -1.0), 4)


def compute_ndwi(nir: Optional[float], swir: Optional[float]) -> Optional[float]:
    """
    Compute Normalized Difference Water/Moisture Index: (NIR - SWIR) / (NIR + SWIR).
    Valid output range: [-1.0, 1.0].
    """
    if nir is None or swir is None:
        return None
    denom = nir + swir
    if denom == 0.0:
        return 0.0
    ndwi = (nir - swir) / denom
    return round(max(min(ndwi, 1.0), -1.0), 4)


# Fuel category mapping table: Indian forest types to standard fuel codes
STANDARDIZED_FUEL_CLASSES = {
    "CHIR_PINE": "CONIFER_HIGH_FLAMMABILITY",
    "TEMPERATE_CONIFER": "CONIFER_MODERATE_FLAMMABILITY",
    "SAL_DECIDUOUS": "BROADLEAF_HIGH_LITTER",
    "DRY_DECIDUOUS": "BROADLEAF_MODERATE_LITTER",
    "SCRUB_GRASSLAND": "GRASSLAND_FAST_SPREAD",
    "SHRUB_HEATH": "SHRUB_COMPACT",
    "AGRICULTURE_CROPLAND": "AGRICULTURE_SEASONAL",
    "WATER_RIVER": "NON_BURNABLE_WATER",
    "BARREN_ROCK_SNOW": "NON_BURNABLE_BARREN",
    "UNKNOWN": "BROADLEAF_MODERATE_LITTER",
}


def standardize_fuel_class(raw_fuel_type: Optional[str]) -> str:
    """Normalize raw land cover or fuel class string to standardized category."""
    if not raw_fuel_type:
        return STANDARDIZED_FUEL_CLASSES["UNKNOWN"]
    norm = raw_fuel_type.strip().upper()
    return STANDARDIZED_FUEL_CLASSES.get(norm, norm)
