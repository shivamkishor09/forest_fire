"""Service layer orchestrating 24-hour fire risk prediction, persistence, and GeoJSON generation."""

import json
import logging
import uuid
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from services.risk_engine.inference.predictor import RiskPredictor
from services.risk_engine.common.types import RiskClass, RiskPrediction as RiskPredictionContract
from services.risk_engine.models.base import BaseRiskModel

from ..core.config import settings
from ..core.model_manager import risk_model_manager
from ..core.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    ModelUnavailableException,
    FeatureDataUnavailableException,
)
from ..models.risk_prediction import RiskPrediction as RiskPredictionModel
from ..models.grid_cell import GridCell
from ..repositories.risk_repository import RiskRepository
from ..schemas.risk import (
    RiskPredictRequest,
    RiskPredictResponse,
    RiskCellProperties,
    RiskSummaryResponse,
    RiskSummaryDistribution,
)
from ..schemas.geojson import GeoJSONFeature, GeoJSONFeatureCollection
from .region_service import RegionService

logger = logging.getLogger("RiskService")


class RiskService:
    """
    Orchestrates real machine-learning risk inference, PostGIS persistence,
    and GeoJSON spatial representation.
    """

    # In-memory prediction cache for fast access and testing environments:
    # key: (region_id, date_str, model_version) -> dict
    _cache: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.repo = RiskRepository(db) if db is not None else None
        self.region_service = RegionService(db)

    def _resolve_region(self, region_id_or_code: str):
        """Validates and retrieves region detail, or raises ResourceNotFoundException."""
        try:
            return self.region_service.get_region(region_id_or_code)
        except ResourceNotFoundException:
            raise ResourceNotFoundException(
                f"Region '{region_id_or_code}' not found.",
                details={"region_id": region_id_or_code},
            )

    def _resolve_model(self, model_name_or_version: Optional[str] = None) -> BaseRiskModel:
        """Resolves model name/version alias and retrieves cached active model."""
        target_version = model_name_or_version
        if not target_version or target_version in ("xgboost-baseline", "baseline"):
            target_version = getattr(settings, "DEFAULT_RISK_MODEL_VERSION", "risk-xgboost-v001")

        return risk_model_manager.get_model(target_version)

    def _find_processed_dataset(
        self, region_code: str, region_name: str
    ) -> Optional[Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]]:
        """
        Locates Phase 4 processed feature records and 500m grid polygons for a region.
        Searches data/processed subdirectories for manifest matching region code or name.
        """
        repo_root = Path(__file__).resolve().parents[4]
        processed_dir = repo_root / settings.PROCESSED_DATA_DIR

        if not processed_dir.is_dir():
            return None

        # Check candidate directories
        candidates = list(processed_dir.glob("*"))
        for cand in candidates:
            if not cand.is_dir():
                continue

            manifest_path = cand / "manifest.json"
            features_path = cand / "features.parquet"
            if not features_path.is_file():
                features_path = cand / "features.csv"
            grid_geojson_path = cand / "grid_500m.geojson"

            if not features_path.is_file():
                continue

            # Check if this run matches the region
            is_match = False
            if manifest_path.is_file():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        m_data = json.load(f)
                        m_reg_id = str(m_data.get("region_id", "")).lower()
                        m_reg_name = str(m_data.get("region_name", "")).lower()
                        if (
                            region_code.lower() in m_reg_id
                            or m_reg_id in region_code.lower()
                            or region_name.lower() in m_reg_name
                            or "garhwal" in region_code.lower()
                            and "garhwal" in m_reg_id
                        ):
                            is_match = True
                except Exception:
                    pass

            if not is_match and ("garhwal" in region_code.lower() and "garhwal" in cand.name.lower()):
                is_match = True

            if is_match:
                df = (
                    pd.read_parquet(features_path)
                    if features_path.suffix == ".parquet"
                    else pd.read_csv(features_path)
                )

                polygons_map: Dict[str, Dict[str, Any]] = {}
                if grid_geojson_path.is_file():
                    try:
                        with open(grid_geojson_path, "r", encoding="utf-8") as f:
                            grid_json = json.load(f)
                            for feat in grid_json.get("features", []):
                                cid = (
                                    feat.get("id")
                                    or feat.get("properties", {}).get("cell_id")
                                    or feat.get("properties", {}).get("cell_code")
                                )
                                if cid:
                                    polygons_map[str(cid)] = feat.get("geometry", {})
                    except Exception as e:
                        logger.warning(f"Error parsing grid_500m.geojson: {e}")

                return df, polygons_map

        return None

    def predict_risk(self, request: RiskPredictRequest) -> RiskPredictResponse:
        """
        Executes on-demand or batch 24-hour fire risk prediction for a region.
        Idempotent: returns existing predictions unless force_recompute is True.
        """
        region = self._resolve_region(request.region_id)
        model = self._resolve_model(request.model_version or request.model_name)
        model_version = model.model_version
        target_date_str = request.target_date

        try:
            target_dt = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationException(
                f"Invalid date format '{target_date_str}'. Expected YYYY-MM-DD.",
                details={"target_date": target_date_str},
            )

        cache_key = (str(region.id), target_date_str, model_version)

        # 1. Idempotency Check
        if not request.force_recompute:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                return RiskPredictResponse(
                    job_id=cached["job_id"],
                    region_id=request.region_id,
                    target_date=target_date_str,
                    status="COMPLETED",
                    cells_predicted=cached["cells_predicted"],
                    mean_risk_probability=cached["mean_risk_probability"],
                    completed_at=cached["completed_at"],
                    model_version=model_version,
                )

            if self.repo is not None:
                try:
                    existing_count = self.repo.count_predictions_for_date(
                        uuid.UUID(str(region.id)), target_dt, model_version
                    )
                    if existing_count > 0:
                        preds = self.repo.get_predictions_by_region(
                            uuid.UUID(str(region.id)), target_dt, limit=existing_count
                        )
                        mean_p = round(
                            float(np.mean([float(p.risk_probability) for p in preds])), 4
                        )
                        return RiskPredictResponse(
                            job_id=f"risk-job-db-{region.code.lower()}-{target_date_str}",
                            region_id=request.region_id,
                            target_date=target_date_str,
                            status="COMPLETED",
                            cells_predicted=existing_count,
                            mean_risk_probability=mean_p,
                            completed_at=preds[0].generated_at.isoformat() if preds else datetime.now(timezone.utc).isoformat(),
                            model_version=model_version,
                        )
                except Exception as e:
                    logger.debug(f"Database check skipped or failed: {e}")

        # 2. Retrieve Model-Ready Features
        dataset = self._find_processed_dataset(region.code, region.name)
        if dataset is None:
            raise FeatureDataUnavailableException(
                f"No model-ready environmental observations found for region '{region.name}' ({region.code}). "
                "Please run data ingestion and preprocessing pipeline first.",
                details={"region_id": str(region.id), "region_code": region.code},
            )

        df, polygons_map = dataset
        if df.empty:
            raise FeatureDataUnavailableException(
                f"Environmental feature dataset for region '{region.code}' is empty.",
                details={"region_id": str(region.id)},
            )

        # 3. Model/Feature Compatibility Check
        required_features = getattr(model, "feature_names", None) or []
        if required_features:
            missing = [
                f for f in required_features
                if f not in df.columns
                and not f.startswith("fuel_")
                and f not in ("aspect_sin", "aspect_cos", "wind_u_ms", "wind_v_ms")
            ]
            if missing:
                raise ValidationException(
                    f"Feature dataset incompatible with model schema. Missing columns: {missing}",
                    details={"missing_columns": missing, "model_version": model_version},
                )

        # 4. Batch Inference via RiskPredictor
        predictor = RiskPredictor(model)
        now_utc = datetime.now(timezone.utc)
        pred_timestamp = datetime(
            target_dt.year, target_dt.month, target_dt.day, 0, 0, 0, tzinfo=timezone.utc
        )

        predictions: List[RiskPredictionContract] = predictor.predict_dataframe(
            df=df,
            prediction_time=pred_timestamp,
            region_id=str(region.id),
        )

        # Validate probability bounds [0.0, 1.0]
        for p in predictions:
            if not (0.0 <= p.probability <= 1.0):
                raise ValidationException(
                    f"Model generated invalid probability: {p.probability} for cell {p.grid_cell_id}",
                    details={"grid_cell_id": p.grid_cell_id, "probability": p.probability},
                )

        # 5. Database Persistence (when DB is active)
        if self.db is not None and self.repo is not None:
            try:
                from geoalchemy2.elements import WKTElement
                from shapely.geometry import shape

                region_uuid = uuid.UUID(str(region.id))

                if request.force_recompute:
                    self.repo.delete_predictions_for_date(region_uuid, target_dt, model_version)

                # Ensure GridCells exist in DB
                existing_cells = (
                    self.db.query(GridCell.id, GridCell.cell_code)
                    .filter(GridCell.region_id == region_uuid)
                    .all()
                )
                cell_uuid_map = {code: cid for cid, code in existing_cells}

                if not cell_uuid_map:
                    new_grid_cells = []
                    for _, row in df.iterrows():
                        cid_str = str(row["grid_cell_id"])
                        cell_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, cid_str)
                        geom = polygons_map.get(cid_str)
                        wkt_str = (
                            shape(geom).wkt
                            if geom
                            else f"POINT({row['centroid_lon']} {row['centroid_lat']})"
                        )
                        c_lat = float(row.get("centroid_lat", 0.0))
                        c_lon = float(row.get("centroid_lon", 0.0))
                        new_grid_cells.append(
                            GridCell(
                                id=cell_uuid,
                                region_id=region_uuid,
                                cell_code=cid_str,
                                centroid=WKTElement(f"POINT({c_lon} {c_lat})", srid=4326),
                                geometry=WKTElement(wkt_str, srid=4326),
                                resolution_meters=500,
                                elevation_m=float(row.get("elevation_m", 0.0)) if pd.notnull(row.get("elevation_m")) else None,
                                slope_deg=float(row.get("slope_deg", 0.0)) if pd.notnull(row.get("slope_deg")) else None,
                                aspect_deg=float(row.get("aspect_deg", 0.0)) if pd.notnull(row.get("aspect_deg")) else None,
                                fuel_type=str(row.get("fuel_type", "UNKNOWN")),
                            )
                        )
                        cell_uuid_map[cid_str] = cell_uuid

                    self.db.add_all(new_grid_cells)
                    self.db.commit()

                # Insert RiskPrediction records
                db_records = []
                for p in predictions:
                    c_uuid = cell_uuid_map.get(p.grid_cell_id) or uuid.uuid5(uuid.NAMESPACE_DNS, p.grid_cell_id)
                    db_records.append(
                        RiskPredictionModel(
                            id=uuid.uuid4(),
                            grid_cell_id=c_uuid,
                            region_id=region_uuid,
                            valid_for_date=target_dt,
                            risk_probability=p.probability,
                            risk_class=p.risk_class.value,
                            model_version=model_version,
                            generated_at=now_utc,
                        )
                    )
                self.repo.save_predictions_batch(db_records)
            except Exception as e:
                logger.warning(f"Could not persist risk predictions to database: {e}")
                self.db.rollback()

        # 6. Cache Predictions in Memory
        mean_p = round(float(np.mean([p.probability for p in predictions])), 4)
        job_id = f"risk-job-{uuid.uuid4().hex[:8]}"

        self._cache[cache_key] = {
            "job_id": job_id,
            "region_id": str(region.id),
            "target_date": target_date_str,
            "model_version": model_version,
            "predictions": predictions,
            "polygons_map": polygons_map,
            "features_df": df,
            "cells_predicted": len(predictions),
            "mean_risk_probability": mean_p,
            "completed_at": now_utc.isoformat(),
        }

        return RiskPredictResponse(
            job_id=job_id,
            region_id=request.region_id,
            target_date=target_date_str,
            status="COMPLETED",
            cells_predicted=len(predictions),
            mean_risk_probability=mean_p,
            completed_at=now_utc.isoformat(),
            model_version=model_version,
        )

    def get_risk_layer(
        self,
        region_id: str,
        target_date: Optional[str] = None,
        min_risk: Optional[str] = None,
    ) -> GeoJSONFeatureCollection:
        """
        Retrieves 24-hour fire risk predictions formatted as GeoJSON FeatureCollection.
        """
        region = self._resolve_region(region_id)
        target_date_str = target_date or date.today().isoformat()
        default_version = getattr(settings, "DEFAULT_RISK_MODEL_VERSION", "risk-xgboost-v001")
        cache_key = (str(region.id), target_date_str, default_version)

        # Trigger prediction automatically if not yet in cache
        if cache_key not in self._cache:
            self.predict_risk(
                RiskPredictRequest(
                    region_id=region_id,
                    target_date=target_date_str,
                    force_recompute=False,
                    model_version=default_version,
                )
            )

        cached = self._cache[cache_key]
        predictions: List[RiskPredictionContract] = cached["predictions"]
        polygons_map: Dict[str, Dict[str, Any]] = cached["polygons_map"]
        features_df: pd.DataFrame = cached["features_df"]

        # Feature lookup dictionary by cell_id
        feat_lookup = {}
        for _, row in features_df.iterrows():
            cid = str(row["grid_cell_id"])
            feat_lookup[cid] = row

        # Filter by minimum risk threshold if specified
        risk_thresholds = {"LOW": 0.0, "MODERATE": 0.25, "HIGH": 0.50, "EXTREME": 0.75}
        min_threshold = risk_thresholds.get((min_risk or "").upper(), 0.0)

        geojson_features: List[GeoJSONFeature] = []
        for p in predictions:
            if p.probability < min_threshold:
                continue

            cid = p.grid_cell_id
            row_data = feat_lookup.get(cid, {})

            geom = polygons_map.get(cid)
            if not geom:
                # Fallback box around centroid if explicit polygon is missing
                c_lat = float(row_data.get("centroid_lat", 30.2))
                c_lon = float(row_data.get("centroid_lon", 78.7))
                d = 0.0025  # ~250m half-width
                geom = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [round(c_lon - d, 6), round(c_lat - d, 6)],
                            [round(c_lon + d, 6), round(c_lat - d, 6)],
                            [round(c_lon + d, 6), round(c_lat + d, 6)],
                            [round(c_lon - d, 6), round(c_lat + d, 6)],
                            [round(c_lon - d, 6), round(c_lat - d, 6)],
                        ]
                    ],
                }

            # Build enriched cell properties
            props = RiskCellProperties(
                grid_cell_id=cid,
                cell_id=cid,
                risk_probability=p.probability,
                risk_class=p.risk_class.value,
                fwi=float(row_data.get("fwi", 0.0)) if pd.notnull(row_data.get("fwi")) else None,
                fwi_index=float(row_data.get("fwi", 0.0)) if pd.notnull(row_data.get("fwi")) else None,
                fuel_type=str(row_data.get("fuel_type", "UNKNOWN")),
                elevation_m=float(row_data.get("elevation_m", 0.0)) if pd.notnull(row_data.get("elevation_m")) else None,
                elevation=float(row_data.get("elevation_m", 0.0)) if pd.notnull(row_data.get("elevation_m")) else None,
                slope_deg=float(row_data.get("slope_deg", 0.0)) if pd.notnull(row_data.get("slope_deg")) else None,
                slope=float(row_data.get("slope_deg", 0.0)) if pd.notnull(row_data.get("slope_deg")) else None,
                aspect=float(row_data.get("aspect_deg", 0.0)) if pd.notnull(row_data.get("aspect_deg")) else None,
                temperature_c=float(row_data.get("temperature_c", 0.0)) if pd.notnull(row_data.get("temperature_c")) else None,
                relative_humidity_pct=float(row_data.get("relative_humidity_pct", 0.0)) if pd.notnull(row_data.get("relative_humidity_pct")) else None,
                wind_speed_ms=float(row_data.get("wind_speed_ms", 0.0)) if pd.notnull(row_data.get("wind_speed_ms")) else None,
                model_version=p.model_version,
                forecast_start=p.forecast_start,
                forecast_end=p.forecast_end,
                prediction_timestamp=p.prediction_timestamp,
                valid_for_date=p.valid_for_date,
            )

            geojson_features.append(
                GeoJSONFeature(
                    type="Feature",
                    id=cid,
                    geometry=geom,
                    properties=props.model_dump(),
                )
            )

        high_cells = sum(1 for p in predictions if p.risk_class in (RiskClass.HIGH, RiskClass.EXTREME))
        extreme_cells = sum(1 for p in predictions if p.risk_class == RiskClass.EXTREME)

        return GeoJSONFeatureCollection(
            type="FeatureCollection",
            features=geojson_features,
            properties={
                "region_id": str(region.id),
                "region_code": region.code,
                "region_name": region.name,
                "forecast_date": target_date_str,
                "model_version": default_version,
                "generated_at": cached["completed_at"],
                "total_cells": len(predictions),
                "high_risk_cells": high_cells,
                "extreme_risk_cells": extreme_cells,
                "mean_probability": cached["mean_risk_probability"],
            },
        )

    def get_risk_summary(
        self,
        region_id: str,
        target_date: Optional[str] = None,
    ) -> RiskSummaryResponse:
        """
        Retrieves regional aggregation statistics across categorical risk levels.
        """
        region = self._resolve_region(region_id)
        target_date_str = target_date or date.today().isoformat()
        default_version = getattr(settings, "DEFAULT_RISK_MODEL_VERSION", "risk-xgboost-v001")
        cache_key = (str(region.id), target_date_str, default_version)

        if cache_key not in self._cache:
            self.predict_risk(
                RiskPredictRequest(
                    region_id=region_id,
                    target_date=target_date_str,
                    force_recompute=False,
                    model_version=default_version,
                )
            )

        cached = self._cache[cache_key]
        predictions: List[RiskPredictionContract] = cached["predictions"]

        counts = {
            "low": sum(1 for p in predictions if p.risk_class == RiskClass.LOW),
            "moderate": sum(1 for p in predictions if p.risk_class == RiskClass.MODERATE),
            "high": sum(1 for p in predictions if p.risk_class == RiskClass.HIGH),
            "extreme": sum(1 for p in predictions if p.risk_class == RiskClass.EXTREME),
        }

        return RiskSummaryResponse(
            region_id=str(region.id),
            target_date=target_date_str,
            total_cells=len(predictions),
            high_risk_cells=counts["high"],
            extreme_risk_cells=counts["extreme"],
            mean_probability=cached["mean_risk_probability"],
            model_version=default_version,
            risk_distribution=RiskSummaryDistribution(
                low=counts["low"],
                moderate=counts["moderate"],
                high=counts["high"],
                extreme=counts["extreme"],
            ),
        )
