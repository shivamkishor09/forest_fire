"""Dataset loading, integrity validation, and target distribution auditing."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

from ..common.exceptions import (
    FeatureValidationError,
    InsufficientPositivesError,
    RiskEngineError,
)
from ..features.ordering import NUMERICAL_FEATURES, CATEGORICAL_FEATURES, CANONICAL_RAW_FEATURES


class TrainingDataset:
    """Represents a validated tabular risk-model training dataset."""

    def __init__(
        self,
        df: pd.DataFrame,
        dataset_id: str = "dataset_default",
        target_col: str = "target_fire_next_24h",
    ):
        self.df = df.copy()
        self.dataset_id = dataset_id
        self.target_col = target_col
        self._validate_and_audit()

    @classmethod
    def from_file(
        cls,
        file_path: Union[str, Path],
        target_col: str = "target_fire_next_24h",
        min_positives: int = 1,
    ) -> "TrainingDataset":
        """Load and validate dataset from CSV or Parquet file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Training dataset not found: {path}")

        if path.suffix in (".parquet", ".pq"):
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path)

        dataset_id = path.stem
        dataset = cls(df=df, dataset_id=dataset_id, target_col=target_col)

        if dataset.class_distribution["positive_samples"] < min_positives:
            raise InsufficientPositivesError(
                f"Dataset contains {dataset.class_distribution['positive_samples']} positive fire samples, "
                f"which is fewer than required minimum ({min_positives}). Cannot train a meaningful model."
            )

        return dataset

    def _validate_and_audit(self) -> None:
        """Validate structure, identifiers, duplicate rows, and target column."""
        if self.df.empty:
            raise FeatureValidationError("Dataset is empty (0 rows).")

        # 1. Target column presence and binary validity
        if self.target_col not in self.df.columns:
            raise FeatureValidationError(f"Target column '{self.target_col}' not found in dataset.")

        targets = self.df[self.target_col].dropna()
        if targets.empty:
            raise FeatureValidationError(f"Target column '{self.target_col}' contains only nulls.")

        unique_targets = set(targets.unique())
        if not unique_targets.issubset({0, 1, 0.0, 1.0}):
            raise FeatureValidationError(
                f"Target column '{self.target_col}' must be binary 0 or 1, found values: {unique_targets}"
            )

        # 2. Key identifiers check
        required_ids = ["grid_cell_id", "reference_date"]
        for id_col in required_ids:
            if id_col not in self.df.columns:
                raise FeatureValidationError(f"Required identifier column '{id_col}' is missing.")
            if self.df[id_col].isna().any():
                raise FeatureValidationError(f"Identifier column '{id_col}' contains null values.")

        # 3. Duplicate checks on (grid_cell_id, reference_date)
        duplicates = self.df.duplicated(subset=["grid_cell_id", "reference_date"]).sum()
        if duplicates > 0:
            raise FeatureValidationError(
                f"Found {duplicates} duplicate records for same (grid_cell_id, reference_date) pair."
            )

        # 4. Check presence of canonical raw features
        missing_features = [col for col in CANONICAL_RAW_FEATURES if col not in self.df.columns]
        if missing_features:
            raise FeatureValidationError(
                f"Dataset missing required canonical feature columns: {sorted(missing_features)}"
            )

        # 5. Audit target class distribution
        y = self.df[self.target_col].astype(int)
        pos = int((y == 1).sum())
        neg = int((y == 0).sum())
        total = len(y)
        pos_ratio = round((pos / total) * 100.0, 3)
        neg_ratio = round((neg / total) * 100.0, 3)

        self.class_distribution: Dict[str, Any] = {
            "total_samples": total,
            "positive_samples": pos,
            "negative_samples": neg,
            "positive_percentage": pos_ratio,
            "negative_percentage": neg_ratio,
            "imbalance_ratio": round(neg / max(pos, 1), 2),
        }

    @property
    def temporal_range(self) -> Dict[str, str]:
        """Return earliest and latest reference_date in dataset."""
        dates = self.df["reference_date"].astype(str)
        return {
            "start_date": str(dates.min()),
            "end_date": str(dates.max()),
        }
