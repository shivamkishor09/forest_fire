"""Unit tests for Spread Engine models and grid state contracts."""

from services.spread_engine.simulation.grid import FireGrid, CellState
from services.spread_engine.models.config import SimulationInput, EnvironmentalConditions


def test_fire_grid_initialization_and_states():
    """Verify FireGrid initial states and state transitions."""
    grid = FireGrid(rows=10, cols=10, resolution_meters=500)
    assert grid.rows == 10
    assert grid.cols == 10
    assert grid.resolution_meters == 500

    # Initial state should be UNBURNED
    assert grid.get_cell_state(5, 5) == CellState.UNBURNED

    # Update state
    grid.set_cell_state(5, 5, CellState.BURNING)
    assert grid.get_cell_state(5, 5) == CellState.BURNING

    grid.set_cell_state(5, 5, CellState.BURNED)
    assert grid.get_cell_state(5, 5) == CellState.BURNED

    counts = grid.count_by_state()
    assert counts[CellState.BURNED] == 1
    assert counts[CellState.UNBURNED] == 99


def test_simulation_input_contract():
    """Verify SimulationInput construction with environmental conditions."""
    env = EnvironmentalConditions(wind_speed_ms=7.5, wind_direction_deg=225.0)
    sim_input = SimulationInput(
        simulation_id="sim-test-01",
        ignition_lat=30.2,
        ignition_lon=78.7,
        duration_hours=12,
        environment=env
    )
    assert sim_input.simulation_id == "sim-test-01"
    assert sim_input.duration_hours == 12
    assert sim_input.environment.wind_speed_ms == 7.5
