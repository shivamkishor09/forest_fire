"""Output writers for tabular data (CSV, Parquet) and spatial formats (GeoJSON)."""

import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import geopandas as gpd

from ..common.types import GridCellDefinition, CanonicalFeatureRecord


class DatasetWriter:
    """Writes model-ready datasets and spatial grids in standard formats."""

    @staticmethod
    def write_csv(df: pd.DataFrame, target_path: Path) -> Path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target_path, index=False)
        return target_path

    @staticmethod
    def write_parquet(df: pd.DataFrame, target_path: Path) -> Path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Convert list columns to strings for Parquet compatibility if needed
        clean_df = df.copy()
        if "imputed_fields" in clean_df.columns:
            clean_df["imputed_fields"] = clean_df["imputed_fields"].apply(lambda x: ",".join(x) if isinstance(x, list) else str(x))
        clean_df.to_parquet(target_path, index=False, engine="pyarrow", compression="snappy")
        return target_path

    @staticmethod
    def write_grid_geojson(cells: List[GridCellDefinition], target_path: Path) -> Path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        features = []
        for c in cells:
            features.append({
                "type": "Feature",
                "id": c.cell_id,
                "properties": {
                    "cell_id": c.cell_id,
                    "region_id": c.region_id,
                    "cell_code": c.cell_code,
                    "centroid_lat": c.centroid_lat,
                    "centroid_lon": c.centroid_lon,
                    "resolution_meters": c.resolution_meters,
                    "row_idx": c.row_idx,
                    "col_idx": c.col_idx,
                },
                "geometry": c.geometry,
            })

        fc = {
            "type": "FeatureCollection",
            "features": features,
        }
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(fc, f)
        return target_path
