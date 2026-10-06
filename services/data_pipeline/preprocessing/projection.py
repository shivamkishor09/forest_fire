"""Coordinate Reference System (CRS) management, UTM zone discovery, and reprojection."""

import math
from typing import Any, Dict, List, Tuple
from pyproj import CRS, Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform

from ..common.types import BoundingBox


class CrsManager:
    """Manages spatial reference systems, metric projections, and coordinate transformations."""

    CANONICAL_CRS = "EPSG:4326"  # WGS 84 geographic 2D
    WEB_MERCATOR_CRS = "EPSG:3857"

    @staticmethod
    def get_utm_epsg_for_lon_lat(longitude: float, latitude: float) -> str:
        """
        Determine the appropriate WGS 84 UTM EPSG code for a given longitude and latitude.
        Formula: zone = floor((lon + 180) / 6) + 1. Northern hemisphere is EPSG:326xx, Southern is EPSG:327xx.
        """
        zone = int(math.floor((longitude + 180.0) / 6.0)) + 1
        zone = min(max(zone, 1), 60)
        epsg_code = 32600 + zone if latitude >= 0 else 32700 + zone
        return f"EPSG:{epsg_code}"

    @classmethod
    def get_transformer(cls, source_crs: str, target_crs: str) -> Transformer:
        """Create a thread-safe pyproj Transformer with always_xy=True (lon, lat / x, y)."""
        src = CRS.from_user_input(source_crs)
        dst = CRS.from_user_input(target_crs)
        return Transformer.from_crs(src, dst, always_xy=True)

    @classmethod
    def transform_point(
        cls,
        x: float,
        y: float,
        source_crs: str,
        target_crs: str
    ) -> Tuple[float, float]:
        """Transform a single coordinate pair (x/lon, y/lat) between CRSs."""
        if source_crs == target_crs:
            return x, y
        transformer = cls.get_transformer(source_crs, target_crs)
        tx, ty = transformer.transform(x, y)
        return tx, ty

    @classmethod
    def transform_geometry(
        cls,
        geojson_geom: Dict[str, Any],
        source_crs: str,
        target_crs: str
    ) -> Dict[str, Any]:
        """Transform a GeoJSON geometry dictionary between CRSs."""
        if source_crs == target_crs:
            return geojson_geom

        transformer = cls.get_transformer(source_crs, target_crs)
        shapely_geom = shape(geojson_geom)
        transformed_geom = transform(transformer.transform, shapely_geom)
        return mapping(transformed_geom)

    @classmethod
    def transform_bbox(
        cls,
        bbox: BoundingBox,
        source_crs: str,
        target_crs: str
    ) -> Tuple[float, float, float, float]:
        """
        Transform a BoundingBox (min_lon, min_lat, max_lon, max_lat) to target CRS extent
        (min_x, min_y, max_x, max_y).
        """
        transformer = cls.get_transformer(source_crs, target_crs)
        xs = [bbox.min_lon, bbox.max_lon, bbox.min_lon, bbox.max_lon]
        ys = [bbox.min_lat, bbox.min_lat, bbox.max_lat, bbox.max_lat]
        tx, ty = transformer.transform(xs, ys)
        return min(tx), min(ty), max(tx), max(ty)
