"""Adapter for NASA/NOAA VIIRS (VNP14IMGTDL / VJ114IMGTDL) 375m active fire detections."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from ..base import FireDataSource, BoundingBox
from ...common.types import CanonicalFireObservation


class ViirsFireAdapter(FireDataSource):
    """Adapter for VIIRS 375m active fire detections from Suomi-NPP and NOAA-20."""

    @property
    def source_name(self) -> str:
        return "NASA_NOAA_VIIRS"

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
        """Parse raw VIIRS tabular records into canonical observations."""
        results: List[CanonicalFireObservation] = []
        for r in records:
            lat = float(r["latitude"])
            lon = float(r["longitude"])

            # Datetime parsing
            if "detection_time" in r and isinstance(r["detection_time"], datetime):
                dt = r["detection_time"]
            elif "detected_at" in r:
                dt = pd.to_datetime(r["detected_at"]).to_pydatetime()
            elif "acq_date" in r and "acq_time" in r:
                time_str = str(r["acq_time"]).zfill(4)
                dt_str = f"{r['acq_date']} {time_str[:2]}:{time_str[2:]}:00"
                dt = pd.to_datetime(dt_str).to_pydatetime()
            else:
                dt = datetime.now(timezone.utc)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            # VIIRS uses low/nominal/high or numeric
            conf = r.get("confidence", r.get("confidence_pct", "nominal"))
            if isinstance(conf, str):
                conf_map = {"l": 30.0, "low": 30.0, "n": 75.0, "nominal": 75.0, "h": 95.0, "high": 95.0}
                conf_val = conf_map.get(conf.lower(), 75.0)
            else:
                conf_val = float(conf)

            # VIIRS FRP
            frp = float(r["frp"]) if "frp" in r and pd.notnull(r["frp"]) else (
                float(r["frp_mw"]) if "frp_mw" in r and pd.notnull(r["frp_mw"]) else None
            )

            # VIIRS Brightness temperature (I-4 channel ~375m)
            bt = float(r["bright_ti4"]) if "bright_ti4" in r and pd.notnull(r["bright_ti4"]) else (
                float(r["brightness_temp_k"]) if "brightness_temp_k" in r and pd.notnull(r["brightness_temp_k"]) else None
            )

            results.append(
                CanonicalFireObservation(
                    source=self.source_name,
                    detection_time=dt,
                    latitude=lat,
                    longitude=lon,
                    confidence_pct=conf_val,
                    frp_mw=frp,
                    brightness_temp_k=bt,
                    scan_track=f"{r.get('scan', '0.375')}/{r.get('track', '0.375')}",
                    metadata={"satellite": r.get("satellite", "Suomi-NPP"), "instrument": "VIIRS"},
                )
            )
        return results

    def parse_csv(self, file_path_or_buffer: Any) -> List[CanonicalFireObservation]:
        """Parse raw CSV file from VIIRS."""
        df = pd.read_csv(file_path_or_buffer)
        return self.parse_records(df.to_dict(orient="records"))
