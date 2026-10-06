"""Command-line interface (CLI) for running the environmental data ingestion and preprocessing pipeline."""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .adapters.base import BoundingBox
from .adapters.fire.modis import ModisFireAdapter
from .adapters.weather.imd import ImdWeatherAdapter
from .adapters.vegetation.sentinel import SentinelVegetationAdapter
from .adapters.terrain.cartodem import CartoDemTerrainAdapter
from .grid.generator import GridGenerator
from .features.pipeline import FeaturePipeline
from .outputs.manifest import ManifestBuilder
from .outputs.quality_report import QualityReportWriter
from .outputs.writers import DatasetWriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DataPipelineCLI")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Predictive Forest Fire Risk & Spread Simulation - Environmental Data Pipeline (Phase 4)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run pipeline command
    run_parser = subparsers.add_parser("run", help="Run end-to-end data pipeline")
    run_parser.add_argument("--region-file", type=str, default="data/sample/region_garhwal.geojson")
    run_parser.add_argument("--reference-date", type=str, default="2026-05-15")
    run_parser.add_argument("--fires-file", type=str, default="data/sample/active_fires_sample.csv")
    run_parser.add_argument("--weather-file", type=str, default="data/sample/weather_observations_sample.csv")
    run_parser.add_argument("--veg-file", type=str, default="data/sample/vegetation_indices_sample.csv")
    run_parser.add_argument("--terrain-file", type=str, default="data/sample/terrain_dem_sample.csv")
    run_parser.add_argument("--output-dir", type=str, default="data/processed/sample_run")
    run_parser.add_argument("--resolution", type=int, default=500)
    run_parser.add_argument("--generate-target", action="store_true", help="Include 24h future fire target label")
    run_parser.add_argument("--strict-anti-leakage", action="store_true", default=False)
    run_parser.add_argument("--imputation-strategy", type=str, default="regional_default", choices=["regional_default", "median"])

    # Generate grid command
    grid_parser = subparsers.add_parser("generate-grid", help="Generate 500m grid for a region GeoJSON")
    grid_parser.add_argument("--region-file", type=str, default="data/sample/region_garhwal.geojson")
    grid_parser.add_argument("--output-file", type=str, default="data/processed/grid_500m.geojson")
    grid_parser.add_argument("--resolution", type=int, default=500)

    return parser.parse_args()


def run_pipeline(args):
    logger.info("Initializing Data Ingestion & Preprocessing Pipeline (Phase 4)...")
    region_path = Path(args.region_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not region_path.exists():
        logger.error(f"Region file not found: {region_path}")
        sys.exit(1)

    # 1. Load region GeoJSON
    with open(region_path, "r", encoding="utf-8") as f:
        region_fc = json.load(f)
    feature = region_fc["features"][0]
    region_id = feature.get("properties", {}).get("id", "region_garhwal")
    region_name = feature.get("properties", {}).get("name", "Garhwal Forest Division")
    region_poly = feature.get("geometry")

    # Determine bounding box from region geometry
    coords = region_poly["coordinates"][0]
    lons = [pt[0] for pt in coords]
    lats = [pt[1] for pt in coords]
    bbox = BoundingBox(
        min_lon=min(lons),
        min_lat=min(lats),
        max_lon=max(lons),
        max_lat=max(lats),
    )

    # 2. Generate 500m spatial grid
    logger.info(f"Generating {args.resolution}m spatial grid for region {region_id}...")
    grid_gen = GridGenerator(resolution_meters=args.resolution)
    cells = grid_gen.generate_grid_for_bbox(
        bbox=bbox,
        region_id=region_id,
        region_polygon=region_poly,
    )
    logger.info(f"Generated {len(cells)} grid cells within region boundary.")

    # 3. Ingest raw observations through adapters
    logger.info("Ingesting observations via source adapters...")
    modis_adapter = ModisFireAdapter()
    imd_adapter = ImdWeatherAdapter()
    sentinel_adapter = SentinelVegetationAdapter()
    cartodem_adapter = CartoDemTerrainAdapter()

    fires = modis_adapter.parse_csv(args.fires_file) if Path(args.fires_file).exists() else []
    weather = imd_adapter.parse_csv(args.weather_file) if Path(args.weather_file).exists() else []
    veg = sentinel_adapter.parse_csv(args.veg_file) if Path(args.veg_file).exists() else []
    terrain = cartodem_adapter.parse_csv(args.terrain_file) if Path(args.terrain_file).exists() else []

    logger.info(
        f"Ingested: {len(fires)} fire records, {len(weather)} weather records, "
        f"{len(veg)} vegetation records, {len(terrain)} terrain records."
    )

    # 4. Execute Feature Engineering Pipeline
    ref_dt = datetime.strptime(args.reference_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    run_id = f"run_{ref_dt.strftime('%Y%m%d')}_{region_id}"

    pipeline = FeaturePipeline(
        strict_anti_leakage=args.strict_anti_leakage,
        imputation_strategy=args.imputation_strategy,
    )

    logger.info(f"Executing FeaturePipeline for reference cutoff {ref_dt.isoformat()}...")
    records, quality_report = pipeline.process(
        cells=cells,
        reference_time=ref_dt,
        fire_observations=fires,
        weather_observations=weather,
        vegetation_observations=veg,
        terrain_observations=terrain,
        generate_target=args.generate_target,
        run_id=run_id,
    )

    # 5. Convert to DataFrame and Write Outputs
    df = pipeline.records_to_dataframe(records)
    csv_path = output_dir / "features.csv"
    parquet_path = output_dir / "features.parquet"
    grid_path = output_dir / "grid_500m.geojson"
    report_json_path = output_dir / "quality_report.json"
    report_md_path = output_dir / "quality_report.md"
    manifest_path = output_dir / "manifest.json"

    DatasetWriter.write_csv(df, csv_path)
    DatasetWriter.write_parquet(df, parquet_path)
    DatasetWriter.write_grid_geojson(cells, grid_path)
    QualityReportWriter.save_json(quality_report, report_json_path)
    QualityReportWriter.save_markdown(quality_report, report_md_path)

    # 6. Create & Save Manifest
    manifest = ManifestBuilder.create_manifest(
        run_id=run_id,
        region_id=region_id,
        region_name=region_name,
        reference_date=args.reference_date,
        grid_cells_count=len(cells),
        feature_records_count=len(records),
        feature_columns=list(df.columns),
        target_column="target_fire_next_24h" if args.generate_target else None,
        sources_ingested={
            "fire": {"source": modis_adapter.source_name, "count": len(fires)},
            "weather": {"source": imd_adapter.source_name, "count": len(weather)},
            "vegetation": {"source": sentinel_adapter.source_name, "count": len(veg)},
            "terrain": {"source": cartodem_adapter.source_name, "count": len(terrain)},
        },
        output_files={
            "features_csv": str(csv_path),
            "features_parquet": str(parquet_path),
            "grid_geojson": str(grid_path),
            "quality_report_json": str(report_json_path),
            "quality_report_md": str(report_md_path),
            "manifest_json": str(manifest_path),
        },
        resolution_meters=args.resolution,
    )
    ManifestBuilder.save_manifest(manifest, manifest_path)

    logger.info("Pipeline execution completed successfully!")
    logger.info(f"Outputs saved to {output_dir}")
    logger.info(f"Quality Summary: Clean: {quality_report.clean_records_pct}%, Imputed: {quality_report.imputed_records_pct}%")


def main():
    args = parse_args()
    if args.command == "run":
        run_pipeline(args)
    elif args.command == "generate-grid":
        region_path = Path(args.region_file)
        with open(region_path, "r", encoding="utf-8") as f:
            region_fc = json.load(f)
        feature = region_fc["features"][0]
        region_id = feature.get("properties", {}).get("id", "region_grid")
        coords = feature["geometry"]["coordinates"][0]
        lons = [pt[0] for pt in coords]
        lats = [pt[1] for pt in coords]
        bbox = BoundingBox(min_lon=min(lons), min_lat=min(lats), max_lon=max(lons), max_lat=max(lats))

        grid_gen = GridGenerator(resolution_meters=args.resolution)
        cells = grid_gen.generate_grid_for_bbox(bbox, region_id, feature["geometry"])
        out_path = Path(args.output_file)
        DatasetWriter.write_grid_geojson(cells, out_path)
        logger.info(f"Exported {len(cells)} cells to {out_path}")


if __name__ == "__main__":
    main()
