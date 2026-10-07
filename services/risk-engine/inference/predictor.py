"""Inference interface for 24-hour fire risk prediction on 500m spatial cells."""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from ..models.base import BaseRiskModel
from ..common.config import settings
from ..common.types import RiskClass, RiskPrediction, RiskInferenceInput
from ..features.validation import RiskFeatureValidator
from .validation import InferenceValidator


class RiskPredictor:
    """
    Executes single-cell and vectorized batch 24-hour fire risk predictions.
    Computes susceptibility probability, derives centralized risk classification,
    and returns canonical RiskPrediction contracts.
    """

    def __init__(self, model: BaseRiskModel):
        self.model = model

    @staticmethod
    def classify_probability(prob: float, thresholds: Optional[dict] = None) -> RiskClass:
        """Derive centralized risk classification using model thresholds or platform settings."""
        if thresholds and "LOW_MAX" in thresholds and "MODERATE_MAX" in thresholds and "HIGH_MAX" in thresholds:
            if prob < thresholds["LOW_MAX"]:
                return RiskClass.LOW
            elif prob < thresholds["MODERATE_MAX"]:
                return RiskClass.MODERATE
            elif prob < thresholds["HIGH_MAX"]:
                return RiskClass.HIGH
            else:
                return RiskClass.EXTREME
        return settings.classify_probability(prob)

    def classify_model_probability(self, prob: float) -> RiskClass:
        """Classify probability using this predictor's model thresholds."""
        return self.classify_probability(prob, getattr(self.model, "thresholds", None))


    def predict_risk(self, inference_input: RiskInferenceInput) -> RiskPrediction:
        """
        Validate inputs and invoke model to produce canonical RiskPrediction for one cell.
        """
        # Validate features
        InferenceValidator.validate_single_input(inference_input.features)

        pred_time = inference_input.prediction_time or datetime.now(timezone.utc)
        if pred_time.tzinfo is None:
            pred_time = pred_time.replace(tzinfo=timezone.utc)

        forecast_end = pred_time + timedelta(hours=24)

        probability = float(self.model.predict_susceptibility(inference_input.features))
        risk_class = self.classify_model_probability(probability)

        top_importances = getattr(self.model, "feature_importances", None)
        if top_importances:
            top_importances = dict(list(top_importances.items())[:5])

        return RiskPrediction(
            grid_cell_id=inference_input.grid_cell_id,
            probability=round(probability, 4),
            risk_class=risk_class,
            model_version=self.model.model_version,
            prediction_timestamp=pred_time.isoformat(),
            forecast_start=pred_time.isoformat(),
            forecast_end=forecast_end.isoformat(),
            region_id=inference_input.region_id,
            valid_for_date=pred_time.strftime("%Y-%m-%d"),
            feature_importances=top_importances,
        )

    def predict_risk_batch(
        self,
        inputs: List[RiskInferenceInput],
    ) -> List[RiskPrediction]:
        """
        Execute prediction across a batch of RiskInferenceInput items.
        """
        if not inputs:
            return []

        # Validate inputs
        feature_dicts = [item.features for item in inputs]
        InferenceValidator.validate_batch_inputs(feature_dicts)

        # If model supports vectorized batch prediction, convert to DataFrame
        if hasattr(self.model, "predict_batch_probabilities"):
            df = pd.DataFrame(feature_dicts)
            probas = getattr(self.model, "predict_batch_probabilities")(df)
        else:
            probas = [float(self.model.predict_susceptibility(item.features)) for item in inputs]

        predictions: List[RiskPrediction] = []
        now = datetime.now(timezone.utc)

        top_importances = getattr(self.model, "feature_importances", None)
        if top_importances:
            top_importances = dict(list(top_importances.items())[:5])

        for item, proba in zip(inputs, probas):
            p_time = item.prediction_time or now
            if p_time.tzinfo is None:
                p_time = p_time.replace(tzinfo=timezone.utc)
            f_end = p_time + timedelta(hours=24)
            p_val = round(float(proba), 4)

            predictions.append(
                RiskPrediction(
                    grid_cell_id=item.grid_cell_id,
                    probability=p_val,
                    risk_class=self.classify_model_probability(p_val),
                    model_version=self.model.model_version,
                    prediction_timestamp=p_time.isoformat(),
                    forecast_start=p_time.isoformat(),
                    forecast_end=f_end.isoformat(),
                    region_id=item.region_id,
                    valid_for_date=p_time.strftime("%Y-%m-%d"),
                    feature_importances=top_importances,
                )
            )

        return predictions

    def predict_dataframe(
        self,
        df: pd.DataFrame,
        prediction_time: Optional[datetime] = None,
        region_id: Optional[str] = None,
    ) -> List[RiskPrediction]:
        """
        High-performance vectorized inference across an entire spatial grid DataFrame.
        """
        if df.empty:
            return []

        if "grid_cell_id" not in df.columns:
            raise ValueError("Input DataFrame must contain 'grid_cell_id' column.")

        now = prediction_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        f_end = now + timedelta(hours=24)

        if hasattr(self.model, "predict_batch_probabilities"):
            probas = getattr(self.model, "predict_batch_probabilities")(df)
        else:
            probas = np.array([float(self.model.predict_susceptibility(row)) for row in df.to_dict(orient="records")])

        cell_ids = df["grid_cell_id"].tolist()
        r_ids = df["region_id"].tolist() if "region_id" in df.columns else [region_id] * len(cell_ids)

        top_importances = getattr(self.model, "feature_importances", None)
        if top_importances:
            top_importances = dict(list(top_importances.items())[:5])

        predictions: List[RiskPrediction] = []
        for cid, rid, prob in zip(cell_ids, r_ids, probas):
            p_val = round(float(prob), 4)
            predictions.append(
                RiskPrediction(
                    grid_cell_id=cid,
                    probability=p_val,
                    risk_class=self.classify_model_probability(p_val),
                    model_version=self.model.model_version,
                    prediction_timestamp=now.isoformat(),
                    forecast_start=now.isoformat(),
                    forecast_end=f_end.isoformat(),
                    region_id=rid,
                    valid_for_date=now.strftime("%Y-%m-%d"),
                    feature_importances=top_importances,
                )
            )

        return predictions
