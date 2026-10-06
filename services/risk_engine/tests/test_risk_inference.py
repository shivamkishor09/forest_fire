"""Unit tests for risk model inference, loader, and predictor interfaces."""

from pathlib import Path
from datetime import datetime, timezone
import pytest
import pandas as pd

from services.risk_engine.common.types import RiskClass, RiskInferenceInput
from services.risk_engine.inference.loader import ModelLoader
from services.risk_engine.inference.predictor import RiskPredictor
from services.risk_engine.models.registry import ModelRegistry
from services.risk_engine.training.pipeline import TrainingPipeline


@pytest.fixture
def trained_test_model(tmp_path: Path, sample_feature_matrix):
    data_file = tmp_path / "train.parquet"
    sample_feature_matrix.to_parquet(data_file)

    registry = ModelRegistry(registry_root=tmp_path / "models")
    pipeline = TrainingPipeline(registry=registry)
    pipeline.run(dataset_path=data_file, model_version="test-infer-v1")
    return registry, "test-infer-v1"


def test_model_loader_and_caching(trained_test_model):
    registry, version = trained_test_model
    ModelLoader.clear_cache()

    model1 = ModelLoader.load_model(version, registry=registry, use_cache=True)
    assert model1.model_version == version

    # Second call should retrieve from cache
    model2 = ModelLoader.load_model(version, registry=registry, use_cache=True)
    assert model1 is model2


def test_single_cell_prediction(trained_test_model):
    registry, version = trained_test_model
    model = ModelLoader.load_model(version, registry=registry)
    predictor = RiskPredictor(model)

    features = {
        "elevation_m": 1200.0,
        "slope_deg": 18.0,
        "aspect_deg": 180.0,
        "aspect_sin": 0.0,
        "aspect_cos": -1.0,
        "ndvi": 0.45,
        "ndwi": -0.12,
        "fuel_type": "CONIFER_HIGH_FLAMMABILITY",
        "temperature_c": 36.5,
        "relative_humidity_pct": 18.0,
        "wind_speed_ms": 6.5,
        "wind_direction_deg": 210.0,
        "wind_u_ms": -3.2,
        "wind_v_ms": -5.6,
        "precipitation_24h_mm": 0.0,
        "precipitation_7d_mm": 0.0,
        "fwi": 45.0,
        "fire_count_7d": 1,
        "fire_count_30d": 2,
        "days_since_last_fire": 3.0,
        "dist_to_recent_fire_m": 1500.0,
    }

    inp = RiskInferenceInput(
        grid_cell_id="cell_test_01",
        features=features,
        region_id="region_test",
        prediction_time=datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc),
    )

    pred = predictor.predict_risk(inp)
    assert pred.grid_cell_id == "cell_test_01"
    assert 0.0 <= pred.probability <= 1.0
    assert isinstance(pred.risk_class, RiskClass)
    assert pred.model_version == version
    assert pred.prediction_timestamp == "2026-05-15T12:00:00+00:00"
    assert pred.forecast_start == "2026-05-15T12:00:00+00:00"
    assert pred.forecast_end == "2026-05-16T12:00:00+00:00"
    assert pred.valid_for_date == "2026-05-15"


def test_batch_prediction_vectorized(trained_test_model, sample_feature_matrix):
    registry, version = trained_test_model
    model = ModelLoader.load_model(version, registry=registry)
    predictor = RiskPredictor(model)

    df = sample_feature_matrix.iloc[:50]
    predictions = predictor.predict_dataframe(df, region_id="test_reg")

    assert len(predictions) == 50
    for p in predictions:
        assert 0.0 <= p.probability <= 1.0
        assert p.risk_class in [RiskClass.LOW, RiskClass.MODERATE, RiskClass.HIGH, RiskClass.EXTREME]
        assert p.model_version == version
