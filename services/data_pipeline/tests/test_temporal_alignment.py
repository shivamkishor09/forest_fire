"""Unit tests for temporal alignment and strict anti-leakage guards."""

from datetime import datetime, timezone, timedelta
import pytest
from services.data_pipeline.common.types import (
    CanonicalFireObservation,
    CanonicalWeatherObservation,
    DataLeakageError,
)
from services.data_pipeline.preprocessing.temporal_alignment import TemporalAligner


def test_anti_leakage_guard_strict():
    ref_time = datetime(2026, 5, 15, 0, 0, 0, tzinfo=timezone.utc)
    aligner = TemporalAligner(reference_time=ref_time, strict_anti_leakage=True)

    past_fire = CanonicalFireObservation(
        source="MODIS",
        detection_time=datetime(2026, 5, 14, 12, 0, 0, tzinfo=timezone.utc),
        latitude=30.2,
        longitude=78.7,
        confidence_pct=80.0,
    )
    future_fire = CanonicalFireObservation(
        source="MODIS",
        detection_time=datetime(2026, 5, 15, 6, 0, 0, tzinfo=timezone.utc),
        latitude=30.2,
        longitude=78.7,
        confidence_pct=90.0,
    )

    # In strict mode, feeding future data MUST raise DataLeakageError
    with pytest.raises(DataLeakageError) as exc_info:
        aligner.filter_and_guard_observations([past_fire, future_fire], "detection_time")
    assert "Data leakage detected" in str(exc_info.value)


def test_anti_leakage_guard_non_strict_filter():
    ref_time = datetime(2026, 5, 15, 0, 0, 0, tzinfo=timezone.utc)
    aligner = TemporalAligner(reference_time=ref_time, strict_anti_leakage=False)

    past_fire = CanonicalFireObservation(
        source="MODIS",
        detection_time=datetime(2026, 5, 14, 12, 0, 0, tzinfo=timezone.utc),
        latitude=30.2,
        longitude=78.7,
        confidence_pct=80.0,
    )
    future_fire = CanonicalFireObservation(
        source="MODIS",
        detection_time=datetime(2026, 5, 15, 6, 0, 0, tzinfo=timezone.utc),
        latitude=30.2,
        longitude=78.7,
        confidence_pct=90.0,
    )

    # Non-strict mode should silently discard future fire and preserve past fire
    valid = aligner.filter_and_guard_observations([past_fire, future_fire], "detection_time")
    assert len(valid) == 1
    assert valid[0].detection_time == past_fire.detection_time


def test_fire_history_metrics():
    ref_time = datetime(2026, 5, 15, 0, 0, 0, tzinfo=timezone.utc)
    aligner = TemporalAligner(reference_time=ref_time, strict_anti_leakage=False)

    fire_2d_ago = CanonicalFireObservation(
        source="MODIS",
        detection_time=ref_time - timedelta(days=2),
        latitude=30.2,
        longitude=78.7,
        confidence_pct=80.0,
    )
    fire_10d_ago = CanonicalFireObservation(
        source="MODIS",
        detection_time=ref_time - timedelta(days=10),
        latitude=30.2,
        longitude=78.7,
        confidence_pct=80.0,
    )

    metrics = aligner.compute_fire_history_metrics([fire_2d_ago, fire_10d_ago])
    assert metrics["fire_count_7d"] == 1
    assert metrics["fire_count_30d"] == 2
    assert metrics["days_since_last_fire"] == 2.0


def test_cumulative_precipitation():
    ref_time = datetime(2026, 5, 15, 0, 0, 0, tzinfo=timezone.utc)
    aligner = TemporalAligner(reference_time=ref_time, strict_anti_leakage=False)

    w1 = CanonicalWeatherObservation(
        source="IMD",
        timestamp=ref_time - timedelta(days=1),
        latitude=30.2,
        longitude=78.7,
        precipitation_mm=5.0,
    )
    w2 = CanonicalWeatherObservation(
        source="IMD",
        timestamp=ref_time - timedelta(days=4),
        latitude=30.2,
        longitude=78.7,
        precipitation_mm=12.5,
    )
    w_old = CanonicalWeatherObservation(
        source="IMD",
        timestamp=ref_time - timedelta(days=15),
        latitude=30.2,
        longitude=78.7,
        precipitation_mm=20.0,
    )

    p7 = aligner.compute_cumulative_precipitation([w1, w2, w_old], lookback_days=7)
    assert p7 == 17.5
