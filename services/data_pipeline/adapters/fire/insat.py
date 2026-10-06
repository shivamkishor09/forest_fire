"""Adapter for ISRO INSAT-3D / 3DR thermal anomaly and fire products."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from ..base import FireDataSource, BoundingBox
from ...common.types import CanonicalFireObservation


class InsatFireAdapter(FireDataSource):
    """Adapter for ISRO INSAT-3D / 3DR geostationary forest fire detections."""

    @property
    def source_name(self) -> str:
        return "ISRO_INSAT_3D"

    def validate_connection(self) -> bool:
        return True

    def fetch_active_fires(
        self,
        bbox: BoundingBox,
        start_time: datetime,
        end_time: datetime,
        min_confidence: float = 50.0
    ) -> List[Dict[str, Any]]:
        canonical = self.fetch_canonical_fires(bbox, start_time, end_time, min_confidence)
        return [c.model_dump() for c in canonical]

    def parse_records(self, records: List[Dict[str, Any]]) -> List[CanonicalFireObservation]:
        """Parse raw INSAT fire anomaly records."""
        results: List[CanonicalFireObservation] = []
        for r in records:
            lat = float(r["latitude"])
            lon = float(r["longitude"])

            if "observation_time" in r:
                dt = pd.to_datetime(r["observation_time"]).to_pydatetime()
            elif "detected_at" in r:
                dt = pd.to_datetime(r["detected_at"]).to_pydatetime()
            else:
                dt = datetime.now(timezone.utc)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            conf = float(r.get("confidence_pct", r.get("confidence", 70.0)))
            frp = float(r["frp_mw"]) if "frp_mw" in r and pd.notnull(r["frp_mw"]) else None
            bt = float(r["brightness_temp_k"]) if "brightness_temp_k" in r and pd.notnull(r["brightness_temp_k"]) else None

            results.append(
                CanonicalFireObservation(
                    source=self.source_name,
                    detection_time=dt,
                    latitude=lat,
                    longitude=lon,
                    confidence_pct=conf,
                    frp_mw=frp,
                    brightness_temp_k=bt,
                    scan_track="4.0km/4.0km",
                    metadata={"satellite": "INSAT-3D/3DR", "orbit": "Geostationary (82°E / 74°E)"},
                )
            )
        return results
