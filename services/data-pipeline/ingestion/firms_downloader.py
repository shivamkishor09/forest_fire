"""Automated NASA FIRMS historical active fire observation ingestion."""

import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from ..adapters.base import BoundingBox
from ..common.types import CanonicalFireObservation
from ..adapters.fire.viirs import ViirsFireAdapter


class FirmsDownloader:
    """
    Downloads historical fire detections from NASA FIRMS Area API.
    Uses environment variable NASA_FIRMS_MAP_KEY (or FIRMS_MAP_KEY).
    Never overwrites existing raw files unless forced.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"):
        self.api_key = api_key or os.getenv("NASA_FIRMS_MAP_KEY") or os.getenv("FIRMS_MAP_KEY")
        if not self.api_key:
            # Check if present in .env
            env_path = Path(".env")
            if env_path.is_file():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() in ("NASA_FIRMS_MAP_KEY", "FIRMS_MAP_KEY") and v.strip():
                            self.api_key = v.strip()
                            break

        if not self.api_key:
            raise ValueError(
                "NASA FIRMS MAP Key not found in environment (NASA_FIRMS_MAP_KEY) or .env file. "
                "Obtain a free key at https://firms.modaps.eosdis.nasa.gov/api/map_key"
            )
        self.base_url = base_url

    def download_firms_data(
        self,
        region_name: str,
        bbox: BoundingBox,
        start_date: str,
        end_date: str,
        source: str = "VIIRS_SNPP_SP",
        output_dir: str = "data/raw/firms",
        force_redownload: bool = False,
    ) -> Path:
        """
        Download historical fire CSVs in 5-day increments and save combined raw CSV.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        filename = f"{region_name.lower().replace(' ', '_')}_{source}_{start_date}_{end_date}.csv"
        target_file = out_path / filename

        if target_file.exists() and not force_redownload:
            print(f"[FIRMS] Raw data already exists at: {target_file}")
            return target_file

        dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        dt_end = datetime.strptime(end_date, "%Y-%m-%d")

        extent_str = f"{bbox.min_lon},{bbox.min_lat},{bbox.max_lon},{bbox.max_lat}"
        all_dfs: List[pd.DataFrame] = []

        cur = dt_start
        print(f"[FIRMS] Fetching {source} detections for {region_name} ({start_date} to {end_date})...")

        while cur <= dt_end:
            cur_str = cur.strftime("%Y-%m-%d")
            # FIRMS Area API accepts day range [1..5]
            days_chunk = min(5, (dt_end - cur).days + 1)
            if days_chunk <= 0:
                break

            url = f"{self.base_url}/{self.api_key}/{source}/{extent_str}/{days_chunk}/{cur_str}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ForestFirePlatform/1.0)"})

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw_csv = resp.read().decode("utf-8")
                    lines = [l for l in raw_csv.strip().split("\n") if l.strip()]
                    if len(lines) > 1:
                        df_chunk = pd.read_csv(pd.io.common.StringIO(raw_csv))
                        all_dfs.append(df_chunk)
                        print(f"  [FIRMS] {cur_str} (+{days_chunk}d): {len(df_chunk)} fire detections")
                    else:
                        print(f"  [FIRMS] {cur_str} (+{days_chunk}d): 0 fire detections")
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                print(f"  [FIRMS Error] {cur_str}: HTTP {e.code} - {err_msg}")
            except Exception as e:
                print(f"  [FIRMS Error] {cur_str}: {e}")

            cur += timedelta(days=days_chunk)
            time.sleep(0.3)  # Respectful rate limiting

        if all_dfs:
            combined = pd.concat(all_dfs, ignore_index=True)
            # Deduplicate identical detections
            dedup_cols = [c for c in ["latitude", "longitude", "acq_date", "acq_time"] if c in combined.columns]
            if dedup_cols:
                combined = combined.drop_duplicates(subset=dedup_cols)
            combined.to_csv(target_file, index=False)
            print(f"[FIRMS] Saved {len(combined)} unique fire observations to: {target_file}")
        else:
            # Create empty template with standard columns
            cols = ["latitude", "longitude", "bright_ti4", "scan", "track", "acq_date", "acq_time", "confidence", "frp"]
            pd.DataFrame(columns=cols).to_csv(target_file, index=False)
            print(f"[FIRMS] 0 fire detections found; created empty file at: {target_file}")

        return target_file
