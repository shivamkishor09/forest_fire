"""Fire grid spatial data structures, raster management, and cell state representation."""

import math
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from ..models.enums import CellState, FuelClass
from ..physics.fuel import normalize_fuel_type, calculate_fuel_factor
from ..common.exceptions import IgnitionOutsideGridError, GridValidationError


class FireGrid:
    """
    2D spatial grid representation for fire propagation.
    Retains full Phase 1 contract compatibility.
    """

    def __init__(self, rows: int, cols: int, resolution_meters: int = 500):
        if rows <= 0 or cols <= 0:
            raise GridValidationError(f"Grid dimensions must be positive, got ({rows}, {cols})")
        self.rows = rows
        self.cols = cols
        self.resolution_meters = resolution_meters
        # Initialize all cells to UNBURNED
        self.matrix: List[List[CellState]] = [
            [CellState.UNBURNED for _ in range(cols)] for _ in range(rows)
        ]

    def set_cell_state(self, r: int, c: int, state: CellState) -> None:
        """Update the state of a specific cell coordinate."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self.matrix[r][c] = state

    def get_cell_state(self, r: int, c: int) -> CellState:
        """Query state of a cell."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.matrix[r][c]
        raise IndexError(f"Cell ({r}, {c}) is out of bounds for grid of size ({self.rows}, {self.cols})")

    def count_by_state(self) -> Dict[CellState, int]:
        """Aggregate count of cells by state."""
        counts = {
            CellState.UNBURNED: 0,
            CellState.BURNING: 0,
            CellState.BURNED: 0,
            CellState.NON_BURNABLE: 0,
        }
        for row in self.matrix:
            for cell in row:
                counts[cell] = counts.get(cell, 0) + 1
        return counts


class SimulationGrid:
    """
    High-performance NumPy-backed 2D spatial grid for Cellular Automata fire spread.
    Maintains synchronized state, burn timers, elevation, slope, aspect, and fuel rasters.
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        resolution_meters: float = 500.0,
        center_lat: float = 30.0,
        center_lon: float = 78.5,
        default_elevation_m: float = 1000.0,
        default_slope_deg: float = 0.0,
        default_aspect_deg: float = 180.0,
        default_fuel: str = FuelClass.BROADLEAF_MODERATE_LITTER.value,
    ):
        if rows <= 0 or cols <= 0:
            raise GridValidationError(f"Grid dimensions must be positive: rows={rows}, cols={cols}")
        if resolution_meters <= 0:
            raise GridValidationError(f"Grid resolution must be positive: {resolution_meters}")

        self.rows = rows
        self.cols = cols
        self.resolution_meters = float(resolution_meters)
        self.center_lat = float(center_lat)
        self.center_lon = float(center_lon)

        # Geographic bounds calculations
        self.meters_per_deg_lat = 111320.0
        cos_lat = math.cos(math.radians(self.center_lat))
        self.meters_per_deg_lon = 111320.0 * max(cos_lat, 0.0001)

        self.delta_lat = self.resolution_meters / self.meters_per_deg_lat
        self.delta_lon = self.resolution_meters / self.meters_per_deg_lon

        self.total_lat_span = self.rows * self.delta_lat
        self.total_lon_span = self.cols * self.delta_lon

        self.north_lat = self.center_lat + (self.total_lat_span / 2.0)
        self.south_lat = self.center_lat - (self.total_lat_span / 2.0)
        self.west_lon = self.center_lon - (self.total_lon_span / 2.0)
        self.east_lon = self.center_lon + (self.total_lon_span / 2.0)

        # NumPy rasters for vectorized computation
        self.state = np.full((rows, cols), CellState.UNBURNED.value, dtype=np.int8)
        self.burn_timer = np.zeros((rows, cols), dtype=np.int16)

        # Environmental layers
        self.elevation = np.full((rows, cols), default_elevation_m, dtype=np.float32)
        self.slope = np.full((rows, cols), default_slope_deg, dtype=np.float32)
        self.aspect = np.full((rows, cols), default_aspect_deg, dtype=np.float32)

        # Fuel representation: store canonical string per cell
        canonical_default_fuel = normalize_fuel_type(default_fuel)
        self.fuel = np.full((rows, cols), canonical_default_fuel, dtype=object)

        # Mark non-burnable cells initially based on default fuel
        if calculate_fuel_factor(canonical_default_fuel) <= 0.0:
            self.state[:] = CellState.NON_BURNABLE.value

    def set_cell_state(self, r: int, c: int, state: CellState) -> None:
        """Update state of cell at (r, c)."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self.state[r, c] = state.value
        else:
            raise IndexError(f"Cell ({r}, {c}) is out of bounds for ({self.rows}, {self.cols})")

    def get_cell_state(self, r: int, c: int) -> CellState:
        """Retrieve state of cell at (r, c)."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return CellState(self.state[r, c])
        raise IndexError(f"Cell ({r}, {c}) is out of bounds for ({self.rows}, {self.cols})")

    def count_by_state(self) -> Dict[CellState, int]:
        """Aggregate cell counts by discrete state."""
        counts = {
            CellState.UNBURNED: int(np.count_nonzero(self.state == CellState.UNBURNED.value)),
            CellState.BURNING: int(np.count_nonzero(self.state == CellState.BURNING.value)),
            CellState.BURNED: int(np.count_nonzero(self.state == CellState.BURNED.value)),
            CellState.NON_BURNABLE: int(np.count_nonzero(self.state == CellState.NON_BURNABLE.value)),
        }
        return counts

    def lat_lon_to_row_col(self, lat: float, lon: float) -> Tuple[int, int]:
        """
        Map a WGS 84 geographic coordinate (latitude, longitude) to (row, col) grid indices.
        Raises IgnitionOutsideGridError if coordinate is outside the grid bounds.
        """
        if lat > self.north_lat or lat < self.south_lat or lon < self.west_lon or lon > self.east_lon:
            raise IgnitionOutsideGridError(
                f"Coordinates ({lat}, {lon}) lie outside grid bounding box "
                f"[{self.south_lat:.4f}, {self.west_lon:.4f}, {self.north_lat:.4f}, {self.east_lon:.4f}]"
            )

        row = int(math.floor((self.north_lat - lat) / self.delta_lat))
        col = int(math.floor((lon - self.west_lon) / self.delta_lon))

        # Clamp edge cases exactly on the eastern or southern boundary
        row = min(self.rows - 1, max(0, row))
        col = min(self.cols - 1, max(0, col))
        return row, col

    def row_col_to_lat_lon(self, row: int, col: int) -> Tuple[float, float]:
        """Get the centroid (latitude, longitude) for a grid cell (row, col)."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError(f"Cell ({row}, {col}) is out of bounds for ({self.rows}, {self.cols})")

        lat = self.north_lat - (row + 0.5) * self.delta_lat
        lon = self.west_lon + (col + 0.5) * self.delta_lon
        return lat, lon

    def get_cell_bbox(self, row: int, col: int) -> Tuple[float, float, float, float]:
        """
        Return (west_lon, south_lat, east_lon, north_lat) bounding box for cell (row, col).
        """
        cell_north = self.north_lat - row * self.delta_lat
        cell_south = self.north_lat - (row + 1) * self.delta_lat
        cell_west = self.west_lon + col * self.delta_lon
        cell_east = self.west_lon + (col + 1) * self.delta_lon
        return cell_west, cell_south, cell_east, cell_north

    def ignite(self, row: int, col: int, burning_steps: int = 3) -> None:
        """Ignite a combustible cell at (row, col)."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError(f"Ignition coordinate ({row}, {col}) out of grid bounds")

        if self.state[row, col] == CellState.NON_BURNABLE.value:
            raise GridValidationError(f"Cannot ignite non-burnable cell at ({row}, {col})")

        self.state[row, col] = CellState.BURNING.value
        self.burn_timer[row, col] = burning_steps

    def to_legacy_fire_grid(self) -> FireGrid:
        """Convert to legacy FireGrid for backward compatibility."""
        fg = FireGrid(rows=self.rows, cols=self.cols, resolution_meters=int(self.resolution_meters))
        for r in range(self.rows):
            for c in range(self.cols):
                fg.matrix[r][c] = CellState(self.state[r, c])
        return fg
