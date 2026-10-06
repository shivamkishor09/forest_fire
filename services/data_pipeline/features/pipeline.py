"""End-to-end feature pipeline orchestrating spatial/temporal alignment, feature engineering, and quality auditing."""

from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from ..common.types import (
    GridCellDefinition,
    CanonicalFireObservation,
    CanonicalWeatherObservation,
    CanonicalVegetationObservation,
    CanonicalTerrainObservation,
    CanonicalFeatureRecord,
    QualityReport,
)
from ..grid.indexing import SpatialGridIndex
from ..preprocessing.spatial_alignment import SpatialAligner
from ..preprocessing.temporal_alignment import TemporalAligner
from ..preprocessing.missing_data import MissingDataHandler
from .weather import compute_wind_vector_components
from .vegetation import standardize_fuel_class
from .terrain import compute_cyclical_aspect
from .fire_weather import FwiCalculator
from .fire_history import FireHistoryExtractor
from .target import TargetLabeler


class FeaturePipeline:
    """Orchestrates end-to-end extraction and harmonization of spatial-temporal features."""

    def __init__(
        self,
        strict_anti_leakage: bool = True,
        imputation_strategy: str = "regional_default",
    ):
        self.strict_anti_leakage = strict_anti_leakage
        self.missing_handler = MissingDataHandler(imputation_strategy=imputation_strategy)

    def process(
        self,
        cells: List[GridCellDefinition],
        reference_time: datetime,
        fire_observations: List[CanonicalFireObservation],
        weather_observations: List[CanonicalWeatherObservation],
        vegetation_observations: List[CanonicalVegetationObservation],
        terrain_observations: List[CanonicalTerrainObservation],
        generate_target: bool = False,
        run_id: str = "run_default",
    ) -> Tuple[List[CanonicalFeatureRecord], QualityReport]:
        """
        Execute end-to-end feature engineering pipeline for given reference cutoff time T_ref.
        """
        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)
        ref_date_str = reference_time.strftime("%Y-%m-%d")

        # 1. Temporal aligner & anti-leakage guards for feature observations
        temp_aligner = TemporalAligner(reference_time, strict_anti_leakage=self.strict_anti_leakage)

        # Historical / feature observations strictly <= T_ref
        valid_fires = temp_aligner.filter_and_guard_observations(fire_observations, "detection_time")
        valid_weather = temp_aligner.filter_and_guard_observations(weather_observations, "timestamp")
        valid_veg = temp_aligner.filter_and_guard_observations(vegetation_observations, "observation_time")

        # 2. Spatial indexing & alignment
        spatial_index = SpatialGridIndex(cells)
        spatial_aligner = SpatialAligner(spatial_index)

        cell_fires_map = spatial_aligner.align_fire_observations(valid_fires)
        weather_by_cell = spatial_aligner.align_weather_observations(valid_weather)
        veg_by_cell = spatial_aligner.align_vegetation_observations(valid_veg)
        terrain_by_cell = spatial_aligner.align_terrain_observations(terrain_observations)

        # 3. Fire history extractor
        fire_hist_extractor = FireHistoryExtractor(reference_time)

        # 4. Optional target labels for training / evaluation (evaluates future window T_ref < T <= T_ref + 24h)
        target_labels: Dict[str, int] = {}
        if generate_target:
            target_labeler = TargetLabeler(reference_time, target_window_hours=24)
            # Pass ALL fires so it can isolate the future window
            target_labels = target_labeler.compute_labels_for_cells(cells, fire_observations, spatial_index)

        raw_feature_records: List[CanonicalFeatureRecord] = []

        # 5. Build feature record for each cell
        for cell in cells:
            cid = cell.cell_id

            # Terrain features
            t_data = terrain_by_cell.get(cid, {})
            elev = t_data.get("elevation_m")
            slope = t_data.get("slope_deg")
            aspect = t_data.get("aspect_deg")
            aspect_sin, aspect_cos = compute_cyclical_aspect(aspect)

            # Vegetation features
            v_data = veg_by_cell.get(cid, {})
            raw_fuel = v_data.get("fuel_type", "UNKNOWN")
            fuel_type = standardize_fuel_class(raw_fuel)
            ndvi = v_data.get("ndvi")
            ndwi = v_data.get("ndwi")

            # Weather features
            w_data = weather_by_cell.get(cid, {})
            temp_c = w_data.get("temperature_c")
            rh_pct = w_data.get("relative_humidity_pct")
            wind_spd = w_data.get("wind_speed_ms")
            wind_dir = w_data.get("wind_direction_deg")
            wind_u = w_data.get("wind_u_ms")
            wind_v = w_data.get("wind_v_ms")
            precip_24h = w_data.get("precipitation_mm", 0.0)

            if wind_u is None and wind_spd is not None and wind_dir is not None:
                wind_u, wind_v = compute_wind_vector_components(wind_spd, wind_dir)

            # Lookback weather: 7-day precipitation
            precip_7d = precip_24h  # Default to 24h if multi-day history not fed

            # Fire history for cell
            cell_fires = cell_fires_map.get(cid, [])
            fire_hist_metrics = temp_aligner.compute_fire_history_metrics(cell_fires)
            days_since = fire_hist_metrics["days_since_last_fire"]
            if days_since is None:
                days_since = 365.0  # Censored observation: no fire detected in historical window

            dist_to_fire = fire_hist_extractor.compute_proximity_to_recent_fires(cell, valid_fires)
            if dist_to_fire is None:
                dist_to_fire = 50000.0  # Regional distance baseline when no active fires present

            # Fire Weather Index (FWI)
            fwi_val = None
            if temp_c is not None and rh_pct is not None and wind_spd is not None:
                fwi_results = FwiCalculator.calculate_all_indices(
                    temperature_c=temp_c,
                    rh_pct=rh_pct,
                    wind_speed_ms=wind_spd,
                    precipitation_24h_mm=precip_24h or 0.0,
                    month=reference_time.month,
                )
                fwi_val = fwi_results.get("fwi")

            target_val = target_labels.get(cid) if generate_target else None

            record = CanonicalFeatureRecord(
                grid_cell_id=cid,
                cell_code=cell.cell_code,
                region_id=cell.region_id,
                reference_date=ref_date_str,
                centroid_lat=cell.centroid_lat,
                centroid_lon=cell.centroid_lon,
                elevation_m=elev,
                slope_deg=slope,
                aspect_deg=aspect,
                aspect_sin=aspect_sin,
                aspect_cos=aspect_cos,
                fuel_type=fuel_type,
                ndvi=ndvi,
                ndwi=ndwi,
                temperature_c=temp_c,
                relative_humidity_pct=rh_pct,
                wind_speed_ms=wind_spd,
                wind_direction_deg=wind_dir,
                wind_u_ms=wind_u,
                wind_v_ms=wind_v,
                precipitation_24h_mm=precip_24h,
                precipitation_7d_mm=precip_7d,
                fwi=fwi_val,
                fire_count_7d=fire_hist_metrics["fire_count_7d"],
                fire_count_30d=fire_hist_metrics["fire_count_30d"],
                days_since_last_fire=days_since,
                dist_to_recent_fire_m=dist_to_fire,
                target_fire_next_24h=target_val,
            )
            raw_feature_records.append(record)

        # 6. Traceable missing-data handling and quality auditing
        audited_records, quality_report = self.missing_handler.audit_and_impute_records(
            raw_feature_records,
            run_id=run_id,
            reference_date=ref_date_str,
        )

        return audited_records, quality_report

    @staticmethod
    def records_to_dataframe(records: List[CanonicalFeatureRecord]) -> pd.DataFrame:
        """Convert canonical feature records into a deterministic, sorted pandas DataFrame."""
        rows = [r.model_dump() for r in records]
        df = pd.DataFrame(rows)
        if not df.empty and "grid_cell_id" in df.columns:
            # Deterministic sorting
            df = df.sort_values(by=["reference_date", "grid_cell_id"]).reset_index(drop=True)
        return df
