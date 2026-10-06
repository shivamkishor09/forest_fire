"""Base risk model abstract interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..common.types import ModelMetadata


class BaseRiskModel(ABC):
    """Abstract interface that all 24-hour fire risk models must implement."""

    def __init__(self, metadata: ModelMetadata):
        self.metadata = metadata

    @property
    def model_name(self) -> str:
        return self.metadata.model_name

    @property
    def model_version(self) -> str:
        return self.metadata.model_version

    @abstractmethod
    def predict_susceptibility(self, features: Dict[str, Any]) -> float:
        """
        Compute fire susceptibility probability in [0.0, 1.0] for a 500m cell.
        """
        pass
