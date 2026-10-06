"""Validation logic for risk model input features."""

import math
from typing import Any, Dict, List, Set, Union
import numpy as np
import pandas as pd

from ..common.exceptions import FeatureValidationError
from .schema import FEATURE_SPECIFICATIONS
from .ordering import (
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    CANONICAL_RAW_FEATURES,
    KNOWN_FUEL_CLASSES,
    ALL_VALID_FUEL_CLASSES,
)

REQUIRED_CORE_FEATURES: Set[str] = {
    "elevation_m",
    "slope_deg",
    "temperature_c",
    "relative_humidity_pct",
    "wind_speed_ms",
    "ndvi",
    "fwi",
}


class RiskFeatureValidator:
    """Enforces strict presence, data types, physical bounds, and absence of NaN/Infs."""

    @staticmethod
    def validate_features(
        features: Dict[str, Any],
        require_all_canonical: bool = False,
        allow_unknown_fields: bool = False,
    ) -> List[str]:
        """
        Validate feature dictionary. Returns list of error messages (empty if valid).
        """
        errors: List[str] = []

        # Required features check
        expected_set = set(CANONICAL_RAW_FEATURES) if require_all_canonical else REQUIRED_CORE_FEATURES
        missing = expected_set - set(features.keys())
        if missing:
            errors.append(f"Missing required features: {sorted(list(missing))}")
            return errors

        # Unknown fields check
        if not allow_unknown_fields:
            allowed = set(CANONICAL_RAW_FEATURES) | {"grid_cell_id", "region_id", "prediction_time", "cell_code", "reference_date"}
            unknown = set(features.keys()) - allowed
            if unknown:
                errors.append(f"Unexpected unknown features provided: {sorted(list(unknown))}")

        # Bounds and type validation
        for name, spec in FEATURE_SPECIFICATIONS.items():
            if name not in features:
                continue

            val = features[name]

            if spec.data_type in ("float", "int"):
                if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
                    errors.append(f"Feature '{name}' contains null or non-finite value")
                    continue

                try:
                    num_val = float(val)
                except (ValueError, TypeError):
                    errors.append(f"Feature '{name}' cannot be cast to numeric: {val}")
                    continue

                if spec.min_val is not None and num_val < spec.min_val:
                    errors.append(f"{name} out of range [{spec.min_val}, {spec.max_val}]: {num_val}")
                elif spec.max_val is not None and num_val > spec.max_val:
                    errors.append(f"{name} out of range [{spec.min_val}, {spec.max_val}]: {num_val}")

            elif spec.data_type == "categorical":
                if val is not None and str(val).upper() not in ALL_VALID_FUEL_CLASSES:
                    errors.append(f"Unrecognized categorical {name} value: '{val}'. Known: {ALL_VALID_FUEL_CLASSES}")

        return errors

    @classmethod
    def validate_or_raise(
        cls,
        features: Dict[str, Any],
        require_all_canonical: bool = False,
    ) -> None:
        """Validate feature dictionary and raise FeatureValidationError if invalid."""
        errors = cls.validate_features(features, require_all_canonical=require_all_canonical)
        if errors:
            raise FeatureValidationError(f"Feature validation failed: {'; '.join(errors)}")

    @classmethod
    def validate_dataframe(cls, df: pd.DataFrame, require_all_canonical: bool = True) -> None:
        """Validate that a pandas DataFrame contains valid columns and finite values."""
        if df.empty:
            raise FeatureValidationError("Input DataFrame is empty.")

        expected = set(CANONICAL_RAW_FEATURES) if require_all_canonical else REQUIRED_CORE_FEATURES
        missing = expected - set(df.columns)
        if missing:
            raise FeatureValidationError(f"DataFrame is missing required feature columns: {sorted(list(missing))}")

        # Check for non-finite values in numerical features
        for num_col in NUMERICAL_FEATURES:
            if num_col in df.columns:
                null_count = df[num_col].isna().sum()
                if null_count > 0:
                    raise FeatureValidationError(f"Column '{num_col}' contains {null_count} null/NaN values.")
                inf_count = np.isinf(df[num_col]).sum()
                if inf_count > 0:
                    raise FeatureValidationError(f"Column '{num_col}' contains {inf_count} infinite values.")
