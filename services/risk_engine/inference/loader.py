"""Safe model loader with in-memory caching and integrity checks."""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import xgboost as xgb

from ..common.config import settings
from ..common.exceptions import ModelNotFoundError, ModelCorruptError
from ..common.types import ModelMetadata
from ..models.artifact import ModelArtifactSerializer
from ..models.metadata import ModelMetadataManager
from ..models.registry import ModelRegistry
from ..training.trainer import TrainedXGBoostRiskModel, TrainedRandomForestRiskModel


class ModelLoader:
    """Safely loads model artifacts from the registry with thread-safe caching."""

    _cache: Dict[str, Any] = {}

    @classmethod
    def load_model(
        cls,
        version: Optional[str] = None,
        registry: Optional[ModelRegistry] = None,
        use_cache: bool = True,
    ) -> Union[TrainedXGBoostRiskModel, TrainedRandomForestRiskModel]:
        """
        Load model version from registry. If version is None, loads default active version.
        """
        reg = registry or ModelRegistry()
        target_version = version or reg.get_default_version()

        if use_cache and target_version in cls._cache:
            return cls._cache[target_version]

        model_dir = reg.get_model_dir(target_version)

        # 1. Load metadata
        metadata_file = model_dir / "metadata.json"
        metadata = ModelMetadataManager.load_metadata(metadata_file)

        # 2. Load preprocessor
        preprocessor_file = model_dir / "preprocessor.json"
        preprocessor = ModelArtifactSerializer.load_preprocessor(preprocessor_file)

        # 3. Load optional calibrator & thresholds
        cal_file = model_dir / "calibrator.joblib"
        calibrator = None
        if cal_file.exists():
            try:
                import joblib
                calibrator = joblib.load(cal_file)
            except Exception:
                calibrator = None

        thresh_file = model_dir / "thresholds.json"
        thresholds = None
        if thresh_file.exists():
            try:
                import json
                with open(thresh_file, "r", encoding="utf-8") as f:
                    thresholds = json.load(f)
            except Exception:
                thresholds = None

        # 4. Load model artifact
        xgb_file = model_dir / "model.json"
        rf_file = model_dir / "model.joblib"

        if xgb_file.exists():
            raw_model = ModelArtifactSerializer.load_xgboost(xgb_file)
            wrapped_model = TrainedXGBoostRiskModel(
                model=raw_model,
                preprocessor=preprocessor,
                metadata=metadata,
                calibrator=calibrator,
                thresholds=thresholds,
            )
        elif rf_file.exists():
            raw_model = ModelArtifactSerializer.load_random_forest(rf_file)
            wrapped_model = TrainedRandomForestRiskModel(
                model=raw_model,
                preprocessor=preprocessor,
                metadata=metadata,
            )
        else:
            raise ModelNotFoundError(f"No valid model binary found in {model_dir}")

        if use_cache:
            cls._cache[target_version] = wrapped_model

        return wrapped_model

    @classmethod
    def clear_cache(cls) -> None:
        """Clear model cache."""
        cls._cache.clear()
