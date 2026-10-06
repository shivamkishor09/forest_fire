"""Unit tests for Spread Engine simulation runner."""

from services.spread_engine.models.config import SimulationInput, EnvironmentalConditions
from services.spread_engine.simulation.runner import CellularAutomataRunner


def test_simulation_runner_execution():
    """Verify CellularAutomataRunner generates standard 12-hour timesteps."""
    runner = CellularAutomataRunner()
    env = EnvironmentalConditions(wind_speed_ms=6.0, wind_direction_deg=180.0)
    sim_input = SimulationInput(
        simulation_id="sim-run-12h",
        ignition_lat=30.22,
        ignition_lon=78.78,
        duration_hours=12,
        environment=env
    )

    result = runner.run_simulation(sim_input)
    assert result.simulation_id == "sim-run-12h"
    assert result.duration_hours == 12
    assert len(result.timesteps) == 12

    # Verify first and last timestep properties
    first_step = result.timesteps[0]
    assert first_step.step_hour == 1
    assert first_step.burned_area_ha > 0
    assert first_step.boundary_polygon["type"] == "Polygon"

    last_step = result.timesteps[11]
    assert last_step.step_hour == 12
    assert last_step.burned_area_ha > first_step.burned_area_ha
