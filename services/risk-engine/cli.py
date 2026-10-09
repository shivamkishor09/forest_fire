"""Command-line interface (CLI) for data ingestion, dataset building, validation, training, and evaluation."""

import argparse
import json
import logging
import sys
from pathlib import Path
import pandas as pd

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from services.risk_engine.common.logging import get_logger
from services.risk_engine.common.config import settings
from services.risk_engine.training.pipeline import TrainingPipeline
from services.risk_engine.training.dataset import TrainingDataset
from services.risk_engine.evaluation.evaluation import RiskModelEvaluator
from services.risk_engine.evaluation.reports import EvaluationReportGenerator
from services.risk_engine.inference.loader import ModelLoader
from services.risk_engine.inference.predictor import RiskPredictor, RiskInferenceInput
from services.risk_engine.models.registry import ModelRegistry
from services.risk_engine.training.multi_season_pipeline import (
    run_ingestion,
    run_build_dataset,
    run_validate_dataset,
    run_train,
    run_evaluate,
    run_all,
)

logger = get_logger("CLI")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Predictive Forest Fire Risk Platform - CLI (Data Pipeline & Risk Engine)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest raw historical NASA FIRMS and ERA5 weather data")
    ingest_parser.add_argument("--firms-dir", type=str, default="data/raw/firms")
    ingest_parser.add_argument("--weather-dir", type=str, default="data/raw/weather")

    # Build dataset command
    build_parser = subparsers.add_parser("build-dataset", help="Build multi-season longitudinal dataset")
    build_parser.add_argument("--firms-dir", type=str, default="data/raw/firms")
    build_parser.add_argument("--weather-dir", type=str, default="data/raw/weather")
    build_parser.add_argument("--output-dir", type=str, default="data/datasets/multiseason_v2")
    build_parser.add_argument("--negative-ratio", type=int, default=15)
    build_parser.add_argument("--min-confidence", type=float, default=50.0)

    # Validate dataset command
    val_parser = subparsers.add_parser("validate-dataset", help="Validate multi-season dataset quality")
    val_parser.add_argument("--dataset-dir", type=str, default="data/datasets/multiseason_v2")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train 24-hour XGBoost fire risk model")
    train_parser.add_argument("--input", type=str, default="data/datasets/multiseason_v2")
    train_parser.add_argument("--model-version", type=str, default="risk-xgboost-v002")
    train_parser.add_argument("--train-ratio", type=float, default=0.75)
    train_parser.add_argument("--cutoff-date", type=str, default=None)
    train_parser.add_argument("--include-rf", action="store_true", help="Also train Random Forest baseline")

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate trained model on a dataset")
    eval_parser.add_argument("--model-version", type=str, default="risk-xgboost-v002")
    eval_parser.add_argument("--dataset", type=str, default="data/datasets/multiseason_v2")
    eval_parser.add_argument("--threshold", type=float, default=0.10)

    # All command
    all_parser = subparsers.add_parser("all", help="Execute complete pipeline end-to-end")
    all_parser.add_argument("--firms-dir", type=str, default="data/raw/firms")
    all_parser.add_argument("--weather-dir", type=str, default="data/raw/weather")
    all_parser.add_argument("--dataset-dir", type=str, default="data/datasets/multiseason_v2")
    all_parser.add_argument("--model-version", type=str, default="risk-xgboost-v002")

    # Predict command
    pred_parser = subparsers.add_parser("predict", help="Run 24-hour fire risk inference")
    pred_parser.add_argument("--model-version", type=str, default=None)
    pred_parser.add_argument("--input", type=str, required=True)
    pred_parser.add_argument("--output", type=str, default=None)

    # Info command
    info_parser = subparsers.add_parser("info", help="Display metadata of registered model version")
    info_parser.add_argument("--model-version", type=str, default=None)

    return parser.parse_args()


def handle_ingest(args):
    print("Executing historical satellite and weather ingestion...")
    result = run_ingestion(firms_dir=args.firms_dir, weather_dir=args.weather_dir)
    print(json.dumps(result, indent=2))


def handle_build_dataset(args):
    print(f"Building longitudinal dataset in {args.output_dir}...")
    result = run_build_dataset(
        raw_firms_dir=args.firms_dir,
        raw_weather_dir=args.weather_dir,
        output_dir=args.output_dir,
        negative_ratio=args.negative_ratio,
        min_confidence=args.min_confidence,
    )
    print(json.dumps(result, indent=2))


def handle_validate_dataset(args):
    print(f"Validating dataset in {args.dataset_dir}...")
    report = run_validate_dataset(dataset_dir=args.dataset_dir)
    print(json.dumps(report, indent=2))


def handle_train(args):
    inp_path = Path(args.input)
    if inp_path.is_dir() or args.model_version == "risk-xgboost-v002":
        print(f"Training multi-season model {args.model_version} on dataset directory {args.input}...")
        result = run_train(
            dataset_dir=str(inp_path),
            model_version=args.model_version,
            output_model_dir=f"models/risk/{args.model_version}",
        )
        print(json.dumps(result, indent=2))
    else:
        pipeline = TrainingPipeline()
        trained_model, metrics, artifact_path = pipeline.run(
            dataset_path=args.input,
            model_version=args.model_version,
            train_ratio=args.train_ratio,
            cutoff_date=args.cutoff_date,
            include_rf_baseline=args.include_rf,
        )
        print(f"\nTraining completed successfully for version: {args.model_version}")
        print(f"Artifact directory: {artifact_path}")
        print(
            f"Evaluation metrics: Accuracy={metrics.accuracy:.4f}, Precision={metrics.precision:.4f}, "
            f"Recall={metrics.recall:.4f}, F1={metrics.f1_score:.4f}\n"
        )


def handle_evaluate(args):
    inp_path = Path(args.dataset)
    if inp_path.is_dir() or (inp_path.is_file() and "test.parquet" in inp_path.name) or args.model_version == "risk-xgboost-v002":
        dataset_dir = str(inp_path if inp_path.is_dir() else inp_path.parent)
        print(f"Evaluating model {args.model_version} on dataset {dataset_dir}...")
        result = run_evaluate(
            dataset_dir=dataset_dir,
            model_version=args.model_version,
            model_dir=f"models/risk/{args.model_version}",
        )
        print(json.dumps(result, indent=2))
    else:
        model = ModelLoader.load_model(args.model_version)
        df = pd.read_parquet(inp_path) if inp_path.suffix in (".parquet", ".pq") else pd.read_csv(inp_path)
        metrics = RiskModelEvaluator.evaluate_model(model, df, threshold=args.threshold)
        print(f"\nEvaluation of {args.model_version} on {args.dataset}:")
        print(json.dumps(metrics.model_dump(), indent=2))


def handle_all(args):
    print("Executing full end-to-end pipeline...")
    result = run_all(
        firms_dir=args.firms_dir,
        weather_dir=args.weather_dir,
        dataset_dir=args.dataset_dir,
        model_version=args.model_version,
        model_dir=f"models/risk/{args.model_version}",
    )
    print("\nEnd-to-end pipeline completed successfully!")
    print(json.dumps(result, indent=2))


def handle_predict(args):
    model = ModelLoader.load_model(args.model_version)
    predictor = RiskPredictor(model)
    in_path = Path(args.input)
    if in_path.is_file():
        if in_path.suffix in (".parquet", ".pq"):
            df = pd.read_parquet(in_path)
        elif in_path.suffix == ".json":
            df = pd.read_json(in_path)
        else:
            df = pd.read_csv(in_path)
    else:
        try:
            data = json.loads(args.input)
            if isinstance(data, dict):
                data = [data]
            df = pd.DataFrame(data)
        except Exception:
            raise FileNotFoundError(f"Input file not found and input is not valid JSON: {args.input}")

    predictions = predictor.predict_dataframe(df)

    results = [p.model_dump() for p in predictions]
    print(f"\nGenerated predictions for {len(results)} grid cells.")
    if results:
        print(
            f"Sample prediction (cell {results[0]['grid_cell_id']}): "
            f"Probability={results[0]['probability']}, Class={results[0]['risk_class']}"
        )
        print(json.dumps([r for r in results[:5]], indent=2, default=str))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(results).to_csv(out_path, index=False)
        print(f"Saved predictions to: {out_path}")


def handle_info(args):
    registry = ModelRegistry()
    ver = args.model_version or registry.get_default_version()
    model = ModelLoader.load_model(ver)
    print(f"\nModel Information for version: {ver}")
    print(json.dumps(model.metadata.model_dump(), indent=2))


def main():
    args = parse_args()
    if args.command == "ingest":
        handle_ingest(args)
    elif args.command == "build-dataset":
        handle_build_dataset(args)
    elif args.command == "validate-dataset":
        handle_validate_dataset(args)
    elif args.command == "train":
        handle_train(args)
    elif args.command == "evaluate":
        handle_evaluate(args)
    elif args.command == "all":
        handle_all(args)
    elif args.command == "predict":
        handle_predict(args)
    elif args.command == "info":
        handle_info(args)


if __name__ == "__main__":
    main()
