"""Comprehensive Dataset Quality Validator for multi-season fire risk datasets (Phase 9)."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


class DatasetQualityValidator:
    """
    Audits dataset integrity, class distribution, temporal boundaries,
    coordinate validity, feature ranges, and absence of data leakage.
    """

    EXPECTED_FEATURES = [
        "elevation_m", "slope_deg", "aspect_deg", "aspect_sin", "aspect_cos",
        "fuel_type", "ndvi", "ndwi", "temperature_c", "relative_humidity_pct",
        "wind_speed_ms", "wind_direction_deg", "wind_u_ms", "wind_v_ms",
        "precipitation_24h_mm", "precipitation_7d_mm", "fwi",
        "fire_count_7d", "fire_count_30d", "days_since_last_fire",
        "dist_to_recent_fire_m", "target_fire_next_24h"
    ]

    PHYSICAL_RANGES = {
        "temperature_c": (-30.0, 55.0),
        "relative_humidity_pct": (0.0, 100.0),
        "wind_speed_ms": (0.0, 60.0),
        "precipitation_24h_mm": (0.0, 500.0),
        "elevation_m": (0.0, 8848.0),
        "slope_deg": (0.0, 90.0),
        "ndvi": (-1.0, 1.0),
        "ndwi": (-1.0, 1.0),
        "fwi": (0.0, 250.0),
    }

    @classmethod
    def validate_dataset(
        cls,
        df: pd.DataFrame,
        dataset_name: str = "dataset",
        expected_target: str = "target_fire_next_24h",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate single split or combined DataFrame. Returns (is_valid, report_dict).
        """
        issues: List[str] = []
        warnings: List[str] = []

        total_rows = len(df)
        if total_rows == 0:
            return False, {"error": "Dataset is completely empty (0 rows)."}

        # 1. Required columns
        missing_cols = [c for c in cls.EXPECTED_FEATURES if c not in df.columns]
        if missing_cols:
            issues.append(f"Missing required feature columns: {missing_cols}")

        # 2. Target checks
        if expected_target in df.columns:
            targets = df[expected_target].dropna()
            unique_targets = set(targets.unique())
            if not unique_targets.issubset({0, 1, 0.0, 1.0}):
                issues.append(f"Target column '{expected_target}' contains non-binary values: {unique_targets}")
            positives = int((df[expected_target] == 1).sum())
            negatives = int((df[expected_target] == 0).sum())
            pos_ratio = round((positives / total_rows) * 100.0, 2)
            imbalance = round(negatives / max(positives, 1), 2)
        else:
            positives, negatives, pos_ratio, imbalance = 0, 0, 0.0, 0.0
            issues.append(f"Target column '{expected_target}' missing.")

        # 3. Missing values check
        null_counts = df[cls.EXPECTED_FEATURES].isna().sum().to_dict() if not missing_cols else {}
        cols_with_nulls = {k: int(v) for k, v in null_counts.items() if v > 0}
        if cols_with_nulls:
            issues.append(f"Columns with null/missing values: {cols_with_nulls}")

        # 4. Duplicate checks
        id_cols = [c for c in ["grid_cell_id", "reference_date"] if c in df.columns]
        duplicates_count = 0
        if len(id_cols) == 2:
            duplicates_count = int(df.duplicated(subset=id_cols).sum())
            if duplicates_count > 0:
                issues.append(f"Found {duplicates_count} duplicate rows for same (grid_cell_id, reference_date)")

        # 5. Coordinate checks
        if "centroid_lat" in df.columns and "centroid_lon" in df.columns:
            invalid_coords = int(((df["centroid_lat"] < 8.0) | (df["centroid_lat"] > 37.0) |
                                  (df["centroid_lon"] < 68.0) | (df["centroid_lon"] > 98.0)).sum())
            if invalid_coords > 0:
                warnings.append(f"{invalid_coords} rows have coordinates outside Indian land boundaries")

        # 6. Physical range checks
        range_violations = {}
        for col, (rmin, rmax) in cls.PHYSICAL_RANGES.items():
            if col in df.columns:
                viol = int(((df[col] < rmin) | (df[col] > rmax)).sum())
                if viol > 0:
                    range_violations[col] = viol
                    issues.append(f"Feature '{col}' has {viol} values outside plausible range [{rmin}, {rmax}]")

        is_valid = len(issues) == 0

        report = {
            "dataset_name": dataset_name,
            "total_rows": total_rows,
            "positive_samples": positives,
            "negative_samples": negatives,
            "positive_percentage": pos_ratio,
            "imbalance_ratio": imbalance,
            "duplicate_records": duplicates_count,
            "columns_with_nulls": cols_with_nulls,
            "range_violations": range_violations,
            "is_valid": is_valid,
            "issues": issues,
            "warnings": warnings,
        }

        return is_valid, report

    @classmethod
    def audit_splits(
        cls,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        date_col: str = "reference_date",
    ) -> Dict[str, Any]:
        """
        Audits multi-season train/val/test splits for leakage and temporal ordering.
        Guarantees: max(T_train) < min(T_val) <= max(T_val) < min(T_test).
        """
        train_dates = sorted(train_df[date_col].astype(str).unique())
        val_dates = sorted(val_df[date_col].astype(str).unique())
        test_dates = sorted(test_df[date_col].astype(str).unique())

        train_max = max(train_dates) if train_dates else ""
        val_min = min(val_dates) if val_dates else ""
        val_max = max(val_dates) if val_dates else ""
        test_min = min(test_dates) if test_dates else ""

        leakage_train_val = train_max >= val_min if (train_max and val_min) else False
        leakage_val_test = val_max >= test_min if (val_max and test_min) else False
        leakage_detected = leakage_train_val or leakage_val_test

        overlap_dates = set(train_dates).intersection(set(val_dates)).union(
            set(val_dates).intersection(set(test_dates))
        )

        return {
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "train_date_range": [min(train_dates), train_max] if train_dates else [],
            "val_date_range": [val_min, val_max] if val_dates else [],
            "test_date_range": [test_min, max(test_dates)] if test_dates else [],
            "date_overlap": list(overlap_dates),
            "leakage_detected": leakage_detected,
            "temporal_ordering_valid": not leakage_detected,
        }
