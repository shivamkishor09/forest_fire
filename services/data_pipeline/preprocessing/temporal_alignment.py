"""Temporal alignment, daily compositing, lookback windows, and anti-leakage guards."""

from datetime import datetime, timezone, timedelta, date
from typing import Any, Dict, List, Optional, Tuple, TypeVar
import logging

from ..common.types import (
    CanonicalFireObservation,
    CanonicalWeatherObservation,
    CanonicalVegetationObservation,
    DataLeakageError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TemporalAligner:
    """Enforces temporal consistency, rolling windows, and strict anti-leakage guards."""

    def __init__(self, reference_time: datetime, strict_anti_leakage: bool = True):
        """
        Args:
            reference_time: The cutoff prediction point T_ref (UTC). Observations with T > T_ref are future data.
            strict_anti_leakage: If True, raise DataLeakageError if future data is encountered.
                                 If False, filter future data with a warning.
        """
        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)
        self.reference_time = reference_time
        self.strict_anti_leakage = strict_anti_leakage

    def filter_and_guard_observations(
        self,
        observations: List[Any],
        timestamp_attr: str = "detection_time"
    ) -> List[Any]:
        """
        Filter observations against reference_time.
        Guarantees that no record with T > T_ref enters downstream preprocessing.
        """
        valid_records = []
        future_records = []

        for obs in observations:
            t = getattr(obs, timestamp_attr)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)

            if t > self.reference_time:
                future_records.append(obs)
            else:
                valid_records.append(obs)

        if future_records:
            msg = (
                f"Data leakage detected! Found {len(future_records)} observations with timestamp "
                f"> reference cutoff {self.reference_time.isoformat()}."
            )
            if self.strict_anti_leakage:
                raise DataLeakageError(msg)
            else:
                logger.warning(f"{msg} Discarding future records in non-strict mode.")

        return valid_records

    def filter_lookback_window(
        self,
        observations: List[Any],
        lookback_days: int,
        timestamp_attr: str = "detection_time"
    ) -> List[Any]:
        """
        Filter observations to window [T_ref - lookback_days, T_ref].
        Guarantees both backward bound and strict forward cutoff.
        """
        guarded = self.filter_and_guard_observations(observations, timestamp_attr)
        window_start = self.reference_time - timedelta(days=lookback_days)

        window_records = []
        for obs in guarded:
            t = getattr(obs, timestamp_attr)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if t >= window_start:
                window_records.append(obs)

        return window_records

    def compute_fire_history_metrics(
        self,
        cell_fires: List[CanonicalFireObservation],
    ) -> Dict[str, Any]:
        """
        Compute historical fire metrics for a grid cell strictly up to T_ref.
        """
        guarded_fires = self.filter_and_guard_observations(cell_fires, "detection_time")

        t7_start = self.reference_time - timedelta(days=7)
        t30_start = self.reference_time - timedelta(days=30)

        count_7d = 0
        count_30d = 0
        latest_fire_time: Optional[datetime] = None

        for f in guarded_fires:
            t = f.detection_time
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)

            if t >= t7_start:
                count_7d += 1
            if t >= t30_start:
                count_30d += 1

            if latest_fire_time is None or t > latest_fire_time:
                latest_fire_time = t

        days_since_last_fire = None
        if latest_fire_time is not None:
            delta = self.reference_time - latest_fire_time
            days_since_last_fire = round(delta.total_seconds() / 86400.0, 2)

        return {
            "fire_count_7d": count_7d,
            "fire_count_30d": count_30d,
            "days_since_last_fire": days_since_last_fire,
        }

    def compute_cumulative_precipitation(
        self,
        weather_history: List[CanonicalWeatherObservation],
        lookback_days: int = 7
    ) -> float:
        """
        Compute cumulative precipitation (mm) over the lookback window strictly up to T_ref.
        """
        guarded = self.filter_lookback_window(weather_history, lookback_days, "timestamp")
        total_precip = 0.0
        for w in guarded:
            if w.precipitation_mm is not None:
                total_precip += w.precipitation_mm
        return round(total_precip, 2)
