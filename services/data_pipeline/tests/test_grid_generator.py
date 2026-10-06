"""Unit tests for 500m grid generation and spatial indexing."""

import pytest
from services.data_pipeline.adapters.base import BoundingBox
from services.data_pipeline.grid.generator import GridGenerator
from services.data_pipeline.grid.indexing import SpatialGridIndex, haversine_distance_meters
from services.data_pipeline.preprocessing.projection import CrsManager


def test_utm_crs_discovery():
    # Uttarakhand, India (~78.7°E, 30.2°N) is in UTM Zone 44N -> EPSG:32644
    epsg = CrsManager.get_utm_epsg_for_lon_lat(78.7, 30.2)
    assert epsg == "EPSG:32644"

    # Kerala, India (~76.5°E, 10.0°N) is in UTM Zone 43N -> EPSG:32643
    epsg_kerala = CrsManager.get_utm_epsg_for_lon_lat(76.5, 10.0)
    assert epsg_kerala == "EPSG:32643"


def test_grid_generation_500m():
    # Small test box: ~2km x 2km
    bbox = BoundingBox(min_lon=78.70, min_lat=30.20, max_lon=78.72, max_lat=30.22)
    generator = GridGenerator(resolution_meters=500)
    cells = generator.generate_grid_for_bbox(bbox, region_id="test_reg")

    assert len(cells) > 0
    first_cell = cells[0]
    assert first_cell.resolution_meters == 500
    assert first_cell.cell_id.startswith("test_reg_CELL_")
    assert first_cell.geometry["type"] == "Polygon"
    assert len(first_cell.geometry["coordinates"][0]) == 5  # Closed ring

    # Verify GeoDataFrame conversion
    gdf = generator.cells_to_geodataframe(cells)
    assert len(gdf) == len(cells)
    assert gdf.crs.to_string() == "EPSG:4326"


def test_spatial_indexing_and_point_lookup():
    bbox = BoundingBox(min_lon=78.70, min_lat=30.20, max_lon=78.72, max_lat=30.22)
    generator = GridGenerator(resolution_meters=500)
    cells = generator.generate_grid_for_bbox(bbox, region_id="test_reg")
    index = SpatialGridIndex(cells)

    # Pick centroid of first cell
    c = cells[0]
    found = index.find_cell_for_point(c.centroid_lat, c.centroid_lon)
    assert found is not None
    assert found.cell_id == c.cell_id

    # Nearest point distance calculation
    d = haversine_distance_meters(30.0, 78.0, 30.0, 78.01)
    assert 900.0 < d < 1100.0  # Approx 1 km
