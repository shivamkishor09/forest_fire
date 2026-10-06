"""500m x 500m regular spatial grid generator."""

import math
from typing import Any, Dict, List, Optional, Tuple
import geopandas as gpd
from shapely.geometry import box, shape, Polygon, Point
from shapely.ops import transform

from ..common.types import BoundingBox, GridCellDefinition
from ..preprocessing.projection import CrsManager


class GridGenerator:
    """Generates deterministic regular 500m x 500m grid cells partitioned over a geographic extent."""

    def __init__(self, resolution_meters: int = 500):
        self.resolution_meters = resolution_meters

    def generate_grid_for_bbox(
        self,
        bbox: BoundingBox,
        region_id: str = "region_default",
        region_polygon: Optional[Dict[str, Any]] = None,
    ) -> List[GridCellDefinition]:
        """
        Generate 500m x 500m cells partitioning the bounding box.
        Uses the local UTM metric coordinate system to enforce true 500.0m metric squares.
        """
        center_lon = (bbox.min_lon + bbox.max_lon) / 2.0
        center_lat = (bbox.min_lat + bbox.max_lat) / 2.0
        utm_crs = CrsManager.get_utm_epsg_for_lon_lat(center_lon, center_lat)

        # Reproject bbox to UTM
        min_x, min_y, max_x, max_y = CrsManager.transform_bbox(
            bbox,
            source_crs=CrsManager.CANONICAL_CRS,
            target_crs=utm_crs,
        )

        res = float(self.resolution_meters)
        # Snap origins to round multiples of resolution
        start_x = math.floor(min_x / res) * res
        end_x = math.ceil(max_x / res) * res
        start_y = math.floor(min_y / res) * res
        end_y = math.ceil(max_y / res) * res

        cols = int(round((end_x - start_x) / res))
        rows = int(round((end_y - start_y) / res))

        to_wgs84 = CrsManager.get_transformer(utm_crs, CrsManager.CANONICAL_CRS)

        shapely_region = shape(region_polygon) if region_polygon else None

        cells: List[GridCellDefinition] = []

        for r in range(rows):
            cell_min_y = start_y + r * res
            cell_max_y = cell_min_y + res

            for c in range(cols):
                cell_min_x = start_x + c * res
                cell_max_x = cell_min_x + res

                # Cell centroid in UTM
                center_utm_x = (cell_min_x + cell_max_x) / 2.0
                center_utm_y = (cell_min_y + cell_max_y) / 2.0

                # Centroid in WGS 84
                c_lon, c_lat = to_wgs84.transform(center_utm_x, center_utm_y)

                # Check if centroid is within region boundary if specified
                if shapely_region is not None:
                    pt = Point(c_lon, c_lat)
                    if not shapely_region.contains(pt) and not shapely_region.touches(pt):
                        continue

                # Cell polygon in UTM transformed to WGS 84
                utm_poly = box(cell_min_x, cell_min_y, cell_max_x, cell_max_y)
                wgs84_poly = transform(to_wgs84.transform, utm_poly)

                # Round coordinates for clean serialization
                coords = [
                    [round(lon, 6), round(lat, 6)]
                    for lon, lat in wgs84_poly.exterior.coords
                ]

                cell_code = f"CELL_{r:04d}_{c:04d}"
                cell_id = f"{region_id}_{cell_code}"

                cells.append(
                    GridCellDefinition(
                        cell_id=cell_id,
                        region_id=region_id,
                        cell_code=cell_code,
                        centroid_lat=round(c_lat, 6),
                        centroid_lon=round(c_lon, 6),
                        geometry={
                            "type": "Polygon",
                            "coordinates": [coords],
                        },
                        resolution_meters=self.resolution_meters,
                        row_idx=r,
                        col_idx=c,
                    )
                )

        return cells

    def cells_to_geodataframe(self, cells: List[GridCellDefinition]) -> gpd.GeoDataFrame:
        """Convert a list of GridCellDefinitions into a GeoPandas GeoDataFrame."""
        data = []
        geometries = []
        for cell in cells:
            data.append({
                "cell_id": cell.cell_id,
                "region_id": cell.region_id,
                "cell_code": cell.cell_code,
                "centroid_lat": cell.centroid_lat,
                "centroid_lon": cell.centroid_lon,
                "resolution_meters": cell.resolution_meters,
                "row_idx": cell.row_idx,
                "col_idx": cell.col_idx,
            })
            geometries.append(shape(cell.geometry))

        gdf = gpd.GeoDataFrame(data, geometry=geometries, crs=CrsManager.CANONICAL_CRS)
        return gdf
