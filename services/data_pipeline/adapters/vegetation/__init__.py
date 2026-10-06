"""Vegetation and fuel type adapters for Sentinel-2, Landsat-8, and ISRO Bhuvan."""

from .sentinel import SentinelVegetationAdapter
from .landsat import LandsatVegetationAdapter
from .bhuvan import BhuvanVegetationAdapter

__all__ = ["SentinelVegetationAdapter", "LandsatVegetationAdapter", "BhuvanVegetationAdapter"]
