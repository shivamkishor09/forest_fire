"""Adapter for ECMWF ERA5 reanalysis and atmospheric forecast grids."""

import math
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional
import pandas as pd

from ..base import WeatherDataSource, BoundingBox
from ...common.types import CanonicalWeatherObservation


class Era5WeatherAdapter(WeatherDataSource):
    """Adapter for ECMWF ERA5 meteorological datasets."""

    @property
    def source_name(self) -> str:
        return "ECMWF_ERA5"

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
                "temperature_c": 28.5,
                "relative_humidity_pct": 35.0,
                "wind_speed_ms": 4.5,
                "wind_direction_deg": 180.0,
                "precipitation_mm": 0.0,
            }
        }

    def parse_records(self, records: List[Dict[str, Any]]) -> List[CanonicalWeatherObservation]:
        """Parse raw ERA5 point/grid observations into canonical records."""
        results: List[CanonicalWeatherObservation] = []
        for r in records:
            lat = float(r["latitude"])
            lon = float(r["longitude"])

            # Timestamp parsing
            if "timestamp" in r:
                dt = pd.to_datetime(r["timestamp"]).to_pydatetime()
            elif "target_date" in r:
                dt = pd.to_datetime(r["target_date"]).to_pydatetime()
            else:
                dt = datetime.now(timezone.utc)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            # Temperature handling: Kelvin to Celsius if > 150
            temp = None
            if "temperature_k" in r and pd.notnull(r["temperature_k"]):
                temp = float(r["temperature_k"]) - 273.15
            elif "t2m" in r and pd.notnull(r["t2m"]):
                val = float(r["t2m"])
                temp = (val - 273.15) if val > 150.0 else val
            elif "temperature_c" in r and pd.notnull(r["temperature_c"]):
                temp = float(r["temperature_c"])

            # Relative humidity
            rh = float(r["relative_humidity_pct"]) if "relative_humidity_pct" in r and pd.notnull(r["relative_humidity_pct"]) else (
                float(r["rh"]) if "rh" in r and pd.notnull(r["rh"]) else None
            )

            # Wind speed / direction and U/V vectors
            u_wind = float(r["u10"]) if "u10" in r and pd.notnull(r["u10"]) else (
                float(r["u_wind_ms"]) if "u_wind_ms" in r and pd.notnull(r["u_wind_ms"]) else None
            )
            v_wind = float(r["v10"]) if "v10" in r and pd.notnull(r["v10"]) else (
                float(r["v_wind_ms"]) if "v_wind_ms" in r and pd.notnull(r["v_wind_ms"]) else None
            )

            wind_speed = None
            wind_dir = None

            if "wind_speed_ms" in r and pd.notnull(r["wind_speed_ms"]):
                wind_speed = float(r["wind_speed_ms"])
                wind_dir = float(r["wind_direction_deg"]) if "wind_direction_deg" in r and pd.notnull(r["wind_direction_deg"]) else 0.0
                if u_wind is None:
                    rad = math.radians(wind_dir)
                    u_wind = -wind_speed * math.sin(rad)
                    v_wind = -wind_speed * math.cos(rad)
            elif u_wind is not None and v_wind is not None:
                wind_speed = math.sqrt(u_wind ** 2 + v_wind ** 2)
                # Meteorological direction from which wind blows
                wind_dir = (math.degrees(math.atan2(-u_wind, -v_wind)) + 360.0) % 360.0

            # Precipitation (ERA5 tp in meters or mm)
            precip = 0.0
            if "tp" in r and pd.notnull(r["tp"]):
                precip = float(r["tp"]) * 1000.0 if float(r["tp"]) < 2.0 else float(r["tp"])
            elif "precipitation_mm" in r and pd.notnull(r["precipitation_mm"]):
                precip = float(r["precipitation_mm"])

            results.append(
                CanonicalWeatherObservation(
                    source=self.source_name,
                    timestamp=dt,
                    latitude=lat,
                    longitude=lon,
                    temperature_c=temp,
                    relative_humidity_pct=rh,
                    wind_speed_ms=wind_speed,
                    wind_direction_deg=wind_dir,
                    precipitation_mm=precip,
                    u_wind_ms=u_wind,
                    v_wind_ms=v_wind,
                    metadata={"provider": "ECMWF", "product": "ERA5_REANALYSIS"},
                )
            )
        return results

    def parse_csv(self, file_path_or_buffer: Any) -> List[CanonicalWeatherObservation]:
        df = pd.read_csv(file_path_or_buffer)
        return self.parse_records(df.to_dict(orient="records"))
