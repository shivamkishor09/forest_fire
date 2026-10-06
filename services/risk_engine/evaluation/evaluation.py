"""Model evaluation runner comparing predictions against ground truth labels."""

from typing import Any, Dict, Optional, Tuple
import pandas as pd
import numpy as np

from ..models.base import BaseRiskModel
from .metrics import compute_classification_metrics, EvaluationMetrics


class RiskModelEvaluator:
    """Evaluates risk models on validation or hold-out test sets."""

    @staticmethod
    def evaluate_model(
        model: BaseRiskModel,
        test_df: pd.DataFrame,
        target_col: str = "target_fire_next_24h",
        threshold: float = 0.5,
    ) -> EvaluationMetrics:
        """
        Evaluate model on test DataFrame and return EvaluationMetrics.
        """
        y_true = test_df[target_col].astype(int).values

        # Vectorized batch prediction if supported, else row-by-row
        if hasattr(model, "predict_batch_probabilities"):
            y_prob = getattr(model, "predict_batch_probabilities")(test_df)
        else:
            y_prob = np.array([model.predict_susceptibility(row) for row in test_df.to_dict(orient="records")])

        metrics = compute_classification_metrics(y_true, y_prob, threshold=threshold)
        return metrics
