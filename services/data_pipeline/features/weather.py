"""Meteorological feature engineering: unit conversions, wind vector decomposition."""

import math
from typing import Optional, Tuple


def kelvin_to_celsius(temp_k: Optional[float]) -> Optional[float]:
    """Convert absolute temperature in Kelvin to Celsius."""
    if temp_k is None:
        return None
    return round(temp_k - 273.15, 2)


def compute_wind_vector_components(
    wind_speed_ms: Optional[float],
    wind_direction_deg: Optional[float]
) -> Tuple[Optional[float], Optional[float]]:
    """
    Decompose wind speed and azimuth into meteorological zonal (u) and meridional (v) components.
    Convention: Direction is the compass heading FROM which the wind is blowing (0°=North, 90°=East).
    u = -speed * sin(dir)
    v = -speed * cos(dir)
    """
    if wind_speed_ms is None or wind_direction_deg is None:
        return None, None

    rad = math.radians(wind_direction_deg)
    u = -wind_speed_ms * math.sin(rad)
    v = -wind_speed_ms * math.cos(rad)
    return round(u, 3), round(v, 3)


def compute_wind_speed_and_direction(
    u_wind_ms: Optional[float],
    v_wind_ms: Optional[float]
) -> Tuple[Optional[float], Optional[float]]:
    """
    Reconstruct wind speed (m/s) and meteorological direction (degrees) from u and v components.
    """
    if u_wind_ms is None or v_wind_ms is None:
        return None, None

    speed = math.sqrt(u_wind_ms ** 2 + v_wind_ms ** 2)
    direction = (math.degrees(math.atan2(-u_wind_ms, -v_wind_ms)) + 360.0) % 360.0
    return round(speed, 2), round(direction, 1)
