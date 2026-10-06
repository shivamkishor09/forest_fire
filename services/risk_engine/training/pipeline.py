"""End-to-end reproducible training pipeline execution."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import pandas as pd

from ..common.logging import get_logger
from ..common.config import settings
from ..common.types import ModelMetadata, EvaluationMetrics
from ..features.schema import RiskFeatureSchema
from .dataset import TrainingDataset
from .split import TemporalSplitter
from .preprocessing import FeaturePreprocessor
from .trainer import XGBoostRiskTrainer, RandomForestRiskTrainer, TrainedXGBoostRiskModel
from ..evaluation.evaluation import RiskModelEvaluator
from ..models.registry import ModelRegistry

logger = get_logger("training_pipeline")


class TrainingPipeline:
    """Executes the complete reproducible model training, evaluation, and serialization workflow."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        random_state: int = 42,
    ):
        self.registry = registry or ModelRegistry()
        self.random_state = random_state

    def run(
        self,
        dataset_path: Union[str, Path],
        model_version: str = "risk-xgboost-v001",
        train_ratio: float = 0.75,
        cutoff_date: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        include_rf_baseline: bool = False,
    ) -> Tuple[TrainedXGBoostRiskModel, EvaluationMetrics, Path]:
        """
        Execute training workflow:
        1. Load & validate dataset
        2. Perform chronological temporal split
        3. Fit preprocessor
        4. Train XGBoost model with class imbalance weighting
        5. Evaluate metrics on validation split
        6. Register model version artifact package
        """
        logger.info(f"Starting risk model training for version: {model_version}")
        logger.info(f"Loading dataset from: {dataset_path}")

        # 1. Load dataset & audit class distribution
        dataset = TrainingDataset.from_file(dataset_path)
        dist = dataset.class_distribution
        logger.info(
            f"Dataset loaded: {dist['total_samples']} samples "
            f"(Positives: {dist['positive_samples']}, Negatives: {dist['negative_samples']}, "
            f"Positive Ratio: {dist['positive_percentage']}%, Imbalance Ratio: {dist['imbalance_ratio']}:1)"
        )

        # 2. Temporal split
        splitter = TemporalSplitter(train_ratio=train_ratio, cutoff_date=cutoff_date)
        train_df, val_df, split_meta = splitter.split(dataset.df)
        logger.info(
            f"Temporal split ({split_meta['strategy']}): "
            f"Train={len(train_df)} samples ({split_meta['train_start_date']} to {split_meta['train_end_date']}), "
            f"Val={len(val_df)} samples ({split_meta['val_start_date']} to {split_meta['val_end_date']})"
        )

        # 3. Preprocessing
        preprocessor = FeaturePreprocessor()
        schema = RiskFeatureSchema()

        # 4. Train XGBoost
        hp = hyperparameters or {}
        trainer = XGBoostRiskTrainer(
            n_estimators=hp.get("n_estimators", 100),
            max_depth=hp.get("max_depth", 5),
            learning_rate=hp.get("learning_rate", 0.05),
            subsample=hp.get("subsample", 0.8),
            colsample_bytree=hp.get("colsample_bytree", 0.8),
            reg_alpha=hp.get("reg_alpha", 0.1),
            reg_lambda=hp.get("reg_lambda", 1.0),
            random_state=self.random_state,
        )

        logger.info("Fitting XGBoost classifier...")
        trained_model = trainer.train(
            train_df=train_df,
            val_df=val_df,
            preprocessor=preprocessor,
            model_version=model_version,
            dataset_version=dataset.dataset_id,
        )

        # 5. Evaluate on validation set
        logger.info("Evaluating model on validation split...")
        metrics = RiskModelEvaluator.evaluate_model(trained_model, val_df)
        logger.info(
            f"Validation Results: Accuracy={metrics.accuracy:.4f}, Precision={metrics.precision:.4f}, "
            f"Recall={metrics.recall:.4f}, F1={metrics.f1_score:.4f}, "
            f"ROC-AUC={metrics.roc_auc if metrics.roc_auc is not None else 'N/A'}"
        )

        # 6. Register artifact package
        artifact_path = self.registry.register_model_version(
            version=model_version,
            model=trained_model.raw_model,
            metadata=trained_model.metadata,
            preprocessor=preprocessor,
            schema=schema,
            metrics=metrics,
        )
        logger.info(f"Model artifacts successfully registered at: {artifact_path}")

        # Optional Random Forest comparison
        if include_rf_baseline:
            logger.info("Training optional Random Forest comparison baseline...")
            rf_trainer = RandomForestRiskTrainer(random_state=self.random_state)
            rf_model = rf_trainer.train(train_df, preprocessor=preprocessor, model_version=f"{model_version}-rf")
            rf_metrics = RiskModelEvaluator.evaluate_model(rf_model, val_df)
            logger.info(
                f"Random Forest Comparison: Accuracy={rf_metrics.accuracy:.4f}, Precision={rf_metrics.precision:.4f}, "
                f"Recall={rf_metrics.recall:.4f}, F1={rf_metrics.f1_score:.4f}"
            )
            self.registry.register_model_version(
                version=f"{model_version}-rf",
                model=rf_model.raw_model,
                metadata=rf_model.metadata,
                preprocessor=preprocessor,
                schema=schema,
                metrics=rf_metrics,
            )

        return trained_model, metrics, artifact_path
