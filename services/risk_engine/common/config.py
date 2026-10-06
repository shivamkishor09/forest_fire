"""Centralized configuration and threshold management for the Risk Engine."""

import os
from pathlib import Path
from typing import Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from .types import RiskClass


class RiskEngineSettings(BaseSettings):
    """Configuration settings for model training, inference, and persistence."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    RISK_MODEL_DIR: str = os.getenv("RISK_MODEL_DIR", "models/risk")
    DEFAULT_RISK_MODEL_VERSION: str = os.getenv("DEFAULT_RISK_MODEL_VERSION", "risk-xgboost-v001")
    RISK_MODEL_RANDOM_SEED: int = int(os.getenv("RISK_MODEL_RANDOM_SEED", "42"))

    # Baseline classification thresholds (centralized & configurable)
    THRESHOLD_LOW: float = 0.25
    THRESHOLD_MODERATE: float = 0.50
    THRESHOLD_HIGH: float = 0.75

    @property
    def model_storage_path(self) -> Path:
        return Path(self.RISK_MODEL_DIR)

    def classify_probability(self, probability: float) -> RiskClass:
        """Map continuous probability into standardized risk classification."""
        if probability < self.THRESHOLD_LOW:
            return RiskClass.LOW
        elif probability < self.THRESHOLD_MODERATE:
            return RiskClass.MODERATE
        elif probability < self.THRESHOLD_HIGH:
            return RiskClass.HIGH
        else:
            return RiskClass.EXTREME


settings = RiskEngineSettings()
