"""Integration tests for end-to-end data pipeline execution and serialization."""

import json
from pathlib import Path
from datetime import datetime, timezone
import pytest

from services.data_pipeline.adapters.base import BoundingBox
from services.data_pipeline.adapters.fire.modis import ModisFireAdapter
from services.data_pipeline.adapters.weather.imd import ImdWeatherAdapter
from services.data_pipeline.adapters.vegetation.sentinel import SentinelVegetationAdapter
from services.data_pipeline.adapters.terrain.cartodem import CartoDemTerrainAdapter
from services.data_pipeline.grid.generator import GridGenerator
from services.data_pipeline.features.pipeline import FeaturePipeline
from services.data_pipeline.outputs.manifest import ManifestBuilder
from services.data_pipeline.outputs.writers import DatasetWriter


def test_end_to_end_pipeline_execution(tmp_path: Path):
    # 1. Bounding box & Grid
    bbox = BoundingBox(min_lon=78.68, min_lat=30.15, max_lon=78.72, max_lat=30.19)
    generator = GridGenerator(resolution_meters=500)
    cells = generator.generate_grid_for_bbox(bbox, region_id="test_region")
    assert len(cells) > 0

    # 2. Ingest sample data
    fires_path = Path("data/sample/active_fires_sample.csv")
    weather_path = Path("data/sample/weather_observations_sample.csv")
    veg_path = Path("data/sample/vegetation_indices_sample.csv")
    terrain_path = Path("data/sample/terrain_dem_sample.csv")

    fires = ModisFireAdapter().parse_csv(fires_path)
    weather = ImdWeatherAdapter().parse_csv(weather_path)
    veg = SentinelVegetationAdapter().parse_csv(veg_path)
    terrain = CartoDemTerrainAdapter().parse_csv(terrain_path)

    # 3. Pipeline execution
    ref_time = datetime(2026, 5, 15, 0, 0, 0, tzinfo=timezone.utc)
    pipeline = FeaturePipeline(strict_anti_leakage=False)
    records, report = pipeline.process(
        cells=cells,
        reference_time=ref_time,
        fire_observations=fires,
        weather_observations=weather,
        vegetation_observations=veg,
        terrain_observations=terrain,
        generate_target=True,
        run_id="test_e2e_run",
    )

    assert len(records) == len(cells)
    assert report.total_records == len(cells)

    # 4. DataFrame conversion & deterministic checks
    df = pipeline.records_to_dataframe(records)
    assert not df.empty
    assert "grid_cell_id" in df.columns
    assert "target_fire_next_24h" in df.columns
    assert "fwi" in df.columns
    assert "temperature_c" in df.columns

    # 5. Output Writers
    csv_file = tmp_path / "features.csv"
    parquet_file = tmp_path / "features.parquet"
    geojson_file = tmp_path / "grid.geojson"
    manifest_file = tmp_path / "manifest.json"

    DatasetWriter.write_csv(df, csv_file)
    DatasetWriter.write_parquet(df, parquet_file)
    DatasetWriter.write_grid_geojson(cells, geojson_file)

    assert csv_file.exists()
    assert parquet_file.exists()
    assert geojson_file.exists()

    manifest = ManifestBuilder.create_manifest(
        run_id="test_e2e_run",
        region_id="test_region",
        region_name="Test Region",
        reference_date="2026-05-15",
        grid_cells_count=len(cells),
        feature_records_count=len(records),
        feature_columns=list(df.columns),
        target_column="target_fire_next_24h",
        sources_ingested={"fire": {"source": "MODIS", "count": len(fires)}},
        output_files={"features_csv": str(csv_file)},
    )
    ManifestBuilder.save_manifest(manifest, manifest_file)
    assert manifest_file.exists()
