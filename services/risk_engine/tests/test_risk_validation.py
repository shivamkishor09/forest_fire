"""Unit tests for Risk Engine feature validation."""

import pytest
from services.risk_engine.features.validator import RiskFeatureValidator


def test_feature_validator_success():
    """Verify complete valid feature set passes validation."""
    valid_features = {
        "elevation_m": 1500.0,
        "slope_deg": 15.0,
        "temperature_c": 30.0,
        "relative_humidity_pct": 20.0,
        "wind_speed_ms": 6.0,
        "ndvi": 0.4,
        "fwi": 22.0,
    }
    errors = RiskFeatureValidator.validate_features(valid_features)
    assert len(errors) == 0


def test_feature_validator_missing_fields():
    """Verify validator catches missing required features."""
    incomplete_features = {
        "elevation_m": 1500.0,
        "temperature_c": 30.0,
    }
    errors = RiskFeatureValidator.validate_features(incomplete_features)
    assert len(errors) == 1
    assert "Missing required features" in errors[0]


def test_feature_validator_out_of_range():
    """Verify validator catches out-of-range numerical values."""
    invalid_features = {
        "elevation_m": 1500.0,
        "slope_deg": 120.0,  # Invalid slope > 90 deg
        "temperature_c": 30.0,
        "relative_humidity_pct": 110.0,  # Invalid humidity > 100%
        "wind_speed_ms": 6.0,
        "ndvi": 2.5,  # Invalid NDVI > 1.0
        "fwi": -5.0,  # Invalid negative FWI
    }
    errors = RiskFeatureValidator.validate_features(invalid_features)
    assert len(errors) == 4
