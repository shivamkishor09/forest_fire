"""Unit tests for XGBoost and Random Forest risk model training."""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from services.risk_engine.training.trainer import XGBoostRiskTrainer, RandomForestRiskTrainer
from services.risk_engine.training.preprocessing import FeaturePreprocessor
from services.risk_engine.training.pipeline import TrainingPipeline
from services.risk_engine.models.registry import ModelRegistry


def _create_deterministic_training_data(n_samples: int = 200) -> pd.DataFrame:
    np.random.seed(42)
    rows = []
    for i in range(n_samples):
        # Fire occurrence correlates with high temperature, low humidity, high FWI
        temp = float(np.random.uniform(25.0, 42.0))
        rh = float(np.random.uniform(15.0, 60.0))
        fwi = float(np.random.uniform(10.0, 80.0))
        target = 1 if (temp > 35.0 and rh < 25.0 and fwi > 40.0) else 0

        rows.append({
            "grid_cell_id": f"cell_{i:04d}",
            "cell_code": f"CELL_{i:04d}",
            "reference_date": "2026-05-15",
            "elevation_m": float(np.random.uniform(600, 2400)),
            "slope_deg": float(np.random.uniform(5, 40)),
            "aspect_deg": float(np.random.uniform(0, 360)),
            "aspect_sin": float(np.sin(np.radians(180))),
            "aspect_cos": float(np.cos(np.radians(180))),
            "fuel_type": "CONIFER_HIGH_FLAMMABILITY" if i % 2 == 0 else "BROADLEAF_MODERATE_LITTER",
            "ndvi": float(np.random.uniform(0.2, 0.7)),
            "ndwi": float(np.random.uniform(-0.3, 0.1)),
            "temperature_c": temp,
            "relative_humidity_pct": rh,
            "wind_speed_ms": float(np.random.uniform(2.0, 10.0)),
            "wind_direction_deg": float(np.random.uniform(0, 360)),
            "wind_u_ms": -3.0,
            "wind_v_ms": -4.0,
            "precipitation_24h_mm": 0.0,
            "precipitation_7d_mm": 0.0,
            "fwi": fwi,
            "fire_count_7d": int(np.random.poisson(0.5)),
            "fire_count_30d": int(np.random.poisson(1.5)),
            "days_since_last_fire": float(np.random.uniform(5, 365)),
            "dist_to_recent_fire_m": float(np.random.uniform(500, 25000)),
            "target_fire_next_24h": target,
        })
    df = pd.DataFrame(rows)
    # Ensure at least 5 positives exist
    if (df["target_fire_next_24h"] == 1).sum() < 5:
        df.loc[:4, "target_fire_next_24h"] = 1
    return df


def test_xgboost_trainer():
    df = _create_deterministic_training_data(100)
    preprocessor = FeaturePreprocessor()
    trainer = XGBoostRiskTrainer(n_estimators=10, max_depth=3, random_state=42)

    model = trainer.train(df, preprocessor=preprocessor, model_version="test-xgb")
    assert model.model_version == "test-xgb"
    assert model.model_name == "risk-xgboost"

    # Single cell inference
    sample_feat = df.iloc[0].to_dict()
    prob = model.predict_susceptibility(sample_feat)
    assert 0.0 <= prob <= 1.0

    # Batch prediction
    probas = model.predict_batch_probabilities(df)
    assert len(probas) == len(df)
    assert ((probas >= 0.0) & (probas <= 1.0)).all()

    # Feature importance
    importances = model.feature_importances
    assert len(importances) > 0
    assert sum(importances.values()) > 0.0


def test_random_forest_trainer():
    df = _create_deterministic_training_data(100)
    preprocessor = FeaturePreprocessor()
    trainer = RandomForestRiskTrainer(n_estimators=10, max_depth=3, random_state=42)

    model = trainer.train(df, preprocessor=preprocessor, model_version="test-rf")
    assert model.model_version == "test-rf"
    prob = model.predict_susceptibility(df.iloc[0].to_dict())
    assert 0.0 <= prob <= 1.0


def test_training_pipeline_execution(tmp_path: Path):
    df = _create_deterministic_training_data(120)
    data_file = tmp_path / "train_data.parquet"
    df.to_parquet(data_file)

    registry = ModelRegistry(registry_root=tmp_path / "models")
    pipeline = TrainingPipeline(registry=registry)

    trained_model, metrics, artifact_path = pipeline.run(
        dataset_path=data_file,
        model_version="risk-test-v1",
        train_ratio=0.75,
        include_rf_baseline=True,
    )

    assert artifact_path.exists()
    assert (artifact_path / "model.json").exists()
    assert (artifact_path / "metadata.json").exists()
    assert (artifact_path / "feature_schema.json").exists()
    assert (artifact_path / "metrics.json").exists()
    assert (artifact_path / "evaluation_report.md").exists()
    assert (artifact_path / "MODEL_CARD.md").exists()

    assert metrics.accuracy > 0.0
