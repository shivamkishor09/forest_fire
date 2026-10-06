"""Custom domain exceptions for the Forest Fire Spread Simulation Engine."""


class SpreadEngineError(Exception):
    """Base exception for all spread simulation engine failures."""
    pass


class InvalidSimulationInputError(SpreadEngineError):
    """Raised when simulation parameters violate boundary or domain constraints."""
    pass


class GridValidationError(SpreadEngineError):
    """Raised when input grid arrays or dimensional parameters are malformed."""
    pass


class IgnitionOutsideGridError(InvalidSimulationInputError):
    """Raised when specified ignition coordinates lie outside the active grid bounding box."""
    pass


class UnsupportedDurationError(InvalidSimulationInputError):
    """Raised when requested simulation duration is non-positive or exceeds maximum allowed (12h)."""
    pass


class InvalidEnvironmentalDataError(SpreadEngineError):
    """Raised when meteorological or topographical input values are out of physical bounds."""
    pass


class SimulationNumericalError(SpreadEngineError):
    """Raised when an arithmetic overflow, underflow, or NaN condition arises during propagation."""
    pass


class BoundaryExtractionError(SpreadEngineError):
    """Raised when geometric boundary extraction or polygon unioning fails."""
    pass
