"""Unit tests for ModelRegistry."""

from pathlib import Path
import pytest
import xgboost as xgb

from services.risk_engine.models.registry import ModelRegistry
from services.risk_engine.common.types import ModelMetadata
from services.risk_engine.training.preprocessing import FeaturePreprocessor
from services.risk_engine.features.schema import RiskFeatureSchema
from services.risk_engine.common.exceptions import ModelNotFoundError


def test_registry_operations(tmp_path: Path):
    registry = ModelRegistry(registry_root=tmp_path / "models")
    assert registry.list_models() == []

    # Create dummy model
    clf = xgb.XGBClassifier(n_estimators=2, max_depth=2)
    # Fit dummy data so it can be saved
    import numpy as np
    clf.fit(np.zeros((10, 5)), np.array([0]*9 + [1]))

    preprocessor = FeaturePreprocessor()
    schema = RiskFeatureSchema()
    meta = ModelMetadata(
        model_name="test-reg",
        model_version="risk-v001",
        algorithm="XGBoost",
    )

    saved_path = registry.register_model_version(
        version="risk-v001",
        model=clf,
        metadata=meta,
        preprocessor=preprocessor,
        schema=schema,
    )

    assert saved_path.exists()
    assert registry.list_models() == ["risk-v001"]
    assert registry.get_model_dir("risk-v001") == saved_path

    with pytest.raises(ModelNotFoundError):
        registry.get_model_dir("nonexistent-v999")
