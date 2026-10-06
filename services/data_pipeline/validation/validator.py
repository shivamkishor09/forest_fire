"""Validation module for raw data quality and bounds."""

from typing import Any, Dict, List
from ..adapters.base import BoundingBox


class RawDataValidator:
    """Enforces geographic bounds, non-null thresholds, and range constraints."""

    @staticmethod
    def validate_bounding_box(bbox: BoundingBox) -> bool:
        """Ensure bounding box has valid coordinates and non-zero positive extent."""
        if not (-90.0 <= bbox.min_lat <= 90.0 and -90.0 <= bbox.max_lat <= 90.0):
            return False
        if not (-180.0 <= bbox.min_lon <= 180.0 and -180.0 <= bbox.max_lon <= 180.0):
            return False
        return bbox.min_lat < bbox.max_lat and bbox.min_lon < bbox.max_lon

    @staticmethod
    def validate_weather_payload(data: Dict[str, Any]) -> bool:
        """Validate weather readings are within physically plausible atmospheric bounds."""
        metrics = data.get("metrics", {})
        temp = metrics.get("temperature_c")
        humidity = metrics.get("relative_humidity_pct")
        wind = metrics.get("wind_speed_ms")

        if temp is not None and not (-40.0 <= temp <= 65.0):
            return False
        if humidity is not None and not (0.0 <= humidity <= 100.0):
            return False
        if wind is not None and wind < 0.0:
            return False
        return True
