"""Unit tests for edge cases, error handling, and robust failure modes."""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from services.risk_engine.common.exceptions import (
    FeatureValidationError,
    InsufficientPositivesError,
    ModelNotFoundError,
    ModelCorruptError,
)
from services.risk_engine.training.dataset import TrainingDataset
from services.risk_engine.features.validation import RiskFeatureValidator
from services.risk_engine.inference.loader import ModelLoader
from services.risk_engine.models.artifact import ModelArtifactSerializer


def test_empty_dataset_raises():
    with pytest.raises(FeatureValidationError):
        TrainingDataset(df=pd.DataFrame())


def test_zero_positives_raises(tmp_path: Path):
    df = pd.DataFrame([{
        "grid_cell_id": f"c_{i}",
        "reference_date": "2026-05-15",
        "elevation_m": 1200.0,
        "slope_deg": 15.0,
        "aspect_deg": 180.0,
        "aspect_sin": 0.0,
        "aspect_cos": -1.0,
        "ndvi": 0.4,
        "ndwi": -0.1,
        "fuel_type": "CHIR_PINE",
        "temperature_c": 30.0,
        "relative_humidity_pct": 30.0,
        "wind_speed_ms": 4.0,
        "wind_direction_deg": 180.0,
        "wind_u_ms": 0.0,
        "wind_v_ms": -4.0,
        "precipitation_24h_mm": 0.0,
        "precipitation_7d_mm": 0.0,
        "fwi": 20.0,
        "fire_count_7d": 0,
        "fire_count_30d": 0,
        "days_since_last_fire": 365.0,
        "dist_to_recent_fire_m": 50000.0,
        "target_fire_next_24h": 0,  # All negatives!
    } for i in range(20)])

    p = tmp_path / "all_neg.parquet"
    df.to_parquet(p)

    with pytest.raises(InsufficientPositivesError):
        TrainingDataset.from_file(p, min_positives=1)


def test_missing_required_features_validation():
    features = {
        "elevation_m": 1200.0,
        # missing slope, temp, rh, wind, ndvi, fwi
    }
    errors = RiskFeatureValidator.validate_features(features)
    assert len(errors) > 0
    assert any("Missing required features" in e for e in errors)


def test_unexpected_unknown_feature_rejected():
    features = {
        "elevation_m": 1200.0,
        "slope_deg": 15.0,
        "temperature_c": 30.0,
        "relative_humidity_pct": 30.0,
        "wind_speed_ms": 4.0,
        "ndvi": 0.4,
        "fwi": 20.0,
        "unexpected_random_col": 999.0,  # Unknown feature!
    }
    errors = RiskFeatureValidator.validate_features(features, allow_unknown_fields=False)
    assert len(errors) > 0
    assert any("Unexpected unknown features" in e for e in errors)


def test_nan_values_rejected():
    features = {
        "elevation_m": 1200.0,
        "slope_deg": float("nan"),  # NaN
        "temperature_c": 30.0,
        "relative_humidity_pct": 30.0,
        "wind_speed_ms": 4.0,
        "ndvi": 0.4,
        "fwi": 20.0,
    }
    errors = RiskFeatureValidator.validate_features(features)
    assert len(errors) > 0
    assert any("non-finite" in e for e in errors)


def test_corrupted_model_loading_raises(tmp_path: Path):
    corrupt_file = tmp_path / "model.json"
    corrupt_file.write_text("this is completely invalid json not an xgboost model")

    with pytest.raises(ModelCorruptError):
        ModelArtifactSerializer.load_xgboost(corrupt_file)


def test_missing_model_raises():
    with pytest.raises(ModelNotFoundError):
        ModelLoader.load_model("definitely_nonexistent_version_xyz", use_cache=False)
