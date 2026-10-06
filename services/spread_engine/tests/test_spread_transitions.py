"""Unit tests for Cellular Automata transition rules and double-buffering."""

import pytest
import numpy as np
from services.spread_engine.simulation.grid import SimulationGrid
from services.spread_engine.simulation.state import GridStateBuffer
from services.spread_engine.simulation.transitions import TransitionEvaluator
from services.spread_engine.calibration.parameters import SimulationParameters
from services.spread_engine.models.enums import CellState, FuelClass


class TestTransitions:
    """Verify state transitions, double-buffering, and burn-out dynamics."""

    def test_burn_timer_decrements_to_burned(self):
        """Active BURNING cell must decrement timer and become BURNED once timer expires."""
        grid = SimulationGrid(rows=5, cols=5)
        # Ignite center cell with timer of 2 steps
        grid.ignite(2, 2, burning_steps=2)

        buffer = GridStateBuffer.from_grid(grid.state, grid.burn_timer)
        # Disable spread to observe only burnout
        params = SimulationParameters(base_spread_probability=0.0)
        evaluator = TransitionEvaluator(parameters=params, deterministic=True)

        # Step 1: Timer 2 -> 1, remains BURNING
        evaluator.step(grid, buffer)
        assert grid.get_cell_state(2, 2) == CellState.BURNING
        assert grid.burn_timer[2, 2] == 1

        # Step 2: Timer 1 -> 0, transitions to BURNED
        evaluator.step(grid, buffer)
        assert grid.get_cell_state(2, 2) == CellState.BURNED
        assert grid.burn_timer[2, 2] == 0

    def test_double_buffered_simultaneous_updates(self):
        """Transitions within a step must be evaluated from current buffer, not intermediate state."""
        grid = SimulationGrid(rows=7, cols=7)
        grid.ignite(3, 3, burning_steps=5)
        buffer = GridStateBuffer.from_grid(grid.state, grid.burn_timer)

        evaluator = TransitionEvaluator(deterministic=True)
        # Before step: only center cell is BURNING
        assert grid.count_by_state()[CellState.BURNING] == 1

        # One step should only ignite immediate 8-neighbours (distance 1), not distance 2
        evaluator.step(grid, buffer)
        assert grid.get_cell_state(3, 3) == CellState.BURNING
        # Corner cells at (0, 0) or (6, 6) must remain UNBURNED
        assert grid.get_cell_state(0, 0) == CellState.UNBURNED
        assert grid.get_cell_state(6, 6) == CellState.UNBURNED

    def test_non_burnable_cells_never_ignite(self):
        """Water and barren cells must remain unburned even when adjacent to active fires."""
        grid = SimulationGrid(rows=5, cols=5)
        grid.ignite(2, 2, burning_steps=5)
        # Place water barrier at (2, 3)
        grid.fuel[2, 3] = FuelClass.NON_BURNABLE_WATER.value
        grid.set_cell_state(2, 3, CellState.NON_BURNABLE)

        buffer = GridStateBuffer.from_grid(grid.state, grid.burn_timer)
        evaluator = TransitionEvaluator(deterministic=True)

        # Run several steps
        for _ in range(3):
            evaluator.step(grid, buffer, wind_speed_ms=10.0, wind_dir_deg=270.0)

        # Water cell must strictly remain NON_BURNABLE
        assert grid.get_cell_state(2, 3) == CellState.NON_BURNABLE

    def test_burned_cells_never_reignite(self):
        """A BURNED cell can never return to BURNING."""
        grid = SimulationGrid(rows=5, cols=5)
        grid.set_cell_state(2, 2, CellState.BURNED)
        # Place burning cell next to it
        grid.ignite(2, 1, burning_steps=5)

        buffer = GridStateBuffer.from_grid(grid.state, grid.burn_timer)
        evaluator = TransitionEvaluator(deterministic=True)
        evaluator.step(grid, buffer)

        assert grid.get_cell_state(2, 2) == CellState.BURNED

    def test_deterministic_consistency(self):
        """Running the same initial condition twice in deterministic mode must yield identical state."""
        def run_sim():
            grid = SimulationGrid(rows=9, cols=9)
            grid.ignite(4, 4, burning_steps=4)
            buffer = GridStateBuffer.from_grid(grid.state, grid.burn_timer)
            evaluator = TransitionEvaluator(deterministic=True)
            for _ in range(4):
                evaluator.step(grid, buffer, wind_speed_ms=8.0, wind_dir_deg=180.0)
            return grid.state.copy()

        state_1 = run_sim()
        state_2 = run_sim()
        assert np.array_equal(state_1, state_2)
