"""Common exceptions for the 24-hour fire risk engine."""

class RiskEngineError(Exception):
    """Base exception for all risk-engine domain errors."""
    pass


class ModelNotFoundError(RiskEngineError):
    """Raised when a requested model version or artifact is missing on disk."""
    pass


class ModelCorruptError(RiskEngineError):
    """Raised when a model artifact cannot be parsed or deserialized."""
    pass


class FeatureValidationError(RiskEngineError):
    """Raised when input feature data violates schema, range, or typing rules."""
    pass


class DataLeakageError(RiskEngineError):
    """Raised when temporal lookahead or target leakage is detected."""
    pass


class InsufficientPositivesError(RiskEngineError):
    """Raised when a training dataset has zero or inadequate positive fire occurrences."""
    pass


class InvalidSplitError(RiskEngineError):
    """Raised when train/test split has temporal overlap or inversion."""
    pass
