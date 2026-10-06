"""Feature transformation, encoding, and ordering for ML training and inference."""

import math
import json
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from ..features.ordering import NUMERICAL_FEATURES, KNOWN_FUEL_CLASSES, normalize_fuel_class
from ..common.exceptions import FeatureValidationError


class FeaturePreprocessor:
    """
    Transforms raw canonical feature records into a model-ready numerical feature matrix.
    Ensures identical feature ordering, categorical one-hot encoding, and missing-data alignment
    between training and inference.
    """

    def __init__(self, known_fuel_classes: Optional[List[str]] = None):
        self.numerical_features = list(NUMERICAL_FEATURES)
        self.known_fuel_classes = list(known_fuel_classes or KNOWN_FUEL_CLASSES)
        self.fuel_columns = [f"fuel_{c}" for c in self.known_fuel_classes]
        self.final_feature_names = self.numerical_features + self.fuel_columns

    def transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform a pandas DataFrame of raw feature columns into the canonical ML matrix.
        Preserves deterministic column ordering. Automatically derives cyclical aspect
        and wind components if not directly provided.
        """
        if df.empty:
            raise FeatureValidationError("Cannot transform empty DataFrame.")

        working_df = df.copy()

        # Derive cyclical aspect if missing
        if "aspect_sin" not in working_df.columns and "aspect_deg" in working_df.columns:
            rad = np.radians(pd.to_numeric(working_df["aspect_deg"], errors="coerce"))
            working_df["aspect_sin"] = np.sin(rad)
            working_df["aspect_cos"] = np.cos(rad)

        # Derive wind components if missing
        if (
            "wind_u_ms" not in working_df.columns
            and "wind_speed_ms" in working_df.columns
            and "wind_direction_deg" in working_df.columns
        ):
            sp = pd.to_numeric(working_df["wind_speed_ms"], errors="coerce")
            wd_rad = np.radians(pd.to_numeric(working_df["wind_direction_deg"], errors="coerce"))
            working_df["wind_u_ms"] = -sp * np.sin(wd_rad)
            working_df["wind_v_ms"] = -sp * np.cos(wd_rad)

        # 1. Extract numerical features in exact order
        out_df = pd.DataFrame(index=working_df.index)
        for col in self.numerical_features:
            if col in working_df.columns:
                out_df[col] = pd.to_numeric(working_df[col], errors="coerce").astype(float)
            else:
                raise FeatureValidationError(f"Missing required numerical column '{col}'")

        # 2. One-hot encode fuel_type against fixed categories
        fuel_series = working_df.get("fuel_type", pd.Series(["UNKNOWN"] * len(working_df), index=working_df.index)).astype(str).apply(normalize_fuel_class)
        for c, col_name in zip(self.known_fuel_classes, self.fuel_columns):
            out_df[col_name] = (fuel_series == c).astype(float)

        return out_df[self.final_feature_names]

    def transform_dict(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Transform a single feature dictionary into a 1 x D numpy array for inference.
        """
        feat = dict(features)
        # Derive cyclical aspect if missing
        if "aspect_sin" not in feat and "aspect_deg" in feat and feat["aspect_deg"] is not None:
            rad = math.radians(float(feat["aspect_deg"]))
            feat["aspect_sin"] = math.sin(rad)
            feat["aspect_cos"] = math.cos(rad)

        # Derive wind components if missing
        if "wind_u_ms" not in feat and "wind_speed_ms" in feat and "wind_direction_deg" in feat:
            if feat["wind_speed_ms"] is not None and feat["wind_direction_deg"] is not None:
                sp = float(feat["wind_speed_ms"])
                rad = math.radians(float(feat["wind_direction_deg"]))
                feat["wind_u_ms"] = -sp * math.sin(rad)
                feat["wind_v_ms"] = -sp * math.cos(rad)

        row_vals = []
        for col in self.numerical_features:
            val = feat.get(col)
            if val is None:
                raise FeatureValidationError(f"Missing required numerical feature '{col}'")
            try:
                row_vals.append(float(val))
            except (ValueError, TypeError):
                raise FeatureValidationError(f"Feature '{col}' value '{val}' cannot be converted to float")

        raw_fuel = normalize_fuel_class(str(feat.get("fuel_type", "UNKNOWN")))
        for c in self.known_fuel_classes:
            row_vals.append(1.0 if raw_fuel == c else 0.0)

        return np.array([row_vals], dtype=np.float32)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize preprocessor configuration."""
        return {
            "numerical_features": self.numerical_features,
            "known_fuel_classes": self.known_fuel_classes,
            "fuel_columns": self.fuel_columns,
            "final_feature_names": self.final_feature_names,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeaturePreprocessor":
        """Deserialize preprocessor configuration."""
        return cls(known_fuel_classes=data.get("known_fuel_classes"))
