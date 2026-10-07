"""Historical daily meteorological data ingestion using Open-Meteo ERA5 reanalysis."""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from ..adapters.base import BoundingBox
from ..features.fire_weather import FwiCalculator


class WeatherDownloader:
    """
    Downloads historical ERA5 meteorological variables for spatial bounding boxes.
    Saves raw daily time series into data/raw/weather/.
    Never overwrites existing raw data unless forced.
    """

    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    def download_weather_data(
        self,
        region_name: str,
        bbox: BoundingBox,
        start_date: str,
        end_date: str,
        output_dir: str = "data/raw/weather",
        force_redownload: bool = False,
    ) -> Path:
        """
        Download historical daily weather for representative sub-points in the bbox.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        filename = f"{region_name.lower().replace(' ', '_')}_weather_{start_date}_{end_date}.csv"
        target_file = out_path / filename

        if target_file.exists() and not force_redownload:
            print(f"[Weather] Raw weather already exists at: {target_file}")
            return target_file

        # Sample grid of sample points across bbox (center and corners)
        lat_pts = [bbox.min_lat + 0.25 * (bbox.max_lat - bbox.min_lat),
                   bbox.min_lat + 0.75 * (bbox.max_lat - bbox.min_lat)]
        lon_pts = [bbox.min_lon + 0.25 * (bbox.max_lon - bbox.min_lon),
                   bbox.min_lon + 0.75 * (bbox.max_lon - bbox.min_lon)]

        sample_coords = [(round(lat, 4), round(lon, 4)) for lat in lat_pts for lon in lon_pts]

        print(f"[Weather] Fetching ERA5 daily weather for {region_name} across {len(sample_coords)} stations ({start_date} to {end_date})...")

        all_records: List[Dict[str, Any]] = []

        for idx, (lat, lon) in enumerate(sample_coords):
            station_id = f"STATION_{region_name.upper()[:3]}_{idx+1}"
            url = (
                f"{self.BASE_URL}?latitude={lat}&longitude={lon}"
                f"&start_date={start_date}&end_date={end_date}"
                f"&daily=temperature_2m_max,relative_humidity_2m_mean,precipitation_sum,"
                f"wind_speed_10m_max,wind_direction_10m_dominant&timezone=UTC"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ForestFirePlatform/1.0)"})

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    daily = data.get("daily", {})
                    times = daily.get("time", [])
                    temps = daily.get("temperature_2m_max", [])
                    rhs = daily.get("relative_humidity_2m_mean", [])
                    rains = daily.get("precipitation_sum", [])
                    winds_kmh = daily.get("wind_speed_10m_max", [])
                    wind_dirs = daily.get("wind_direction_10m_dominant", [])

                    for i, t in enumerate(times):
                        t_c = float(temps[i]) if temps[i] is not None else 30.0
                        rh = float(rhs[i]) if rhs[i] is not None else 30.0
                        rain_24h = float(rains[i]) if rains[i] is not None else 0.0
                        w_kmh = float(winds_kmh[i]) if winds_kmh[i] is not None else 10.0
                        w_ms = round(w_kmh / 3.6, 2)
                        w_dir = float(wind_dirs[i]) if wind_dirs[i] is not None else 180.0

                        all_records.append({
                            "station_id": station_id,
                            "latitude": lat,
                            "longitude": lon,
                            "observation_date": t,
                            "temperature_c": t_c,
                            "relative_humidity_pct": rh,
                            "wind_speed_ms": w_ms,
                            "wind_direction_deg": w_dir,
                            "precipitation_mm": rain_24h,
                        })
                print(f"  [Weather] Station {station_id} ({lat}, {lon}): {len(times)} days fetched")
            except Exception as e:
                print(f"  [Weather Error] Station {station_id}: {e}")

            time.sleep(0.3)

        if all_records:
            df = pd.DataFrame(all_records)
            df.to_csv(target_file, index=False)
            print(f"[Weather] Saved {len(df)} daily weather records to: {target_file}")
        else:
            pd.DataFrame().to_csv(target_file, index=False)

        return target_file
