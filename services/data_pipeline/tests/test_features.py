"""Unit tests for feature engineering equations and Canadian FWI system."""

import math
from datetime import datetime, timezone, timedelta
import pytest
from services.data_pipeline.features.weather import (
    kelvin_to_celsius,
    compute_wind_vector_components,
    compute_wind_speed_and_direction,
)
from services.data_pipeline.features.vegetation import (
    compute_ndvi,
    compute_ndwi,
    standardize_fuel_class,
)
from services.data_pipeline.features.terrain import (
    compute_cyclical_aspect,
    compute_slope_gradient_percent,
)
from services.data_pipeline.features.fire_weather import FwiCalculator
from services.data_pipeline.features.target import TargetLabeler
from services.data_pipeline.common.types import (
    CanonicalFireObservation,
    GridCellDefinition,
)
from services.data_pipeline.grid.indexing import SpatialGridIndex


def test_weather_feature_engineering():
    # Temperature
    assert kelvin_to_celsius(300.15) == 27.0
    assert kelvin_to_celsius(None) is None

    # Wind vectors: North wind (0°) blowing from North to South (v < 0, u = 0)
    u, v = compute_wind_vector_components(10.0, 0.0)
    assert u == 0.0
    assert v == -10.0

    # East wind (90°) blowing from East to West (u < 0, v = 0)
    u_east, v_east = compute_wind_vector_components(10.0, 90.0)
    assert u_east == -10.0
    assert abs(v_east) < 1e-3

    # Reconstruction
    spd, d = compute_wind_speed_and_direction(u, v)
    assert spd == 10.0
    assert d == 0.0


def test_vegetation_features():
    # NDVI = (NIR - Red) / (NIR + Red)
    ndvi = compute_ndvi(0.6, 0.2)
    assert ndvi == 0.5  # (0.4 / 0.8)

    # NDWI = (NIR - SWIR) / (NIR + SWIR)
    ndwi = compute_ndwi(0.6, 0.4)
    assert ndwi == 0.2  # (0.2 / 1.0)

    # Standardization
    assert standardize_fuel_class("CHIR_PINE") == "CONIFER_HIGH_FLAMMABILITY"
    assert standardize_fuel_class(None) == "BROADLEAF_MODERATE_LITTER"


def test_terrain_features():
    # Aspect 0° (North) -> sin=0, cos=1
    s, c = compute_cyclical_aspect(0.0)
    assert s == 0.0
    assert c == 1.0

    # Aspect 90° (East) -> sin=1, cos=0
    s_east, c_east = compute_cyclical_aspect(90.0)
    assert s_east == 1.0
    assert abs(c_east) < 1e-4

    # Slope gradient
    grad = compute_slope_gradient_percent(45.0)
    assert 99.0 < grad < 101.0  # tan(45°) = 1.0 -> 100%


def test_fwi_calculator_equations():
    # Moderate warm dry condition
    temp = 32.0
    rh = 25.0
    wind_spd = 5.0  # m/s -> 18 km/h
    rain = 0.0

    fwi_dict = FwiCalculator.calculate_all_indices(
        temperature_c=temp,
        rh_pct=rh,
        wind_speed_ms=wind_spd,
        precipitation_24h_mm=rain,
        month=5,
    )

    assert "ffmc" in fwi_dict
    assert "isi" in fwi_dict
    assert "dmc" in fwi_dict
    assert "dc" in fwi_dict
    assert "bui" in fwi_dict
    assert "fwi" in fwi_dict

    # Check plausible ranges
    assert 80.0 <= fwi_dict["ffmc"] <= 101.0
    assert fwi_dict["isi"] > 0.0
    assert fwi_dict["fwi"] > 0.0


def test_target_labeler_24h_window():
    ref_time = datetime(2026, 5, 15, 0, 0, 0, tzinfo=timezone.utc)
    labeler = TargetLabeler(reference_time=ref_time, target_window_hours=24)

    # Cell definition
    cell = GridCellDefinition(
        cell_id="c1",
        region_id="r1",
        cell_code="CELL_01",
        centroid_lat=30.2,
        centroid_lon=78.7,
        geometry={"type": "Polygon", "coordinates": [[[78.69, 30.19], [78.71, 30.19], [78.71, 30.21], [78.69, 30.21], [78.69, 30.19]]]},
    )
    index = SpatialGridIndex([cell])

    past_fire = CanonicalFireObservation(
        source="MODIS",
        detection_time=datetime(2026, 5, 14, 23, 0, 0, tzinfo=timezone.utc),  # Past (< T_ref)
        latitude=30.2,
        longitude=78.7,
        confidence_pct=80.0,
    )
    future_fire = CanonicalFireObservation(
        source="MODIS",
        detection_time=datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc),  # Inside target window
        latitude=30.2,
        longitude=78.7,
        confidence_pct=90.0,
    )
    far_future_fire = CanonicalFireObservation(
        source="MODIS",
        detection_time=datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc),  # Outside target window (> T_ref+24h)
        latitude=30.2,
        longitude=78.7,
        confidence_pct=90.0,
    )

    labels = labeler.compute_labels_for_cells([cell], [past_fire, future_fire, far_future_fire], index)
    assert labels["c1"] == 1

    # Without future fire
    labels_no_future = labeler.compute_labels_for_cells([cell], [past_fire, far_future_fire], index)
    assert labels_no_future["c1"] == 0
