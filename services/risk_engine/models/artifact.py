"""Native model serialization and deserialization routines."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import xgboost as xgb
import joblib

from ..common.exceptions import ModelCorruptError
from ..features.schema import RiskFeatureSchema


class ModelArtifactSerializer:
    """Serializes and restores model binary artifacts and preprocessors."""

    @staticmethod
    def save_xgboost(model: xgb.XGBClassifier, target_path: Path) -> Path:
        """Save XGBoost model in native JSON format (model.json)."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(str(target_path))
        return target_path

    @staticmethod
    def load_xgboost(source_path: Path) -> xgb.XGBClassifier:
        """Load native XGBoost model from model.json."""
        if not source_path.exists():
            raise FileNotFoundError(f"Model file not found: {source_path}")
        model = xgb.XGBClassifier()
        try:
            model.load_model(str(source_path))
        except Exception as e:
            raise ModelCorruptError(f"Failed to load XGBoost model from {source_path}: {e}")
        return model

    @staticmethod
    def save_random_forest(model: Any, target_path: Path) -> Path:
        """Save Random Forest baseline model using joblib."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, target_path)
        return target_path

    @staticmethod
    def load_random_forest(source_path: Path) -> Any:
        if not source_path.exists():
            raise FileNotFoundError(f"Model file not found: {source_path}")
        try:
            return joblib.load(source_path)
        except Exception as e:
            raise ModelCorruptError(f"Failed to load Random Forest model from {source_path}: {e}")

    @staticmethod
    def save_preprocessor(preprocessor: Any, target_path: Path) -> Path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(preprocessor.to_dict(), f, indent=2)
        return target_path

    @staticmethod
    def load_preprocessor(source_path: Path) -> Any:
        from ..training.preprocessing import FeaturePreprocessor
        if not source_path.exists():
            raise FileNotFoundError(f"Preprocessor file not found: {source_path}")
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return FeaturePreprocessor.from_dict(data)
        except Exception as e:
            raise ModelCorruptError(f"Failed to load preprocessor from {source_path}: {e}")

    @staticmethod
    def save_feature_schema(schema: RiskFeatureSchema, target_path: Path) -> Path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(schema.model_dump(), f, indent=2)
        return target_path

    @staticmethod
    def load_feature_schema(source_path: Path) -> RiskFeatureSchema:
        if not source_path.exists():
            raise FileNotFoundError(f"Feature schema file not found: {source_path}")
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return RiskFeatureSchema(**data)
        except Exception as e:
            raise ModelCorruptError(f"Failed to load feature schema from {source_path}: {e}")
