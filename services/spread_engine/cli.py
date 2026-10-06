"""Command-line interface for running standalone Cellular Automata fire spread simulations."""

import argparse
import json
import sys
from typing import Optional

from .common.config import ENGINE_VERSION
from .models.inputs import SpreadSimulationInput, IgnitionPoint, WindCondition, TerrainCondition
from .simulation.engine import SpreadSimulationEngine


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser for spread engine."""
    parser = argparse.ArgumentParser(
        prog="spread-engine",
        description="12-Hour Cellular Automata Forest Fire Spread Simulation Engine",
    )
    parser.add_argument(
        "--id",
        dest="sim_id",
        type=str,
        default="cli-sim-01",
        help="Simulation run identifier",
    )
    parser.add_argument(
        "--lat",
        dest="lat",
        type=float,
        required=True,
        help="Ignition latitude in WGS 84 degrees",
    )
    parser.add_argument(
        "--lon",
        dest="lon",
        type=float,
        required=True,
        help="Ignition longitude in WGS 84 degrees",
    )
    parser.add_argument(
        "--duration",
        dest="duration_hours",
        type=int,
        default=12,
        help="Simulation duration in hours (1-12, default: 12)",
    )
    parser.add_argument(
        "--rows",
        dest="grid_rows",
        type=int,
        default=50,
        help="Grid rows (default: 50)",
    )
    parser.add_argument(
        "--cols",
        dest="grid_cols",
        type=int,
        default=50,
        help="Grid columns (default: 50)",
    )
    parser.add_argument(
        "--resolution",
        dest="resolution_m",
        type=float,
        default=500.0,
        help="Spatial resolution in meters (default: 500.0)",
    )
    parser.add_argument(
        "--wind-speed",
        dest="wind_speed",
        type=float,
        default=5.0,
        help="Wind speed in m/s (default: 5.0)",
    )
    parser.add_argument(
        "--wind-dir",
        dest="wind_dir",
        type=float,
        default=180.0,
        help="Wind direction in degrees from North (meteorological 'from' direction, default: 180.0)",
    )
    parser.add_argument(
        "--slope",
        dest="slope_deg",
        type=float,
        default=0.0,
        help="Terrain slope in degrees (default: 0.0)",
    )
    parser.add_argument(
        "--aspect",
        dest="aspect_deg",
        type=float,
        default=180.0,
        help="Slope aspect downhill bearing in degrees (default: 180.0)",
    )
    parser.add_argument(
        "--fuel",
        dest="fuel_type",
        type=str,
        default="CONIFER_HIGH_FLAMMABILITY",
        help="Dominant fuel flammability class (default: CONIFER_HIGH_FLAMMABILITY)",
    )
    parser.add_argument(
        "--output",
        dest="output_file",
        type=str,
        default=None,
        help="Path to write output GeoJSON / JSON file",
    )
    parser.add_argument(
        "--format",
        dest="format",
        choices=["json", "geojson"],
        default="geojson",
        help="Output serialization format (json or geojson)",
    )
    return parser


def main(args: Optional[list] = None) -> int:
    """Execute simulation from parsed arguments."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    sim_input = SpreadSimulationInput(
        simulation_id=parsed.sim_id,
        ignition=IgnitionPoint(lat=parsed.lat, lon=parsed.lon),
        duration_hours=parsed.duration_hours,
        grid_rows=parsed.grid_rows,
        grid_cols=parsed.grid_cols,
        grid_resolution_meters=parsed.resolution_m,
        wind=WindCondition(speed_ms=parsed.wind_speed, direction_deg=parsed.wind_dir),
        terrain=TerrainCondition(
            slope_deg=parsed.slope_deg,
            aspect_deg=parsed.aspect_deg,
            fuel_type=parsed.fuel_type,
        ),
    )

    engine = SpreadSimulationEngine()
    result = engine.execute(sim_input)

    if parsed.format == "geojson":
        output_data = result.to_geojson()
    else:
        output_data = result.to_dict()

    json_str = json.dumps(output_data, indent=2)

    if parsed.output_file:
        with open(parsed.output_file, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Simulation {result.simulation_id} complete ({result.duration_hours}h). Saved to {parsed.output_file}")
    else:
        # Print summary and sample to stdout
        print(f"Simulation ID: {result.simulation_id} (Engine: {result.engine_version})")
        print(f"Total Burned Area: {result.total_area_burned_ha} ha")
        print(f"Peak Spread Velocity: {result.peak_spread_velocity_kmh} km/h")
        print(f"Timesteps Generated: {len(result.timesteps)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
