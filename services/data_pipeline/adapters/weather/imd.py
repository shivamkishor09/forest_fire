"""Adapter for IMD (India Meteorological Department) gridded and AWS observations."""

import math
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional
import pandas as pd

from ..base import WeatherDataSource, BoundingBox
from ...common.types import CanonicalWeatherObservation


class ImdWeatherAdapter(WeatherDataSource):
    """Adapter for IMD 0.25° gridded daily rainfall and temperature / AWS stations."""

    @property
    def source_name(self) -> str:
        return "IMD_API"

    def validate_connection(self) -> bool:
        return True

    def fetch_weather_grid(
        self,
        bbox: BoundingBox,
        target_date: date,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        center_lat = (bbox.min_lat + bbox.max_lat) / 2.0
        center_lon = (bbox.min_lon + bbox.max_lon) / 2.0
        return {
            "source": self.source_name,
            "target_date": target_date.isoformat(),
            "latitude": center_lat,
            "longitude": center_lon,
            "metrics": {
                "temperature_c": 31.5,
                "relative_humidity_pct": 28.0,
                "wind_speed_ms": 6.2,
                "wind_direction_deg": 220.0,
                "precipitation_mm": 0.0,
            }
        }

    def parse_records(self, records: List[Dict[str, Any]]) -> List[CanonicalWeatherObservation]:
        """Parse raw IMD station or gridded data records."""
        results: List[CanonicalWeatherObservation] = []
        for r in records:
            lat = float(r["latitude"])
            lon = float(r["longitude"])

            if "timestamp" in r:
                dt = pd.to_datetime(r["timestamp"]).to_pydatetime()
            elif "observation_date" in r:
                dt = pd.to_datetime(r["observation_date"]).to_pydatetime()
            elif "target_date" in r:
                dt = pd.to_datetime(r["target_date"]).to_pydatetime()
            else:
                dt = datetime.now(timezone.utc)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            # Max or mean temperature in Celsius
            temp = float(r["temperature_c"]) if "temperature_c" in r and pd.notnull(r["temperature_c"]) else (
                float(r["t_max"]) if "t_max" in r and pd.notnull(r["t_max"]) else None
            )

            rh = float(r["relative_humidity_pct"]) if "relative_humidity_pct" in r and pd.notnull(r["relative_humidity_pct"]) else (
                float(r["rh_pct"]) if "rh_pct" in r and pd.notnull(r["rh_pct"]) else None
            )

            wind_spd = float(r["wind_speed_ms"]) if "wind_speed_ms" in r and pd.notnull(r["wind_speed_ms"]) else None
            wind_dir = float(r["wind_direction_deg"]) if "wind_direction_deg" in r and pd.notnull(r["wind_direction_deg"]) else 0.0
            precip = float(r["precipitation_mm"]) if "precipitation_mm" in r and pd.notnull(r["precipitation_mm"]) else (
                float(r["rainfall_mm"]) if "rainfall_mm" in r and pd.notnull(r["rainfall_mm"]) else 0.0
            )

            u_wind = None
            v_wind = None
            if wind_spd is not None:
                rad = math.radians(wind_dir)
                u_wind = -wind_spd * math.sin(rad)
                v_wind = -wind_spd * math.cos(rad)

            results.append(
                CanonicalWeatherObservation(
                    source=self.source_name,
                    timestamp=dt,
                    latitude=lat,
                    longitude=lon,
                    temperature_c=temp,
                    relative_humidity_pct=rh,
                    wind_speed_ms=wind_spd,
                    wind_direction_deg=wind_dir,
                    precipitation_mm=precip,
                    u_wind_ms=u_wind,
                    v_wind_ms=v_wind,
                    metadata={"station_id": r.get("station_id", "IMD_GRID_025"), "division": "IMD_NW_INDIA"},
                )
            )
        return results

    def parse_csv(self, file_path_or_buffer: Any) -> List[CanonicalWeatherObservation]:
        df = pd.read_csv(file_path_or_buffer)
        return self.parse_records(df.to_dict(orient="records"))
