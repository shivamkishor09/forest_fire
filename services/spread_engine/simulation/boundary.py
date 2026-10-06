"""Spatial boundary extraction and GeoJSON polygon generation."""

from typing import Any, Dict, List, Tuple
import numpy as np
import shapely
from shapely.geometry import box, Polygon, MultiPolygon

from ..models.enums import CellState
from .grid import SimulationGrid
from ..common.exceptions import BoundaryExtractionError


def _tuple_to_list_coords(coords: Any, precision: int = 6) -> Any:
    """Recursively convert nested coordinate tuples to lists with rounded precision."""
    if isinstance(coords, (tuple, list)):
        if len(coords) == 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
            return [round(float(coords[0]), precision), round(float(coords[1]), precision)]
        return [_tuple_to_list_coords(item, precision) for item in coords]
    return coords


def extract_fire_boundary_geojson(
    grid: SimulationGrid,
    precision: int = 6,
) -> Dict[str, Any]:
    """
    Generate GeoJSON Polygon or MultiPolygon representing the outer boundary
    perimeter of all actively BURNING and BURNED cells.

    Uses shapely union to dissolve internal cell borders into a continuous exterior boundary.
    """
    burned_mask = (grid.state == CellState.BURNING.value) | (grid.state == CellState.BURNED.value)
    cell_indices = np.argwhere(burned_mask)

    if len(cell_indices) == 0:
        # Fallback empty or point box around center
        w, s, e, n = grid.get_cell_bbox(grid.rows // 2, grid.cols // 2)
        return {
            "type": "Polygon",
            "coordinates": [
                [
                    [round(w, precision), round(s, precision)],
                    [round(e, precision), round(s, precision)],
                    [round(e, precision), round(n, precision)],
                    [round(w, precision), round(n, precision)],
                    [round(w, precision), round(s, precision)],
                ]
            ],
        }

    # Construct individual cell bounding box polygons
    cell_polygons: List[Polygon] = []
    for r, c in cell_indices:
        w, s, e, n = grid.get_cell_bbox(r, c)
        cell_polygons.append(box(w, s, e, n))

    try:
        # Dissolve into single unified geometry
        if len(cell_polygons) == 1:
            union_geom = cell_polygons[0]
        else:
            union_geom = shapely.unary_union(cell_polygons)

        # Simplify very slightly to remove floating point collinear artifacts while retaining exact boundary
        clean_geom = union_geom.simplify(tolerance=1e-7, preserve_topology=True)

        if isinstance(clean_geom, Polygon):
            coords = [list(clean_geom.exterior.coords)]
            for interior in clean_geom.interiors:
                coords.append(list(interior.coords))
            return {
                "type": "Polygon",
                "coordinates": _tuple_to_list_coords(coords, precision),
            }
        elif isinstance(clean_geom, MultiPolygon):
            all_poly_coords = []
            for poly in clean_geom.geoms:
                coords = [list(poly.exterior.coords)]
                for interior in poly.interiors:
                    coords.append(list(interior.coords))
                all_poly_coords.append(coords)
            return {
                "type": "MultiPolygon",
                "coordinates": _tuple_to_list_coords(all_poly_coords, precision),
            }
        else:
            # Fallback to convex hull if geometry collection returned
            hull = clean_geom.convex_hull
            coords = [list(hull.exterior.coords)]
            return {
                "type": "Polygon",
                "coordinates": _tuple_to_list_coords(coords, precision),
            }

    except Exception as exc:
        raise BoundaryExtractionError(f"Failed to extract fire boundary polygon: {str(exc)}") from exc
