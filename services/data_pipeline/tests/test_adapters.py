"""Unit tests for Phase 4 concrete data adapters."""

from datetime import datetime, timezone, date
import pytest
from services.data_pipeline.adapters.base import BoundingBox
from services.data_pipeline.adapters.fire.modis import ModisFireAdapter
from services.data_pipeline.adapters.fire.viirs import ViirsFireAdapter
from services.data_pipeline.adapters.fire.insat import InsatFireAdapter
from services.data_pipeline.adapters.weather.era5 import Era5WeatherAdapter
from services.data_pipeline.adapters.weather.imd import ImdWeatherAdapter
from services.data_pipeline.adapters.vegetation.sentinel import SentinelVegetationAdapter
from services.data_pipeline.adapters.vegetation.landsat import LandsatVegetationAdapter
from services.data_pipeline.adapters.vegetation.bhuvan import BhuvanVegetationAdapter
from services.data_pipeline.adapters.terrain.srtm import SrtmTerrainAdapter
from services.data_pipeline.adapters.terrain.cartodem import CartoDemTerrainAdapter


def test_modis_adapter_parsing():
    adapter = ModisFireAdapter()
    assert adapter.source_name == "NASA_MODIS"
    assert adapter.validate_connection() is True

    records = [
        {
            "latitude": 30.15,
            "longitude": 78.68,
            "brightness": 342.5,
            "scan": 1.1,
            "track": 1.0,
            "acq_date": "2026-05-10",
            "acq_time": 730,
            "confidence": 85,
            "frp": 28.4,
        }
    ]
    canonical = adapter.parse_records(records)
    assert len(canonical) == 1
    obs = canonical[0]
    assert obs.source == "NASA_MODIS"
    assert obs.latitude == 30.15
    assert obs.longitude == 78.68
    assert obs.confidence_pct == 85.0
    assert obs.frp_mw == 28.4
    assert obs.brightness_temp_k == 342.5
    assert obs.geometry["type"] == "Point"
    assert obs.geometry["coordinates"] == [78.68, 30.15]


def test_viirs_adapter_parsing():
    adapter = ViirsFireAdapter()
    assert adapter.source_name == "NASA_NOAA_VIIRS"

    records = [
        {
            "latitude": 30.22,
            "longitude": 78.73,
            "bright_ti4": 358.9,
            "acq_date": "2026-05-15",
            "acq_time": 800,
            "confidence": "high",
            "frp": 58.3,
        }
    ]
    canonical = adapter.parse_records(records)
    assert len(canonical) == 1
    obs = canonical[0]
    assert obs.source == "NASA_NOAA_VIIRS"
    assert obs.confidence_pct == 95.0
    assert obs.frp_mw == 58.3
    assert obs.brightness_temp_k == 358.9


def test_insat_adapter_parsing():
    adapter = InsatFireAdapter()
    assert adapter.source_name == "ISRO_INSAT_3D"

    records = [
        {
            "latitude": 30.18,
            "longitude": 78.71,
            "observation_time": "2026-05-14T08:30:00Z",
            "confidence_pct": 80.0,
            "frp_mw": 35.0,
            "brightness_temp_k": 330.0,
        }
    ]
    canonical = adapter.parse_records(records)
    assert len(canonical) == 1
    obs = canonical[0]
    assert obs.source == "ISRO_INSAT_3D"
    assert obs.frp_mw == 35.0


def test_era5_adapter_parsing():
    adapter = Era5WeatherAdapter()
    assert adapter.source_name == "ECMWF_ERA5"

    records = [
        {
            "latitude": 30.20,
            "longitude": 78.75,
            "timestamp": "2026-05-15T12:00:00Z",
            "temperature_k": 305.15,  # 32.0 C
            "relative_humidity_pct": 25.0,
            "u10": -3.0,
            "v10": -4.0,
            "tp": 0.002,  # 2.0 mm
        }
    ]
    canonical = adapter.parse_records(records)
    assert len(canonical) == 1
    obs = canonical[0]
    assert obs.temperature_c == 32.0
    assert obs.relative_humidity_pct == 25.0
    assert obs.precipitation_mm == 2.0
    assert obs.wind_speed_ms == 5.0
    assert obs.u_wind_ms == -3.0
    assert obs.v_wind_ms == -4.0


def test_imd_adapter_parsing():
    adapter = ImdWeatherAdapter()
    assert adapter.source_name == "IMD_API"

    records = [
        {
            "latitude": 30.15,
            "longitude": 78.78,
            "observation_date": "2026-05-15",
            "temperature_c": 33.2,
            "relative_humidity_pct": 21.0,
            "wind_speed_ms": 6.0,
            "wind_direction_deg": 215.0,
            "precipitation_mm": 0.0,
        }
    ]
    canonical = adapter.parse_records(records)
    assert len(canonical) == 1
    obs = canonical[0]
    assert obs.temperature_c == 33.2
    assert obs.wind_speed_ms == 6.0
    assert obs.u_wind_ms is not None
    assert obs.v_wind_ms is not None


def test_vegetation_adapters():
    s_adapter = SentinelVegetationAdapter()
    records = [
        {
            "latitude": 30.25,
            "longitude": 78.75,
            "observation_time": "2026-05-12T10:30:00Z",
            "b8": 0.35,  # NIR
            "b4": 0.15,  # Red -> NDVI = (0.35-0.15)/(0.35+0.15) = 0.2/0.5 = 0.4
            "b11": 0.25, # SWIR -> NDWI = (0.35-0.25)/(0.35+0.25) = 0.1/0.6 = 0.1667
            "fuel_type": "CHIR_PINE",
        }
    ]
    canonical = s_adapter.parse_records(records)
    assert len(canonical) == 1
    assert canonical[0].ndvi == 0.4
    assert canonical[0].fuel_type == "CHIR_PINE"

    b_adapter = BhuvanVegetationAdapter()
    b_records = [
        {
            "latitude": 30.25,
            "longitude": 78.75,
            "lulc_class": 3,  # CHIR_PINE
            "ndvi": 0.52,
        }
    ]
    b_canonical = b_adapter.parse_records(b_records)
    assert b_canonical[0].fuel_type == "CHIR_PINE"


def test_terrain_adapters():
    carto = CartoDemTerrainAdapter()
    records = [
        {
            "latitude": 30.20,
            "longitude": 78.70,
            "elevation_m": 1240.0,
            "slope_deg": 22.0,
            "aspect_deg": 195.0,
        }
    ]
    canonical = carto.parse_records(records)
    assert len(canonical) == 1
    assert canonical[0].elevation_m == 1240.0
    assert canonical[0].slope_deg == 22.0
    assert canonical[0].aspect_deg == 195.0
