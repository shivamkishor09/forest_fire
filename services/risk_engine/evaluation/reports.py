"""Generates machine-readable metrics JSON, markdown evaluation reports, and model cards."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from ..common.types import ModelMetadata, EvaluationMetrics


class EvaluationReportGenerator:
    """Generates evaluation reports, metrics files, and model cards for model artifacts."""

    @staticmethod
    def save_metrics_json(metrics: EvaluationMetrics, target_file: Path) -> None:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(metrics.model_dump(), f, indent=2)

    @staticmethod
    def generate_evaluation_markdown(
        metadata: ModelMetadata,
        metrics: EvaluationMetrics,
        target_file: Path,
    ) -> None:
        target_file.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# Risk Model Evaluation Report: `{metadata.model_version}`",
            f"",
            f"- **Model Name:** {metadata.model_name}",
            f"- **Algorithm:** {metadata.algorithm}",
            f"- **Created At:** {metadata.created_at}",
            f"- **Dataset Version:** {metadata.dataset_version}",
            f"- **Random Seed:** {metadata.random_seed}",
            f"",
            f"## 1. Dataset & Temporal Split",
            f"",
            f"- **Training Period:** {metadata.training_period.get('start')} to {metadata.training_period.get('end')}",
            f"- **Validation Period:** {metadata.validation_period.get('start')} to {metadata.validation_period.get('end')}",
            f"- **Total Evaluated Samples:** {metrics.total_samples}",
            f"- **Positive Fire Samples:** {metrics.positive_samples} ({metrics.positive_samples / max(metrics.total_samples, 1) * 100:.2f}%)",
            f"- **Negative Non-Fire Samples:** {metrics.negative_samples}",
            f"- **Class Imbalance Strategy:** `{metadata.imbalance_strategy}` (scale_pos_weight = {metadata.positive_weight_ratio})",
            f"",
            f"## 2. Classification Performance Metrics",
            f"",
            f"| Metric | Value |",
            f"|---|---|",
            f"| **Accuracy** | {metrics.accuracy:.4f} |",
            f"| **Precision** | {metrics.precision:.4f} |",
            f"| **Recall** | {metrics.recall:.4f} |",
            f"| **F1-Score** | {metrics.f1_score:.4f} |",
            f"| **ROC-AUC** | {metrics.roc_auc if metrics.roc_auc is not None else 'N/A'} |",
            f"| **PR-AUC** | {metrics.pr_auc if metrics.pr_auc is not None else 'N/A'} |",
            f"",
            f"### Confusion Matrix",
            f"",
            f"| | Predicted Negative (0) | Predicted Positive (1) |",
            f"|---|---|---|",
            f"| **Actual Negative (0)** | True Negatives: **{metrics.true_negatives}** | False Positives: **{metrics.false_positives}** |",
            f"| **Actual Positive (1)** | False Negatives: **{metrics.false_negatives}** | True Positives: **{metrics.true_positives}** |",
            f"",
            f"## 3. Top Feature Importance (Descriptive)",
            f"",
            f"| Rank | Feature Name | Relative Importance |",
            f"|---|---|---|",
        ]

        for i, (feat, imp) in enumerate(metadata.top_feature_importance.items(), 1):
            lines.append(f"| {i} | `{feat}` | {imp:.4f} |")

        lines.extend([
            f"",
            f"> **Note on Feature Importance:** Importance values indicate relative predictive split utility within the trained tree ensemble and do **not** imply direct causality.",
            f"",
            f"## 4. Hyperparameters",
            f"",
            f"```json",
            json.dumps(metadata.hyperparameters, indent=2),
            f"```",
            f"",
            f"## 5. Known Scientific & Practical Limitations",
            f"",
            f"1. **Baseline Tabular Model:** Does not model spatio-temporal graph propagation or deep visual raster contexts (deferred to future spatial research).",
            f"2. **Threshold Sensitivity:** Probability classifications rely on standard engineering thresholds [0.25, 0.50, 0.75]; operational field thresholds must be calibrated with local forest division SOPs.",
            f"3. **Resolution:** Predictions operate at 500m × 500m spatial grid partition. Sub-pixel micro-topographical variations are aggregated.",
            f"4. **Sample Data Disclaimer:** If trained on development sample data, metrics demonstrate software correctness and pipeline reproducibility rather than operational field efficacy.",
        ])

        with open(target_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    @staticmethod
    def generate_model_card(
        metadata: ModelMetadata,
        metrics: EvaluationMetrics,
        target_file: Path,
    ) -> None:
        target_file.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# Model Card: {metadata.model_version}",
            f"",
            f"## Model Details",
            f"- **Model Name:** {metadata.model_name}",
            f"- **Model Version:** {metadata.model_version}",
            f"- **Architecture:** Gradient Boosted Decision Trees ({metadata.algorithm})",
            f"- **Release Date:** {metadata.created_at}",
            f"- **Dataset Lineage:** `{metadata.dataset_version}`",
            f"",
            f"## Intended Use",
            f"- **Primary Use:** 24-hour predictive susceptibility scoring for discrete 500m × 500m forest grid cells.",
            f"- **Users:** Forest department command officers, fire prevention planners, GIS analysts.",
            f"- **Out of Scope:** Active real-time wildfire propagation / flame front spread simulation (handled by the Cellular Automata engine in Phase 7).",
            f"",
            f"## Factors & Precursor Features",
            f"- Topography: Elevation (m), slope (deg), continuous cyclical aspect sin/cos.",
            f"- Meteorology: Temperature (°C), relative humidity (%), wind speed (m/s), orthogonal U/V vectors, 24h & 7d precipitation.",
            f"- Vegetation: Sentinel-2 / Landsat NDVI, NDWI canopy moisture, standardized Indian fuel classification.",
            f"- Fire Weather: Canadian Fire Weather Index (FWI) composite.",
            f"- Historical Fire: 7-day and 30-day fire frequencies, spatial proximity to recent fires, days since last fire.",
            f"",
            f"## Performance & Evaluation",
            f"- **Accuracy:** {metrics.accuracy:.4f}",
            f"- **Recall:** {metrics.recall:.4f}",
            f"- **Precision:** {metrics.precision:.4f}",
            f"- **F1-Score:** {metrics.f1_score:.4f}",
            f"- **ROC-AUC:** {metrics.roc_auc if metrics.roc_auc is not None else 'N/A'}",
            f"",
            f"## Ethical & Safety Considerations",
            f"- Model output represents estimated susceptibility likelihood; it should complement rather than supersede human ground ranger patrols.",
            f"- High-risk alerts must be verified against satellite thermal detections and meteorological warnings.",
        ]

        with open(target_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
