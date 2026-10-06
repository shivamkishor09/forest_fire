import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
from datetime import datetime, timezone

from services.data_pipeline.adapters.base import BoundingBox
from services.data_pipeline.adapters.fire.modis import ModisFireAdapter
from services.data_pipeline.adapters.weather.imd import ImdWeatherAdapter
from services.data_pipeline.adapters.vegetation.sentinel import SentinelVegetationAdapter
from services.data_pipeline.adapters.terrain.cartodem import CartoDemTerrainAdapter
from services.data_pipeline.grid.generator import GridGenerator
from services.data_pipeline.features.pipeline import FeaturePipeline
from services.data_pipeline.outputs.manifest import ManifestBuilder
from services.data_pipeline.outputs.writers import DatasetWriter


def generate_region_dataset(
    region_id: str,
    region_name: str,
    region_code: str,
    bbox: BoundingBox,
    output_subdir: str,
):
    print(f"Generating dataset for {region_name} ({region_code})...")
    generator = GridGenerator(resolution_meters=500)
    cells = generator.generate_grid_for_bbox(bbox, region_id=region_code)
    print(f"  Generated {len(cells)} grid cells.")

    # Load sample inputs
    fires_path = Path("data/sample/active_fires_sample.csv")
    weather_path = Path("data/sample/weather_observations_sample.csv")
    veg_path = Path("data/sample/vegetation_indices_sample.csv")
    terrain_path = Path("data/sample/terrain_dem_sample.csv")

    fires = ModisFireAdapter().parse_csv(fires_path)
    weather = ImdWeatherAdapter().parse_csv(weather_path)
    veg = SentinelVegetationAdapter().parse_csv(veg_path)
    terrain = CartoDemTerrainAdapter().parse_csv(terrain_path)

    # Process pipeline
    ref_time = datetime.now(timezone.utc)
    pipeline = FeaturePipeline(strict_anti_leakage=False)
    records, report = pipeline.process(
        cells=cells,
        reference_time=ref_time,
        fire_observations=fires,
        weather_observations=weather,
        vegetation_observations=veg,
        terrain_observations=terrain,
        generate_target=True,
        run_id=f"run_{output_subdir}",
    )

    df = pipeline.records_to_dataframe(records)
    out_dir = Path(f"data/processed/{output_subdir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_file = out_dir / "features.csv"
    parquet_file = out_dir / "features.parquet"
    geojson_file = out_dir / "grid_500m.geojson"
    manifest_file = out_dir / "manifest.json"

    DatasetWriter.write_csv(df, csv_file)
    DatasetWriter.write_parquet(df, parquet_file)
    DatasetWriter.write_grid_geojson(cells, geojson_file)

    manifest = ManifestBuilder.create_manifest(
        run_id=f"run_{output_subdir}",
        region_id=region_id,
        region_name=region_name,
        reference_date=ref_time.strftime("%Y-%m-%d"),
        grid_cells_count=len(cells),
        feature_records_count=len(records),
        feature_columns=list(df.columns),
        target_column="target_fire_next_24h",
        sources_ingested={
            "fire": {"source": "MODIS", "count": len(fires)},
            "weather": {"source": "IMD", "count": len(weather)},
            "vegetation": {"source": "Sentinel-2", "count": len(veg)},
            "terrain": {"source": "CartoDEM", "count": len(terrain)},
        },
        output_files={
            "features_parquet": "features.parquet",
            "features_csv": "features.csv",
            "grid_geojson": "grid_500m.geojson",
        },
    )
    ManifestBuilder.save_manifest(manifest, manifest_file)
    print(f"  Saved processed dataset to {out_dir}")


if __name__ == "__main__":
    # 1. Garhwal (Uttarakhand)
    generate_region_dataset(
        region_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        region_name="Garhwal Forest Division",
        region_code="UTTARAKHAND_GARHWAL",
        bbox=BoundingBox(min_lon=78.68, min_lat=30.15, max_lon=78.88, max_lat=30.30),
        output_subdir="sample_run_garhwal",
    )

    # 2. Wayanad (Kerala)
    generate_region_dataset(
        region_id="7ca85f64-5717-4562-b3fc-2c963f66afa7",
        region_name="Wayanad Wildlife Sanctuary",
        region_code="WESTERN_GHATS_WAYANAD",
        bbox=BoundingBox(min_lon=76.20, min_lat=11.62, max_lon=76.32, max_lat=11.72),
        output_subdir="sample_run_wayanad",
    )
    print("Done generating processed datasets!")
