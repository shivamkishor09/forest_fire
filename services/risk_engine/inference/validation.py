"""Pre-inference input validation."""

from typing import Any, Dict, List, Union
from ..common.exceptions import FeatureValidationError
from ..features.validation import RiskFeatureValidator


class InferenceValidator:
    """Validates single-cell and batch inference inputs."""

    @staticmethod
    def validate_single_input(features: Dict[str, Any]) -> None:
        RiskFeatureValidator.validate_or_raise(features, require_all_canonical=False)

    @staticmethod
    def validate_batch_inputs(inputs: List[Dict[str, Any]]) -> None:
        if not inputs:
            raise FeatureValidationError("Inference batch cannot be empty.")
        for idx, item in enumerate(inputs):
            try:
                RiskFeatureValidator.validate_or_raise(item, require_all_canonical=False)
            except FeatureValidationError as e:
                raise FeatureValidationError(f"Batch item at index {idx} failed validation: {e}")
