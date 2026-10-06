"""Canonical domain models and data types for the 24-hour fire risk engine."""

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RiskClass(str, Enum):
    """Categorical fire susceptibility classification."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class RiskPrediction(BaseModel):
    """
    Canonical output contract for 24-hour fire risk prediction on a 500m grid cell.
    Conforms to DATA_CONTRACTS.md and Phase 5 specifications.
    """
    grid_cell_id: str = Field(..., description="Unique cell identifier")
    probability: float = Field(..., ge=0.0, le=1.0, description="Estimated 24h fire probability [0.0, 1.0]")
    risk_class: RiskClass = Field(..., description="Categorical classification (LOW, MODERATE, HIGH, EXTREME)")
    model_version: str = Field(..., description="Version of model producing forecast (e.g. risk-xgboost-v001)")
    prediction_timestamp: str = Field(..., description="UTC timestamp of inference generation (ISO 8601)")
    forecast_start: str = Field(..., description="Start of 24h forecast window (ISO 8601)")
    forecast_end: str = Field(..., description="End of 24h forecast window (ISO 8601)")
    region_id: Optional[str] = Field(None, description="Forest division or administrative region ID")
    valid_for_date: Optional[str] = Field(None, description="YYYY-MM-DD target forecast date")
    feature_importances: Optional[Dict[str, float]] = Field(None, description="Top descriptive feature contributions")


class RiskInferenceInput(BaseModel):
    """Input structure for grid cell risk prediction."""
    grid_cell_id: str
    features: Dict[str, Any]
    region_id: Optional[str] = None
    prediction_time: Optional[datetime] = None


class ModelMetadata(BaseModel):
    """Metadata tracking model version, lineage, training configuration, and metrics."""
    model_name: str
    model_version: str
    algorithm: str  # "XGBoost", "RandomForest"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    training_period: Dict[str, str] = Field(default_factory=dict)
    validation_period: Dict[str, str] = Field(default_factory=dict)
    dataset_version: str = "dataset_v1"
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    feature_names: List[str] = Field(default_factory=list)
    random_seed: int = 42
    imbalance_strategy: str = "scale_pos_weight"
    positive_weight_ratio: float = 1.0
    metrics: Dict[str, float] = Field(default_factory=dict)
    confusion_matrix: Dict[str, int] = Field(default_factory=dict)
    top_feature_importance: Dict[str, float] = Field(default_factory=dict)


class EvaluationMetrics(BaseModel):
    """Classification performance metrics computed on validation or test split."""
    total_samples: int
    positive_samples: int
    negative_samples: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: Optional[float] = None
    pr_auc: Optional[float] = None
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
