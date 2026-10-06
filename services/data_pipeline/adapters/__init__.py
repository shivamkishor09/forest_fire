"""Data pipeline adapters package."""

from .base import (
    BoundingBox,
    BaseDataSource,
    FireDataSource,
    WeatherDataSource,
    VegetationDataSource,
    TerrainDataSource,
)
from .sample_adapters import (
    SampleModisFireAdapter,
    SampleImdWeatherAdapter,
    SampleSentinelVegetationAdapter,
    SampleCartoDemTerrainAdapter,
)
from .fire import ModisFireAdapter, ViirsFireAdapter, InsatFireAdapter
from .weather import Era5WeatherAdapter, ImdWeatherAdapter
from .vegetation import SentinelVegetationAdapter, LandsatVegetationAdapter, BhuvanVegetationAdapter
from .terrain import SrtmTerrainAdapter, CartoDemTerrainAdapter

__all__ = [
    "BoundingBox",
    "BaseDataSource",
    "FireDataSource",
    "WeatherDataSource",
    "VegetationDataSource",
    "TerrainDataSource",
    "SampleModisFireAdapter",
    "SampleImdWeatherAdapter",
    "SampleSentinelVegetationAdapter",
    "SampleCartoDemTerrainAdapter",
    "ModisFireAdapter",
    "ViirsFireAdapter",
    "InsatFireAdapter",
    "Era5WeatherAdapter",
    "ImdWeatherAdapter",
    "SentinelVegetationAdapter",
    "LandsatVegetationAdapter",
    "BhuvanVegetationAdapter",
    "SrtmTerrainAdapter",
    "CartoDemTerrainAdapter",
]
