"""Backward-compatible alias for RiskFeatureValidator."""

from .validation import RiskFeatureValidator, REQUIRED_CORE_FEATURES as REQUIRED_RISK_FEATURES

__all__ = ["RiskFeatureValidator", "REQUIRED_RISK_FEATURES"]
