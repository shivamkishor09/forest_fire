"""Common types and schemas for the data ingestion and preprocessing pipeline."""

from .types import (
    CanonicalFireObservation,
    CanonicalWeatherObservation,
    CanonicalVegetationObservation,
    CanonicalTerrainObservation,
    GridCellDefinition,
    CanonicalFeatureRecord,
    DataManifest,
    QualityReport,
    DataLeakageError,
    BoundingBox,
)

__all__ = [
    "CanonicalFireObservation",
    "CanonicalWeatherObservation",
    "CanonicalVegetationObservation",
    "CanonicalTerrainObservation",
    "GridCellDefinition",
    "CanonicalFeatureRecord",
    "DataManifest",
    "QualityReport",
    "DataLeakageError",
    "BoundingBox",
]
