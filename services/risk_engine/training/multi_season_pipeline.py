"""Multi-season pipeline implementation for ingestion, dataset building, validation, training, and evaluation."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
import xgboost as xgb

from services.data_pipeline.adapters.base import BoundingBox
from services.data_pipeline.features.dataset_builder import LongitudinalDatasetBuilder
from services.data_pipeline.ingestion.firms_downloader import FirmsDownloader
from services.data_pipeline.ingestion.weather_downloader import WeatherDownloader
from services.data_pipeline.validation.dataset_validator import DatasetQualityValidator
from services.risk_engine.common.types import ModelMetadata
from services.risk_engine.features.schema import RiskFeatureSchema
from services.risk_engine.inference.loader import ModelLoader
from services.risk_engine.inference.predictor import RiskPredictor
from services.risk_engine.training.preprocessing import FeaturePreprocessor


def run_ingestion(
    firms_dir: str = "data/raw/firms",
    weather_dir: str = "data/raw/weather",
    skip_existing: bool = True,
) -> Dict[str, Any]:
    """Ingest real historical NASA FIRMS and ERA5 reanalysis data for benchmark regions."""
    firms = FirmsDownloader()
    weather = WeatherDownloader()

    regions = [
        {
            "name": "Uttarakhand",
            "bbox": BoundingBox(min_lon=78.2, min_lat=29.8, max_lon=80.2, max_lat=31.2),
            "seasons": [
                ("2022-05-01", "2022-05-25"),  # Train
                ("2023-05-01", "2023-05-25"),  # Train
                ("2024-05-01", "2024-05-25"),  # Val
                ("2025-05-01", "2025-05-25"),  # Test
            ],
        },
        {
            "name": "Western_Ghats",
            "bbox": BoundingBox(min_lon=76.0, min_lat=11.3, max_lon=77.0, max_lat=12.1),
            "seasons": [
                ("2023-03-01", "2023-03-20"),  # Train
                ("2024-03-01", "2024-03-20"),  # Val
                ("2025-03-01", "2025-03-20"),  # Test
            ],
        },
    ]

    ingested_firms = []
    ingested_weather = []

    for reg in regions:
        name = reg["name"]
        bbox = reg["bbox"]
        for s_start, s_end in reg["seasons"]:
            print(f"Ingesting {name} ({s_start} to {s_end})...")
            f_file = firms.download_firms_data(
                region_name=name,
                bbox=bbox,
                start_date=s_start,
                end_date=s_end,
                source="VIIRS_SNPP_SP",
                output_dir=firms_dir,
            )
            ingested_firms.append(str(f_file))

            w_file = weather.download_weather_data(
                region_name=name,
                bbox=bbox,
                start_date=s_start,
                end_date=s_end,
                output_dir=weather_dir,
            )
            ingested_weather.append(str(w_file))

    return {
        "status": "success",
        "firms_files": len(ingested_firms),
        "weather_files": len(ingested_weather),
    }


def run_build_dataset(
    raw_firms_dir: str = "data/raw/firms",
    raw_weather_dir: str = "data/raw/weather",
    output_dir: str = "data/datasets/multiseason_v2",
    negative_ratio: int = 15,
    min_confidence: float = 50.0,
    random_seed: int = 42,
) -> Dict[str, Any]:
    """Construct longitudinal multi-season dataset with strict anti-leakage."""
    builder = LongitudinalDatasetBuilder(
        raw_firms_dir=raw_firms_dir,
        raw_weather_dir=raw_weather_dir,
        output_dir=output_dir,
        negative_ratio=negative_ratio,
        min_confidence=min_confidence,
        random_seed=random_seed,
    )
    return builder.build_dataset()


def run_validate_dataset(
    dataset_dir: str = "data/datasets/multiseason_v2",
) -> Dict[str, Any]:
    """Validate dataset quality across all splits."""
    d_dir = Path(dataset_dir)
    train_df = pd.read_parquet(d_dir / "train.parquet")
    val_df = pd.read_parquet(d_dir / "val.parquet")
    test_df = pd.read_parquet(d_dir / "test.parquet")

    validator = DatasetQualityValidator()
    train_valid, train_report = validator.validate_dataset(train_df, "train")
    val_valid, val_report = validator.validate_dataset(val_df, "validation")
    test_valid, test_report = validator.validate_dataset(test_df, "test")
    split_audit = validator.audit_splits(train_df, val_df, test_df)

    report = {
        "status": "passed" if (train_valid and val_valid and test_valid and split_audit["temporal_ordering_valid"]) else "failed",
        "splits_audit": split_audit,
        "train_quality": train_report,
        "val_quality": val_report,
        "test_quality": test_report,
    }
    report_file = d_dir / "data_quality_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report



def run_train(
    dataset_dir: str = "data/datasets/multiseason_v2",
    model_version: str = "risk-xgboost-v002",
    output_model_dir: str = "models/risk/risk-xgboost-v002",
) -> Dict[str, Any]:
    """Train calibrated XGBoost risk model with imbalance weighting and threshold freezing."""
    d_dir = Path(dataset_dir)
    train_df = pd.read_parquet(d_dir / "train.parquet")
    val_df = pd.read_parquet(d_dir / "val.parquet")

    preprocessor = FeaturePreprocessor()
    X_train = preprocessor.transform_dataframe(train_df)
    y_train = train_df["target_fire_next_24h"].astype(int).values

    X_val = preprocessor.transform_dataframe(val_df)
    y_val = val_df["target_fire_next_24h"].astype(int).values

    # Train XGBoost with optimal class imbalance weighting (scale_pos_weight=8.0)
    clf = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        scale_pos_weight=8.0,
    )
    clf.fit(X_train, y_train)


    # Isotonic calibration on validation split
    try:
        from sklearn.frozen import FrozenEstimator
        calibrator = CalibratedClassifierCV(estimator=FrozenEstimator(clf), method="isotonic")
    except ImportError:
        calibrator = CalibratedClassifierCV(estimator=clf, method="isotonic", cv="prefit")

    calibrator.fit(X_val, y_val)

    # Freeze operational alert thresholds
    thresholds = {
        "ALERT_THRESHOLD": 0.10,
        "LOW_MAX": 0.07,
        "MODERATE_MAX": 0.10,
        "HIGH_MAX": 0.18,
    }

    out_dir = Path(output_model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save model and artifacts
    clf.save_model(str(out_dir / "model.json"))
    joblib.dump(calibrator, str(out_dir / "calibrator.joblib"))

    with open(out_dir / "thresholds.json", "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=2)

    with open(out_dir / "preprocessor.json", "w", encoding="utf-8") as f:
        json.dump(preprocessor.to_dict(), f, indent=2)

    schema = RiskFeatureSchema()
    with open(out_dir / "feature_schema.json", "w", encoding="utf-8") as f:
        json.dump(schema.model_dump(), f, indent=2)

    meta = {
        "model_name": "risk-xgboost",
        "model_version": model_version,
        "algorithm": "XGBoost + CalibratedClassifierCV",
        "model_type": "xgboost_calibrated",
        "description": "Calibrated 24-hour fire risk model trained on multi-season historical data (2022-2023) with isotonic calibration on 2024.",
        "author": "Wildfire Defense Operations & ML Team",
        "dataset_version": "multiseason_v2",
        "features": preprocessor.final_feature_names,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hyperparameters": {
            "n_estimators": 150,
            "max_depth": 5,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "scale_pos_weight": 8.0,
            "calibration_method": "isotonic",
            "best_iteration": int(getattr(clf, "best_iteration", 149)),
        },
        "thresholds": thresholds,
    }

    with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {"status": "trained", "model_version": model_version, "output_dir": str(out_dir)}


def run_evaluate(
    dataset_dir: str = "data/datasets/multiseason_v2",
    model_version: str = "risk-xgboost-v002",
    model_dir: str = "models/risk/risk-xgboost-v002",
) -> Dict[str, Any]:
    """Evaluate calibrated model on strictly unseen 2025 test season."""
    d_dir = Path(dataset_dir)
    m_dir = Path(model_dir)

    test_df = pd.read_parquet(d_dir / "test.parquet")

    clf = xgb.XGBClassifier()
    clf.load_model(str(m_dir / "model.json"))
    calibrator = joblib.load(str(m_dir / "calibrator.joblib"))

    with open(m_dir / "thresholds.json", "r", encoding="utf-8") as f:
        thresholds = json.load(f)

    with open(m_dir / "preprocessor.json", "r", encoding="utf-8") as f:
        prep_dict = json.load(f)

    preprocessor = FeaturePreprocessor.from_dict(prep_dict)
    X_test = preprocessor.transform_dataframe(test_df)
    y_test = test_df["target_fire_next_24h"].astype(int).values

    probs_test = calibrator.predict_proba(X_test)[:, 1]
    alert_thresh = thresholds.get("ALERT_THRESHOLD", 0.10)
    preds_test = (probs_test >= alert_thresh).astype(int)

    acc = accuracy_score(y_test, preds_test)
    prec = precision_score(y_test, preds_test, zero_division=0)
    rec = recall_score(y_test, preds_test, zero_division=0)
    f1 = f1_score(y_test, preds_test, zero_division=0)
    roc_auc = roc_auc_score(y_test, probs_test)
    pr_auc = average_precision_score(y_test, probs_test)
    brier = brier_score_loss(y_test, probs_test)

    cm = confusion_matrix(y_test, preds_test, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    spec = tn / (tn + fp)
    fpr = fp / (fp + tn)

    # Regional breakdown
    regions = test_df["region_id"].unique()
    reg_breakdown = {}
    for reg in regions:
        mask = (test_df["region_id"] == reg).values
        reg_y = y_test[mask]
        reg_p = preds_test[mask]
        reg_probs = probs_test[mask]
        reg_cm = confusion_matrix(reg_y, reg_p, labels=[0, 1]).ravel()
        reg_breakdown[reg] = {
            "samples": int(mask.sum()),
            "positives": int((reg_y == 1).sum()),
            "accuracy": float(accuracy_score(reg_y, reg_p)),
            "precision": float(precision_score(reg_y, reg_p, zero_division=0)),
            "recall": float(recall_score(reg_y, reg_p, zero_division=0)),
            "f1": float(f1_score(reg_y, reg_p, zero_division=0)),
            "roc_auc": float(roc_auc_score(reg_y, reg_probs)) if (reg_y == 1).sum() > 0 else 0.0,
            "pr_auc": float(average_precision_score(reg_y, reg_probs)),
            "confusion_matrix": {"tn": int(reg_cm[0]), "fp": int(reg_cm[1]), "fn": int(reg_cm[2]), "tp": int(reg_cm[3])},
        }

    results = {
        "model_version": model_version,
        "dataset_evaluated": "test.parquet (strictly unseen 2025 season)",
        "samples": len(test_df),
        "positives": int((y_test == 1).sum()),
        "negatives": int((y_test == 0).sum()),
        "alert_threshold": alert_thresh,
        "metrics": {
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1_score": float(f1),
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc),
            "brier_score": float(brier),
            "specificity": float(spec),
            "false_positive_rate": float(fpr),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        },
        "regional_breakdown": reg_breakdown,
    }

    with open(m_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


def run_all(
    firms_dir: str = "data/raw/firms",
    weather_dir: str = "data/raw/weather",
    dataset_dir: str = "data/datasets/multiseason_v2",
    model_version: str = "risk-xgboost-v002",
    model_dir: str = "models/risk/risk-xgboost-v002",
) -> Dict[str, Any]:
    """Execute end-to-end multi-season pipeline from raw satellite data to evaluated model."""
    print("=== Step 1/5: INGESTING HISTORICAL DATA ===")
    ingest_res = run_ingestion(firms_dir=firms_dir, weather_dir=weather_dir)
    print("Ingestion complete.")

    print("\n=== Step 2/5: BUILDING MULTI-SEASON DATASET ===")
    build_res = run_build_dataset(raw_firms_dir=firms_dir, raw_weather_dir=weather_dir, output_dir=dataset_dir)
    print("Dataset build complete.")

    print("\n=== Step 3/5: VALIDATING DATA QUALITY ===")
    val_res = run_validate_dataset(dataset_dir=dataset_dir)
    print("Validation complete.")

    print("\n=== Step 4/5: TRAINING CALIBRATED MODEL ===")
    train_res = run_train(dataset_dir=dataset_dir, model_version=model_version, output_model_dir=model_dir)
    print("Training complete.")

    print("\n=== Step 5/5: EVALUATING ON UNSEEN 2025 SEASON ===")
    eval_res = run_evaluate(dataset_dir=dataset_dir, model_version=model_version, model_dir=model_dir)
    print("Evaluation complete.")

    return {
        "status": "success",
        "ingest": ingest_res,
        "build": build_res,
        "validate": val_res,
        "train": train_res,
        "evaluate": eval_res,
    }
