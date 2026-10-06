"""Unit tests for data pipeline adapter interfaces."""

from datetime import datetime, timezone, date
from services.data_pipeline.adapters.base import BoundingBox
from services.data_pipeline.adapters.sample_adapters import (
    SampleModisFireAdapter,
    SampleImdWeatherAdapter,
    SampleSentinelVegetationAdapter,
    SampleCartoDemTerrainAdapter,
)


def test_adapters_instantiation_and_contract():
    """Verify sample adapters fulfill contract interfaces without raising errors."""
    bbox = BoundingBox(min_lon=78.0, min_lat=30.0, max_lon=79.0, max_lat=31.0)
    now = datetime.now(timezone.utc)
    today = date.today()

    # Fire adapter
    fire_adapter = SampleModisFireAdapter()
    assert fire_adapter.validate_connection() is True
    fires = fire_adapter.fetch_active_fires(bbox, now, now)
    assert len(fires) == 1
    assert fires[0]["source"] == "NASA_MODIS"

    # Weather adapter
    weather_adapter = SampleImdWeatherAdapter()
    assert weather_adapter.validate_connection() is True
    weather = weather_adapter.fetch_weather_grid(bbox, today)
    assert "metrics" in weather
    assert "temperature_c" in weather["metrics"]

    # Vegetation adapter
    veg_adapter = SampleSentinelVegetationAdapter()
    assert veg_adapter.validate_connection() is True
    veg = veg_adapter.fetch_vegetation_indices(bbox, today)
    assert "mean_ndvi" in veg

    # Terrain adapter
    terrain_adapter = SampleCartoDemTerrainAdapter()
    assert terrain_adapter.validate_connection() is True
    terrain = terrain_adapter.fetch_elevation_model(bbox)
    assert "elevation_min_m" in terrain
