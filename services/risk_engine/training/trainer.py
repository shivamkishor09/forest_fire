"""XGBoost and Random Forest risk model trainers with class imbalance handling."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier

from ..models.base import BaseRiskModel
from ..common.types import ModelMetadata
from ..common.config import settings
from .preprocessing import FeaturePreprocessor


class TrainedXGBoostRiskModel(BaseRiskModel):
    """Wrapper around trained XGBoost classifier conforming to BaseRiskModel."""

    def __init__(
        self,
        model: xgb.XGBClassifier,
        preprocessor: FeaturePreprocessor,
        metadata: ModelMetadata,
        calibrator: Optional[Any] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ):
        super().__init__(metadata)
        self.raw_model = model
        self.preprocessor = preprocessor
        self.calibrator = calibrator
        self.thresholds = thresholds or {}

    def predict_susceptibility(self, features: Dict[str, Any]) -> float:
        """Compute single-cell fire risk probability in [0.0, 1.0]."""
        x = self.preprocessor.transform_dict(features)
        if self.calibrator is not None:
            proba = float(self.calibrator.predict_proba(x)[0, 1])
        else:
            proba = float(self.raw_model.predict_proba(x)[0, 1])
        return round(float(np.clip(proba, 0.0, 1.0)), 4)

    def predict_batch_probabilities(self, df: pd.DataFrame) -> np.ndarray:
        """Compute vectorized batch fire risk probabilities for a DataFrame."""
        x = self.preprocessor.transform_dataframe(df)
        if self.calibrator is not None:
            probas = self.calibrator.predict_proba(x)[:, 1]
        else:
            probas = self.raw_model.predict_proba(x)[:, 1]
        return np.clip(probas, 0.0, 1.0)

    @property
    def feature_importances(self) -> Dict[str, float]:
        """Return descriptive feature importances sorted descending by weight/gain."""
        names = self.preprocessor.final_feature_names
        importances = self.raw_model.feature_importances_
        sorted_pairs = sorted(zip(names, importances), key=lambda x: x[1], reverse=True)
        return {name: round(float(imp), 4) for name, imp in sorted_pairs}


class XGBoostRiskTrainer:
    """Trainer for XGBoost fire risk prediction models."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 5,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        reg_alpha: float = 0.1,
        reg_lambda: float = 1.0,
        random_state: int = 42,
    ):
        self.params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "subsample": subsample,
            "colsample_bytree": colsample_bytree,
            "reg_alpha": reg_alpha,
            "reg_lambda": reg_lambda,
            "random_state": random_state,
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "tree_method": "hist",
        }

    def train(
        self,
        train_df: pd.DataFrame,
        val_df: Optional[pd.DataFrame] = None,
        preprocessor: Optional[FeaturePreprocessor] = None,
        target_col: str = "target_fire_next_24h",
        model_version: str = "risk-xgboost-v001",
        dataset_version: str = "dataset_v1",
        imbalance_strategy: str = "scale_pos_weight",
    ) -> TrainedXGBoostRiskModel:
        """
        Train XGBoost binary classifier with automatic scale_pos_weight calculation.
        """
        if preprocessor is None:
            preprocessor = FeaturePreprocessor()

        x_train = preprocessor.transform_dataframe(train_df)
        y_train = train_df[target_col].astype(int).values

        # Compute scale_pos_weight = negative / positive
        pos_count = int((y_train == 1).sum())
        neg_count = int((y_train == 0).sum())
        scale_pos_weight = float(neg_count / max(pos_count, 1))

        current_params = dict(self.params)
        if imbalance_strategy == "scale_pos_weight":
            current_params["scale_pos_weight"] = scale_pos_weight

        xgb_model = xgb.XGBClassifier(**current_params)

        if val_df is not None and not val_df.empty:
            x_val = preprocessor.transform_dataframe(val_df)
            y_val = val_df[target_col].astype(int).values
            xgb_model.fit(
                x_train,
                y_train,
                eval_set=[(x_train, y_train), (x_val, y_val)],
                verbose=False,
            )
        else:
            xgb_model.fit(x_train, y_train, verbose=False)

        dates = train_df.get("reference_date", pd.Series(["unknown"]))
        metadata = ModelMetadata(
            model_name="risk-xgboost",
            model_version=model_version,
            algorithm="XGBoost",
            created_at=pd.Timestamp.now(tz="UTC").isoformat(),
            training_period={"start": str(dates.min()), "end": str(dates.max())},
            validation_period={"start": str(val_df["reference_date"].min()) if val_df is not None else "N/A",
                               "end": str(val_df["reference_date"].max()) if val_df is not None else "N/A"},
            dataset_version=dataset_version,
            hyperparameters=current_params,
            feature_names=preprocessor.final_feature_names,
            random_seed=self.params["random_state"],
            imbalance_strategy=imbalance_strategy,
            positive_weight_ratio=round(scale_pos_weight, 2),
            metrics={},
            confusion_matrix={},
            top_feature_importance={},
        )

        trained_model = TrainedXGBoostRiskModel(
            model=xgb_model,
            preprocessor=preprocessor,
            metadata=metadata,
        )
        metadata.top_feature_importance = dict(list(trained_model.feature_importances.items())[:10])

        return trained_model


class TrainedRandomForestRiskModel(BaseRiskModel):
    """Wrapper around trained Random Forest classifier."""

    def __init__(
        self,
        model: RandomForestClassifier,
        preprocessor: FeaturePreprocessor,
        metadata: ModelMetadata,
    ):
        super().__init__(metadata)
        self.raw_model = model
        self.preprocessor = preprocessor

    def predict_susceptibility(self, features: Dict[str, Any]) -> float:
        x = self.preprocessor.transform_dict(features)
        proba = float(self.raw_model.predict_proba(x)[0, 1])
        return round(float(np.clip(proba, 0.0, 1.0)), 4)

    def predict_batch_probabilities(self, df: pd.DataFrame) -> np.ndarray:
        x = self.preprocessor.transform_dataframe(df)
        probas = self.raw_model.predict_proba(x)[:, 1]
        return np.clip(probas, 0.0, 1.0)


class RandomForestRiskTrainer:
    """Baseline comparison Random Forest trainer."""

    def __init__(self, n_estimators: int = 100, max_depth: int = 8, random_state: int = 42):
        self.params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "class_weight": "balanced_subsample",
            "random_state": random_state,
        }

    def train(
        self,
        train_df: pd.DataFrame,
        preprocessor: Optional[FeaturePreprocessor] = None,
        target_col: str = "target_fire_next_24h",
        model_version: str = "risk-rf-v001",
    ) -> TrainedRandomForestRiskModel:
        if preprocessor is None:
            preprocessor = FeaturePreprocessor()

        x_train = preprocessor.transform_dataframe(train_df)
        y_train = train_df[target_col].astype(int).values

        rf = RandomForestClassifier(**self.params)
        rf.fit(x_train, y_train)

        metadata = ModelMetadata(
            model_name="risk-random-forest",
            model_version=model_version,
            algorithm="RandomForest",
            created_at=pd.Timestamp.now(tz="UTC").isoformat(),
            training_period={"start": str(train_df["reference_date"].min()), "end": str(train_df["reference_date"].max())},
            validation_period={"start": "N/A", "end": "N/A"},
            dataset_version="dataset_v1",
            hyperparameters=self.params,
            feature_names=preprocessor.final_feature_names,
            random_seed=self.params["random_state"],
            imbalance_strategy="class_weight_balanced_subsample",
            positive_weight_ratio=1.0,
            metrics={},
            confusion_matrix={},
            top_feature_importance={},
        )

        return TrainedRandomForestRiskModel(model=rf, preprocessor=preprocessor, metadata=metadata)
