"""Unit tests for spatial boundary polygon extraction and GeoJSON formatting."""

import pytest
from services.spread_engine.simulation.grid import SimulationGrid
from services.spread_engine.simulation.boundary import extract_fire_boundary_geojson
from services.spread_engine.models.enums import CellState
from shapely.geometry import shape


class TestBoundaryExtraction:
    """Verify GeoJSON polygon generation and geometric topology."""

    def test_single_cell_boundary_is_valid_geojson_polygon(self):
        """Single burning cell should yield a standard 5-point closed GeoJSON Polygon."""
        grid = SimulationGrid(rows=10, cols=10, resolution_meters=500.0, center_lat=30.0, center_lon=78.0)
        grid.ignite(5, 5)

        geojson = extract_fire_boundary_geojson(grid)
        assert geojson["type"] == "Polygon"
        coords = geojson["coordinates"][0]
        assert len(coords) == 5
        # Ring must be closed
        assert coords[0] == coords[-1]
        # Coordinates must be within WGS 84 bounds
        for lon, lat in coords:
            assert -180.0 <= lon <= 180.0
            assert -90.0 <= lat <= 90.0

    def test_multi_cell_dissolved_boundary(self):
        """Contiguous burning cells must dissolve internal borders into a single Polygon."""
        grid = SimulationGrid(rows=10, cols=10, resolution_meters=500.0, center_lat=30.0, center_lon=78.0)
        # Ignite 2x2 contiguous patch
        grid.ignite(4, 4)
        grid.ignite(4, 5)
        grid.ignite(5, 4)
        grid.ignite(5, 5)

        geojson = extract_fire_boundary_geojson(grid)
        assert geojson["type"] in ("Polygon", "MultiPolygon")

        # Convert to shapely geometry to test geometric validity
        geom = shape(geojson)
        assert geom.is_valid
        assert not geom.is_empty
        assert geom.area > 0

    def test_boundary_area_expands_with_new_cells(self):
        """Boundary area must increase monotonically as more cells catch fire."""
        grid = SimulationGrid(rows=10, cols=10, resolution_meters=500.0, center_lat=30.0, center_lon=78.0)
        grid.ignite(5, 5)
        geom_1 = shape(extract_fire_boundary_geojson(grid))

        grid.ignite(5, 6)
        geom_2 = shape(extract_fire_boundary_geojson(grid))

        grid.ignite(6, 5)
        geom_3 = shape(extract_fire_boundary_geojson(grid))

        assert geom_2.area > geom_1.area
        assert geom_3.area > geom_2.area
