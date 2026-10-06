"""Unit tests for raw data validator."""

from services.data_pipeline.adapters.base import BoundingBox
from services.data_pipeline.validation.validator import RawDataValidator


def test_bounding_box_validation():
    """Verify BoundingBox validator detects valid and invalid coordinate extents."""
    valid_bbox = BoundingBox(min_lon=76.0, min_lat=11.0, max_lon=77.0, max_lat=12.0)
    assert RawDataValidator.validate_bounding_box(valid_bbox) is True

    # Inverted min/max
    invalid_bbox = BoundingBox(min_lon=77.0, min_lat=12.0, max_lon=76.0, max_lat=11.0)
    assert RawDataValidator.validate_bounding_box(invalid_bbox) is False

    # Out of latitude range
    out_of_bounds = BoundingBox(min_lon=76.0, min_lat=-95.0, max_lon=77.0, max_lat=12.0)
    assert RawDataValidator.validate_bounding_box(out_of_bounds) is False


def test_weather_payload_validation():
    """Verify weather validator detects implausible atmospheric readings."""
    valid_payload = {
        "metrics": {
            "temperature_c": 35.0,
            "relative_humidity_pct": 20.0,
            "wind_speed_ms": 5.0,
        }
    }
    assert RawDataValidator.validate_weather_payload(valid_payload) is True

    invalid_temp = {
        "metrics": {
            "temperature_c": 95.0,  # Unphysical surface temperature
            "relative_humidity_pct": 20.0,
        }
    }
    assert RawDataValidator.validate_weather_payload(invalid_temp) is False
