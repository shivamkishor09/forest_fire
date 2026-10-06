"""Integration tests for end-to-end 12-hour Cellular Automata fire spread simulation."""

import pytest
import numpy as np
from services.spread_engine.models.config import SimulationInput, EnvironmentalConditions
from services.spread_engine.models.inputs import SpreadSimulationInput, IgnitionPoint, WindCondition, TerrainCondition
from services.spread_engine.simulation.engine import SpreadSimulationEngine
from services.spread_engine.simulation.runner import CellularAutomataRunner
from services.spread_engine.common.exceptions import (
    UnsupportedDurationError,
    GridValidationError,
    InvalidEnvironmentalDataError,
)


class TestSpreadIntegration:
    """End-to-end simulation pipeline verification."""

    def test_full_12_hour_simulation(self):
        """Run complete 12-hour simulation and verify output contracts."""
        runner = CellularAutomataRunner()
        env = EnvironmentalConditions(
            wind_speed_ms=8.0,
            wind_direction_deg=225.0,  # Blows toward 45° (North-East)
        )
        sim_input = SimulationInput(
            simulation_id="sim-integ-12h",
            ignition_lat=30.2,
            ignition_lon=78.7,
            duration_hours=12,
            grid_resolution_meters=500,
            grid_rows=40,
            grid_cols=40,
            environment=env,
            fuel_type="CONIFER_HIGH_FLAMMABILITY",
        )

        result = runner.run_simulation(sim_input)

        assert result.simulation_id == "sim-integ-12h"
        assert result.duration_hours == 12
        assert len(result.timesteps) == 12
        assert result.total_area_burned_ha > 0

        # Verify monotonicity of burned area progression
        for i in range(1, len(result.timesteps)):
            prev = result.timesteps[i - 1]
            curr = result.timesteps[i]
            assert curr.step_hour == i + 1
            assert curr.burned_area_ha >= prev.burned_area_ha
            assert curr.boundary_polygon["type"] in ("Polygon", "MultiPolygon")
            assert curr.spread_velocity_kmh > 0
            assert 0.0 <= curr.spread_direction_deg <= 360.0

        # Serialization to dict and GeoJSON
        result_dict = result.to_dict()
        assert "timesteps" in result_dict
        assert len(result_dict["timesteps"]) == 12

        geojson_fc = result.to_geojson()
        assert geojson_fc["type"] == "FeatureCollection"
        assert len(geojson_fc["features"]) == 12

    def test_deterministic_reproducibility(self):
        """Two identical runs must produce 100% bit-for-bit identical outputs."""
        engine = SpreadSimulationEngine()
        sim_input = SpreadSimulationInput(
            simulation_id="sim-repro-01",
            ignition=IgnitionPoint(lat=30.25, lon=78.75),
            duration_hours=6,
            grid_rows=30,
            grid_cols=30,
            grid_resolution_meters=500.0,
            wind=WindCondition(speed_ms=6.0, direction_deg=180.0),
            deterministic=True,
            random_seed=42,
        )

        run_1 = engine.execute(sim_input)
        run_2 = engine.execute(sim_input)

        assert run_1.total_area_burned_ha == run_2.total_area_burned_ha
        assert run_1.peak_spread_velocity_kmh == run_2.peak_spread_velocity_kmh
        assert len(run_1.timesteps) == len(run_2.timesteps)

        for ts1, ts2 in zip(run_1.timesteps, run_2.timesteps):
            assert ts1.step_hour == ts2.step_hour
            assert ts1.burned_area_ha == ts2.burned_area_ha
            assert ts1.spread_velocity_kmh == ts2.spread_velocity_kmh
            assert ts1.spread_direction_deg == ts2.spread_direction_deg
            assert ts1.intensity_mw == ts2.intensity_mw
            assert ts1.boundary_polygon == ts2.boundary_polygon

    def test_input_validation_errors(self):
        """Simulation must reject out-of-bounds parameters."""
        engine = SpreadSimulationEngine()

        # Duration > 12 hours rejected
        with pytest.raises(UnsupportedDurationError):
            engine.execute(
                SimulationInput(
                    simulation_id="sim-invalid",
                    ignition_lat=30.0,
                    ignition_lon=78.0,
                    duration_hours=13,
                )
            )

        # Duration < 1 hour rejected
        with pytest.raises(UnsupportedDurationError):
            engine.execute(
                SimulationInput(
                    simulation_id="sim-invalid",
                    ignition_lat=30.0,
                    ignition_lon=78.0,
                    duration_hours=0,
                )
            )

        # Negative wind speed rejected
        with pytest.raises(InvalidEnvironmentalDataError):
            engine.execute(
                SimulationInput(
                    simulation_id="sim-invalid",
                    ignition_lat=30.0,
                    ignition_lon=78.0,
                    duration_hours=6,
                    environment=EnvironmentalConditions(wind_speed_ms=-5.0, wind_direction_deg=180.0),
                )
            )

        # Invalid grid resolution rejected
        with pytest.raises(GridValidationError):
            engine.execute(
                SimulationInput(
                    simulation_id="sim-invalid",
                    ignition_lat=30.0,
                    ignition_lon=78.0,
                    duration_hours=6,
                    grid_resolution_meters=-100,
                )
            )

    def test_wind_directional_spread_bias(self):
        """Strong wind from West (270°) must push fire predominantly towards East (90°)."""
        engine = SpreadSimulationEngine()
        sim_input = SpreadSimulationInput(
            simulation_id="sim-wind-bias",
            ignition=IgnitionPoint(lat=30.2, lon=78.7),
            duration_hours=4,
            grid_rows=35,
            grid_cols=35,
            wind=WindCondition(speed_ms=12.0, direction_deg=270.0),  # Strong wind blowing East
            deterministic=True,
        )

        result = engine.execute(sim_input)
        final_step = result.timesteps[-1]

        # Spread direction should be biased towards East (60° to 120°)
        assert 60.0 <= final_step.spread_direction_deg <= 120.0

    def test_cli_execution(self, tmp_path):
        """CLI invocation with geojson output writing."""
        from services.spread_engine.cli import main
        out_file = str(tmp_path / "test_sim.geojson")
        exit_code = main([
            "--lat", "30.2",
            "--lon", "78.7",
            "--duration", "3",
            "--rows", "25",
            "--cols", "25",
            "--wind-speed", "5.0",
            "--wind-dir", "180.0",
            "--output", out_file,
            "--format", "geojson",
        ])
        assert exit_code == 0
        import json
        with open(out_file, "r") as f:
            data = json.load(f)
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 3

