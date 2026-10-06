"""Digital Elevation Model (DEM) terrain adapters for SRTM and ISRO CartoDEM."""

from .srtm import SrtmTerrainAdapter
from .cartodem import CartoDemTerrainAdapter

__all__ = ["SrtmTerrainAdapter", "CartoDemTerrainAdapter"]
