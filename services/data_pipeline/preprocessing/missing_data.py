"""Missing data handling, traceable imputation, and quality auditing."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from ..common.types import CanonicalFeatureRecord, QualityReport


# Physically plausible bounds for validation
FEATURE_BOUNDS = {
    "elevation_m": (-500.0, 9000.0),
    "slope_deg": (0.0, 90.0),
    "aspect_deg": (0.0, 360.0),
    "temperature_c": (-40.0, 65.0),
    "relative_humidity_pct": (0.0, 100.0),
    "wind_speed_ms": (0.0, 80.0),
    "precipitation_24h_mm": (0.0, 1500.0),
    "precipitation_7d_mm": (0.0, 3500.0),
    "ndvi": (-1.0, 1.0),
    "ndwi": (-1.0, 1.0),
    "fwi": (0.0, 200.0),
}

# Regional Indian forest defaults when station/raster data is missing
REGIONAL_FEATURE_DEFAULTS = {
    "elevation_m": 1200.0,
    "slope_deg": 15.0,
    "aspect_deg": 180.0,
    "aspect_sin": 0.0,
    "aspect_cos": -1.0,
    "fuel_type": "DECIDUOUS_FOREST",
    "temperature_c": 30.0,
    "relative_humidity_pct": 35.0,
    "wind_speed_ms": 3.5,
    "wind_direction_deg": 180.0,
    "wind_u_ms": 0.0,
    "wind_v_ms": -3.5,
    "precipitation_24h_mm": 0.0,
    "precipitation_7d_mm": 0.0,
    "ndvi": 0.40,
    "ndwi": -0.10,
    "fwi": 25.0,
    "fire_count_7d": 0,
    "fire_count_30d": 0,
    "days_since_last_fire": 365.0,
    "dist_to_recent_fire_m": 50000.0,
}


class MissingDataHandler:
    """Handles missing values, enforces traceability, and flags imputation quality."""

    def __init__(self, imputation_strategy: str = "regional_default"):
        """
        Args:
            imputation_strategy: 'regional_default' or 'median'
        """
        self.imputation_strategy = imputation_strategy

    def audit_and_impute_records(
        self,
        records: List[CanonicalFeatureRecord],
        run_id: str = "pipeline_run",
        reference_date: str = "2026-05-15"
    ) -> Tuple[List[CanonicalFeatureRecord], QualityReport]:
        """
        Audit feature records, apply traceable imputation, and produce a QualityReport.
        """
        if not records:
            report = QualityReport(
                run_id=run_id,
                created_at=reference_date,
                total_records=0,
                clean_records_pct=0.0,
                imputed_records_pct=0.0,
                feature_completeness_pct={},
                imputed_fields_breakdown={},
                out_of_bound_counts={},
                summary_statistics={},
                warnings=["No records provided for auditing."],
            )
            return [], report

        # Compute empirical medians if requested
        empirical_medians: Dict[str, float] = {}
        if self.imputation_strategy == "median":
            for field in REGIONAL_FEATURE_DEFAULTS.keys():
                if field == "fuel_type":
                    continue
                vals = [getattr(r, field) for r in records if getattr(r, field) is not None]
                if vals:
                    empirical_medians[field] = float(np.median(vals))

        imputed_counts: Dict[str, int] = {f: 0 for f in REGIONAL_FEATURE_DEFAULTS.keys()}
        out_of_bounds: Dict[str, int] = {f: 0 for f in FEATURE_BOUNDS.keys()}
        warnings: List[str] = []

        clean_count = 0
        imputed_record_count = 0

        audited_records: List[CanonicalFeatureRecord] = []

        for record in records:
            imputed_fields: List[str] = []

            # Check and impute each field
            for field, default_val in REGIONAL_FEATURE_DEFAULTS.items():
                current_val = getattr(record, field)

                # Null check
                if current_val is None or (isinstance(current_val, float) and np.isnan(current_val)):
                    replacement = empirical_medians.get(field, default_val)
                    setattr(record, field, replacement)
                    imputed_fields.append(field)
                    imputed_counts[field] += 1
                else:
                    # Bound check
                    if field in FEATURE_BOUNDS:
                        min_b, max_b = FEATURE_BOUNDS[field]
                        if not (min_b <= current_val <= max_b):
                            out_of_bounds[field] += 1
                            # Clamp value to physically plausible bound
                            clamped = float(min(max(current_val, min_b), max_b))
                            setattr(record, field, clamped)
                            imputed_fields.append(f"{field}_clamped")

            record.imputed_fields = imputed_fields

            # Assign quality flag
            if len(imputed_fields) == 0:
                record.quality_flag = "CLEAN"
                clean_count += 1
            elif len(imputed_fields) <= 2:
                record.quality_flag = "PARTIALLY_IMPUTED"
                imputed_record_count += 1
            else:
                record.quality_flag = "DEGRADED"
                imputed_record_count += 1

            audited_records.append(record)

        total = len(audited_records)
        clean_pct = round((clean_count / total) * 100.0, 2)
        imputed_pct = round((imputed_record_count / total) * 100.0, 2)

        completeness_pct = {}
        for field, imp_cnt in imputed_counts.items():
            comp = round(((total - imp_cnt) / total) * 100.0, 2)
            completeness_pct[field] = comp
            if comp < 80.0:
                warnings.append(f"Feature '{field}' has high missingness ({100.0 - comp:.1f}% imputed).")

        # Summary statistics for numeric fields
        summary_stats: Dict[str, Dict[str, float]] = {}
        for field in FEATURE_BOUNDS.keys():
            vals = [getattr(r, field) for r in audited_records if getattr(r, field) is not None]
            if vals:
                summary_stats[field] = {
                    "min": round(float(np.min(vals)), 3),
                    "max": round(float(np.max(vals)), 3),
                    "mean": round(float(np.mean(vals)), 3),
                    "std": round(float(np.std(vals)), 3),
                }

        report = QualityReport(
            run_id=run_id,
            created_at=reference_date,
            total_records=total,
            clean_records_pct=clean_pct,
            imputed_records_pct=imputed_pct,
            feature_completeness_pct=completeness_pct,
            imputed_fields_breakdown={k: v for k, v in imputed_counts.items() if v > 0},
            out_of_bound_counts={k: v for k, v in out_of_bounds.items() if v > 0},
            summary_statistics=summary_stats,
            warnings=warnings,
        )

        return audited_records, report
