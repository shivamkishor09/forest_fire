"""Unit tests for risk engine feature schema, validation, and ordering."""

import pytest
import pandas as pd
import numpy as np

from services.risk_engine.features.ordering import (
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    CANONICAL_RAW_FEATURES,
    KNOWN_FUEL_CLASSES,
)
from services.risk_engine.features.schema import RiskFeatureSchema, FEATURE_SPECIFICATIONS
from services.risk_engine.features.validation import RiskFeatureValidator
from services.risk_engine.common.exceptions import FeatureValidationError
from services.risk_engine.training.preprocessing import FeaturePreprocessor


def test_canonical_feature_definitions():
    assert len(NUMERICAL_FEATURES) == 20
    assert "elevation_m" in NUMERICAL_FEATURES
    assert "temperature_c" in NUMERICAL_FEATURES
    assert "fwi" in NUMERICAL_FEATURES
    assert "fuel_type" in CATEGORICAL_FEATURES
    assert len(CANONICAL_RAW_FEATURES) == 21
    assert "CONIFER_HIGH_FLAMMABILITY" in KNOWN_FUEL_CLASSES


def test_feature_specifications():
    schema = RiskFeatureSchema()
    assert len(schema.specifications) >= 21
    assert schema.specifications["temperature_c"].min_val == -40.0
    assert schema.specifications["temperature_c"].max_val == 65.0
    assert schema.specifications["relative_humidity_pct"].min_val == 0.0
    assert schema.specifications["relative_humidity_pct"].max_val == 100.0


def test_feature_validator_clean_input():
    features = {
        "elevation_m": 1200.0,
        "slope_deg": 18.0,
        "aspect_deg": 180.0,
        "aspect_sin": 0.0,
        "aspect_cos": -1.0,
        "ndvi": 0.45,
        "ndwi": -0.12,
        "fuel_type": "CHIR_PINE",
        "temperature_c": 32.5,
        "relative_humidity_pct": 24.0,
        "wind_speed_ms": 5.0,
        "wind_direction_deg": 210.0,
        "wind_u_ms": -2.5,
        "wind_v_ms": -4.3,
        "precipitation_24h_mm": 0.0,
        "precipitation_7d_mm": 0.0,
        "fwi": 28.5,
        "fire_count_7d": 0,
        "fire_count_30d": 1,
        "days_since_last_fire": 12.0,
        "dist_to_recent_fire_m": 4500.0,
    }
    errors = RiskFeatureValidator.validate_features(features, require_all_canonical=True)
    assert len(errors) == 0


def test_feature_validator_out_of_range():
    features = {
        "elevation_m": 1200.0,
        "slope_deg": 120.0,  # Invalid: > 90
        "temperature_c": 75.0,  # Invalid: > 65
        "relative_humidity_pct": 20.0,
        "wind_speed_ms": 5.0,
        "ndvi": 0.4,
        "fwi": 20.0,
    }
    errors = RiskFeatureValidator.validate_features(features)
    assert len(errors) == 2
    assert any("slope_deg out of range" in e for e in errors)
    assert any("temperature_c out of range" in e for e in errors)


def test_feature_preprocessor_deterministic_transform():
    preprocessor = FeaturePreprocessor()
    df = pd.DataFrame([{
        "elevation_m": 1200.0,
        "slope_deg": 18.0,
        "aspect_deg": 180.0,
        "aspect_sin": 0.0,
        "aspect_cos": -1.0,
        "ndvi": 0.45,
        "ndwi": -0.12,
        "fuel_type": "CONIFER_HIGH_FLAMMABILITY",
        "temperature_c": 32.5,
        "relative_humidity_pct": 24.0,
        "wind_speed_ms": 5.0,
        "wind_direction_deg": 210.0,
        "wind_u_ms": -2.5,
        "wind_v_ms": -4.3,
        "precipitation_24h_mm": 0.0,
        "precipitation_7d_mm": 0.0,
        "fwi": 28.5,
        "fire_count_7d": 0,
        "fire_count_30d": 1,
        "days_since_last_fire": 12.0,
        "dist_to_recent_fire_m": 4500.0,
    }])

    matrix = preprocessor.transform_dataframe(df)
    assert matrix.shape == (1, len(preprocessor.final_feature_names))
    assert matrix["fuel_CONIFER_HIGH_FLAMMABILITY"].iloc[0] == 1.0
    assert matrix["fuel_NON_BURNABLE_WATER"].iloc[0] == 0.0
