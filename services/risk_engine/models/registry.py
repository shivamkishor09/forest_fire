"""Lightweight filesystem-backed model registry for risk model versions."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import xgboost as xgb

from ..common.config import settings
from ..common.exceptions import ModelNotFoundError
from ..common.types import ModelMetadata, EvaluationMetrics
from ..features.schema import RiskFeatureSchema
from .artifact import ModelArtifactSerializer
from .metadata import ModelMetadataManager
from ..evaluation.reports import EvaluationReportGenerator


class ModelRegistry:
    """Manages versioned model artifacts under models/risk/."""

    def __init__(self, registry_root: Optional[Path] = None):
        self.root = Path(registry_root or settings.model_storage_path)
        self.root.mkdir(parents=True, exist_ok=True)

    def list_models(self) -> List[str]:
        """List all valid registered model versions."""
        if not self.root.exists():
            return []
        versions = []
        for item in sorted(self.root.iterdir()):
            if item.is_dir() and (item / "metadata.json").exists():
                versions.append(item.name)
        return versions

    def get_model_dir(self, version: str) -> Path:
        """Get directory path for a model version. Raises ModelNotFoundError if absent."""
        target = self.root / version
        if not target.exists() or not target.is_dir():
            raise ModelNotFoundError(f"Model version '{version}' does not exist in registry at {self.root}")
        return target

    def get_default_version(self) -> str:
        """Return the default active model version."""
        default_ver = settings.DEFAULT_RISK_MODEL_VERSION
        available = self.list_models()
        if default_ver in available:
            return default_ver
        if available:
            return available[0]
        return default_ver

    def register_model_version(
        self,
        version: str,
        model: Any,
        metadata: ModelMetadata,
        preprocessor: Any,
        schema: RiskFeatureSchema,
        metrics: Optional[EvaluationMetrics] = None,
    ) -> Path:
        """
        Save complete versioned model artifact package:
        - model.json
        - metadata.json
        - preprocessor.json
        - feature_schema.json
        - metrics.json (if metrics provided)
        - evaluation_report.md (if metrics provided)
        - MODEL_CARD.md (if metrics provided)
        """
        version_dir = self.root / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save model binary
        if isinstance(model, xgb.XGBClassifier):
            ModelArtifactSerializer.save_xgboost(model, version_dir / "model.json")
        else:
            ModelArtifactSerializer.save_random_forest(model, version_dir / "model.joblib")

        # 2. Save preprocessor and schema
        ModelArtifactSerializer.save_preprocessor(preprocessor, version_dir / "preprocessor.json")
        ModelArtifactSerializer.save_feature_schema(schema, version_dir / "feature_schema.json")

        # 3. Save metadata
        if metrics is not None:
            metadata.metrics = {
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "roc_auc": metrics.roc_auc if metrics.roc_auc is not None else 0.0,
            }
            metadata.confusion_matrix = {
                "tp": metrics.true_positives,
                "fp": metrics.false_positives,
                "tn": metrics.true_negatives,
                "fn": metrics.false_negatives,
            }
            EvaluationReportGenerator.save_metrics_json(metrics, version_dir / "metrics.json")
            EvaluationReportGenerator.generate_evaluation_markdown(metadata, metrics, version_dir / "evaluation_report.md")
            EvaluationReportGenerator.generate_model_card(metadata, metrics, version_dir / "MODEL_CARD.md")

        ModelMetadataManager.save_metadata(metadata, version_dir / "metadata.json")

        return version_dir
