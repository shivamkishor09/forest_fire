"""Unit tests for evaluation metrics and report generation."""

from pathlib import Path
import pytest
import numpy as np

from services.risk_engine.evaluation.metrics import compute_classification_metrics
from services.risk_engine.evaluation.reports import EvaluationReportGenerator
from services.risk_engine.common.types import ModelMetadata


def test_metrics_calculation_standard():
    y_true = np.array([0, 0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.4, 0.8, 0.9])

    metrics = compute_classification_metrics(y_true, y_prob, threshold=0.5)

    assert metrics.total_samples == 5
    assert metrics.positive_samples == 2
    assert metrics.negative_samples == 3
    assert metrics.accuracy == 1.0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1_score == 1.0
    assert metrics.roc_auc == 1.0
    assert metrics.true_positives == 2
    assert metrics.true_negatives == 3


def test_metrics_calculation_with_errors():
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.8, 0.2, 0.3, 0.9])  # 1 false positive, 1 false negative

    metrics = compute_classification_metrics(y_true, y_prob, threshold=0.5)

    assert metrics.accuracy == 0.5
    assert metrics.true_positives == 1
    assert metrics.false_positives == 1
    assert metrics.true_negatives == 1
    assert metrics.false_negatives == 1


def test_report_generation(tmp_path: Path):
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.8, 0.9])
    metrics = compute_classification_metrics(y_true, y_prob)

    metadata = ModelMetadata(
        model_name="test-model",
        model_version="v001",
        algorithm="XGBoost",
        training_period={"start": "2026-05-10", "end": "2026-05-14"},
        validation_period={"start": "2026-05-15", "end": "2026-05-15"},
        dataset_version="ds-v1",
        hyperparameters={"max_depth": 3},
        feature_names=["fwi", "temp"],
        random_seed=42,
        imbalance_strategy="scale_pos_weight",
        positive_weight_ratio=1.0,
        metrics={},
        confusion_matrix={},
        top_feature_importance={"fwi": 0.6, "temp": 0.4},
    )

    metrics_json = tmp_path / "metrics.json"
    report_md = tmp_path / "evaluation_report.md"
    card_md = tmp_path / "MODEL_CARD.md"

    EvaluationReportGenerator.save_metrics_json(metrics, metrics_json)
    EvaluationReportGenerator.generate_evaluation_markdown(metadata, metrics, report_md)
    EvaluationReportGenerator.generate_model_card(metadata, metrics, card_md)

    assert metrics_json.exists()
    assert report_md.exists()
    assert card_md.exists()

    content = report_md.read_text(encoding="utf-8")
    assert "Risk Model Evaluation Report: `v001`" in content
    assert "Accuracy" in content
    assert "Confusion Matrix" in content
