"""Unit tests for simulation metrics: area, velocity, direction, and intensity."""

import pytest
from services.spread_engine.simulation.grid import SimulationGrid
from services.spread_engine.simulation.metrics import (
    calculate_burned_area_ha,
    calculate_active_burning_cells,
    calculate_spread_velocity_kmh,
    calculate_dominant_spread_direction_deg,
    calculate_fire_intensity_mw,
)
from services.spread_engine.models.enums import CellState


class TestSimulationMetrics:
    """Verify metrics calculation logic."""

    def test_burned_area_calculation(self):
        """At 500m resolution, each cell is (500x500)/10000 = 25 hectares."""
        grid = SimulationGrid(rows=10, cols=10, resolution_meters=500.0)
        assert calculate_burned_area_ha(grid) == 0.0

        grid.ignite(5, 5)
        assert calculate_burned_area_ha(grid) == 25.0

        grid.ignite(5, 6)
        grid.set_cell_state(4, 5, CellState.BURNED)
        # 2 burning + 1 burned = 3 cells * 25ha = 75ha
        assert calculate_burned_area_ha(grid) == 75.0

    def test_active_burning_count(self):
        grid = SimulationGrid(rows=10, cols=10)
        grid.ignite(5, 5)
        grid.ignite(5, 6)
        grid.set_cell_state(5, 4, CellState.BURNED)
        assert calculate_active_burning_cells(grid) == 2

    def test_dominant_spread_direction(self):
        """Verify vector heading matches directional expansion."""
        grid = SimulationGrid(rows=11, cols=11)
        center_r, center_c = 5, 5
        grid.ignite(center_r, center_c)

        # Fire expands East (same row, higher column)
        grid.ignite(5, 6)
        grid.ignite(5, 7)
        east_heading = calculate_dominant_spread_direction_deg(grid, center_r, center_c)
        assert 80.0 <= east_heading <= 100.0  # Approx 90°

        # Reset and expand North (lower row, same column)
        grid_north = SimulationGrid(rows=11, cols=11)
        grid_north.ignite(center_r, center_c)
        grid_north.ignite(4, 5)
        grid_north.ignite(3, 5)
        north_heading = calculate_dominant_spread_direction_deg(grid_north, center_r, center_c)
        assert north_heading == 0.0 or north_heading >= 350.0  # Approx 0°/360°

        # Expand South (higher row, same column)
        grid_south = SimulationGrid(rows=11, cols=11)
        grid_south.ignite(center_r, center_c)
        grid_south.ignite(6, 5)
        grid_south.ignite(7, 5)
        south_heading = calculate_dominant_spread_direction_deg(grid_south, center_r, center_c)
        assert 170.0 <= south_heading <= 190.0  # Approx 180°

    def test_spread_velocity(self):
        grid = SimulationGrid(rows=20, cols=20, resolution_meters=500.0)
        grid.ignite(10, 10)
        # Advance 4 cells (2.0 km) away
        grid.ignite(10, 14)
        velocity_1h = calculate_spread_velocity_kmh(grid, 10, 10, elapsed_hours=1.0)
        assert velocity_1h == 2.0  # 4 * 0.5km / 1h = 2.0 km/h

        velocity_2h = calculate_spread_velocity_kmh(grid, 10, 10, elapsed_hours=2.0)
        assert velocity_2h == 1.0  # 2.0 km / 2h = 1.0 km/h

    def test_fire_intensity_scaling(self):
        i_low = calculate_fire_intensity_mw(active_burning_count=1, wind_speed_ms=2.0)
        i_high = calculate_fire_intensity_mw(active_burning_count=10, wind_speed_ms=12.0)
        assert i_high > i_low
        assert i_low > 0
