"""Unit tests for SimulationGrid and geographic indexing."""

import pytest
import numpy as np
from services.spread_engine.simulation.grid import SimulationGrid, FireGrid
from services.spread_engine.models.enums import CellState, FuelClass
from services.spread_engine.common.exceptions import IgnitionOutsideGridError, GridValidationError


class TestSimulationGrid:
    """Verify grid initialization, spatial bounds, and coordinate transformations."""

    def test_grid_initialization(self):
        grid = SimulationGrid(
            rows=20,
            cols=20,
            resolution_meters=500.0,
            center_lat=30.0,
            center_lon=78.0,
        )
        assert grid.rows == 20
        assert grid.cols == 20
        assert grid.resolution_meters == 500.0
        assert grid.state.shape == (20, 20)
        assert np.all(grid.state == CellState.UNBURNED.value)

    def test_coordinate_mapping_center_cell(self):
        """Center coordinate must map to central grid row and col."""
        grid = SimulationGrid(
            rows=20,
            cols=20,
            resolution_meters=500.0,
            center_lat=30.0,
            center_lon=78.0,
        )
        row, col = grid.lat_lon_to_row_col(30.0, 78.0)
        assert row in (9, 10)
        assert col in (9, 10)

        # Reverse transformation must return coordinates close to 30.0, 78.0
        lat, lon = grid.row_col_to_lat_lon(row, col)
        assert abs(lat - 30.0) < 0.01
        assert abs(lon - 78.0) < 0.01

    def test_out_of_bounds_ignition_raises_error(self):
        """Coordinates clearly outside the grid bounding box must raise IgnitionOutsideGridError."""
        grid = SimulationGrid(
            rows=10,
            cols=10,
            resolution_meters=500.0,
            center_lat=30.0,
            center_lon=78.0,
        )
        with pytest.raises(IgnitionOutsideGridError):
            grid.lat_lon_to_row_col(35.0, 85.0)

    def test_cell_bounding_box(self):
        """Cell bounding box should define a valid rectangle in WGS 84 coordinates."""
        grid = SimulationGrid(rows=10, cols=10, resolution_meters=500.0, center_lat=30.0, center_lon=78.0)
        west, south, east, north = grid.get_cell_bbox(5, 5)
        assert west < east
        assert south < north

    def test_ignition_and_burn_timer(self):
        grid = SimulationGrid(rows=10, cols=10)
        grid.ignite(5, 5, burning_steps=3)
        assert grid.get_cell_state(5, 5) == CellState.BURNING
        assert grid.burn_timer[5, 5] == 3

    def test_non_burnable_ignition_rejection(self):
        """Igniting a non-burnable cell must raise GridValidationError."""
        grid = SimulationGrid(rows=10, cols=10, default_fuel="NON_BURNABLE_WATER")
        with pytest.raises(GridValidationError):
            grid.ignite(5, 5)

    def test_legacy_fire_grid_conversion(self):
        grid = SimulationGrid(rows=8, cols=8)
        grid.ignite(4, 4)
        fg = grid.to_legacy_fire_grid()
        assert isinstance(fg, FireGrid)
        assert fg.get_cell_state(4, 4) == CellState.BURNING
        assert fg.get_cell_state(0, 0) == CellState.UNBURNED
