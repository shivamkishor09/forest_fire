"""Command-line interface (CLI) for training, evaluating, and running risk inference."""

import argparse
import json
import logging
import sys
from pathlib import Path
import pandas as pd

if __package__ is None or __package__ == "":
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
else:
    from .common.logging import get_logger
    from .common.config import settings
    from .training.pipeline import TrainingPipeline
    from .training.dataset import TrainingDataset
    from .evaluation.evaluation import RiskModelEvaluator
    from .evaluation.reports import EvaluationReportGenerator
    from .inference.loader import ModelLoader
    from .inference.predictor import RiskPredictor, RiskInferenceInput
    from .models.registry import ModelRegistry

logger = get_logger("CLI")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Predictive Forest Fire Risk Platform - 24-Hour Risk Engine (Phase 5)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Train command
    train_parser = subparsers.add_parser("train", help="Train 24-hour XGBoost fire risk model")
    train_parser.add_argument("--input", type=str, default="data/processed/sample_run/features.parquet")
    train_parser.add_argument("--model-version", type=str, default="risk-xgboost-v001")
    train_parser.add_argument("--train-ratio", type=float, default=0.75)
    train_parser.add_argument("--cutoff-date", type=str, default=None)
    train_parser.add_argument("--include-rf", action="store_true", help="Also train Random Forest comparison baseline")

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate trained model on a dataset")
    eval_parser.add_argument("--model-version", type=str, default="risk-xgboost-v001")
    eval_parser.add_argument("--dataset", type=str, default="data/processed/sample_run/features.parquet")
    eval_parser.add_argument("--threshold", type=float, default=0.5)

    # Predict command
    pred_parser = subparsers.add_parser("predict", help="Run 24-hour fire risk inference")
    pred_parser.add_argument("--model-version", type=str, default=None)
    pred_parser.add_argument("--input", type=str, required=True)
    pred_parser.add_argument("--output", type=str, default=None)

    # Info command
    info_parser = subparsers.add_parser("info", help="Display metadata of registered model version")
    info_parser.add_argument("--model-version", type=str, default=None)

    return parser.parse_args()


def handle_train(args):
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
    print(f"Evaluation metrics: Accuracy={metrics.accuracy:.4f}, Precision={metrics.precision:.4f}, Recall={metrics.recall:.4f}, F1={metrics.f1_score:.4f}\n")


def handle_evaluate(args):
    model = ModelLoader.load_model(args.model_version)
    path = Path(args.dataset)
    df = pd.read_parquet(path) if path.suffix in (".parquet", ".pq") else pd.read_csv(path)
    metrics = RiskModelEvaluator.evaluate_model(model, df, threshold=args.threshold)
    print(f"\nEvaluation of {args.model_version} on {args.dataset}:")
    print(json.dumps(metrics.model_dump(), indent=2))


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
        print(f"Sample prediction (cell {results[0]['grid_cell_id']}): Probability={results[0]['probability']}, Class={results[0]['risk_class']}")
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
    if args.command == "train":
        handle_train(args)
    elif args.command == "evaluate":
        handle_evaluate(args)
    elif args.command == "predict":
        handle_predict(args)
    elif args.command == "info":
        handle_info(args)


if __name__ == "__main__":
    main()
