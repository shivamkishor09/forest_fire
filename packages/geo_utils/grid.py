"""Geospatial utilities for 500m grid partitioning and geometry operations."""

import math
from typing import Any, Dict, List, Tuple


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the great-circle distance between two points in meters."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def create_500m_cell_polygon(center_lat: float, center_lon: float, resolution_meters: float = 500.0) -> Dict[str, Any]:
    """
    Generate a square bounding polygon approximating resolution_meters x resolution_meters
    around a center point in WGS 84 (EPSG:4326).
    """
    meters_per_deg_lat = 111320.0
    delta_lat = (resolution_meters / 2.0) / meters_per_deg_lat

    cos_lat = math.cos(math.radians(center_lat))
    meters_per_deg_lon = 111320.0 * max(cos_lat, 0.0001)
    delta_lon = (resolution_meters / 2.0) / meters_per_deg_lon

    min_lat = center_lat - delta_lat
    max_lat = center_lat + delta_lat
    min_lon = center_lon - delta_lon
    max_lon = center_lon + delta_lon

    return {
        "type": "Polygon",
        "coordinates": [
            [
                [round(min_lon, 6), round(min_lat, 6)],
                [round(max_lon, 6), round(min_lat, 6)],
                [round(max_lon, 6), round(max_lat, 6)],
                [round(min_lon, 6), round(max_lat, 6)],
                [round(min_lon, 6), round(min_lat, 6)],
            ]
        ]
    }


def validate_wgs84_coordinates(latitude: float, longitude: float) -> bool:
    """Validate latitude [-90, 90] and longitude [-180, 180]."""
    return (-90.0 <= latitude <= 90.0) and (-180.0 <= longitude <= 180.0)
