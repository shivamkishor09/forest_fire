"""Slope influence factor calculations for terrain-driven fire propagation."""

import math
from .wind import calculate_circular_angle_diff


def calculate_slope_factor(
    slope_deg: float,
    aspect_deg: float,
    propagation_angle_deg: float,
    uphill_coefficient: float = 2.0,
    downhill_coefficient: float = 1.0,
    max_factor: float = 5.0,
    min_factor: float = 0.1,
) -> float:
    """
    Calculate directional terrain slope factor based on local slope angle and aspect.

    Aspect convention:
    - aspect_deg is the azimuth direction that the slope faces DOWNHILL (0=N, 90=E, 180=S, 270=W).
    - The steepest uphill direction is (aspect_deg + 180.0) % 360.
    - propagation_angle_deg is the compass direction of fire movement.

    Returns:
    - K_s: scalar factor (1.0 = flat ground, > 1.0 = uphill acceleration, < 1.0 = downhill retardation).
    """
    if slope_deg <= 0.0:
        return 1.0

    # Compass bearing pointing directly uphill
    uphill_bearing_deg = (aspect_deg + 180.0) % 360.0

    # Directional component of slope in propagation direction
    angle_diff = calculate_circular_angle_diff(propagation_angle_deg, uphill_bearing_deg)
    directional_cosine = math.cos(math.radians(angle_diff))

    effective_slope_deg = slope_deg * directional_cosine
    # Cap effective slope to prevent physical singularities (>60° cliffs)
    clamped_slope = max(-60.0, min(60.0, effective_slope_deg))
    tan_slope = math.tan(math.radians(clamped_slope))

    if tan_slope >= 0.0:
        ks = math.exp(uphill_coefficient * tan_slope)
    else:
        ks = math.exp(-downhill_coefficient * abs(tan_slope))

    return float(max(min_factor, min(max_factor, ks)))


def calculate_elevation_slope_factor(
    elevation_diff_m: float,
    distance_m: float,
    uphill_coefficient: float = 2.0,
    downhill_coefficient: float = 1.0,
    max_factor: float = 5.0,
    min_factor: float = 0.1,
) -> float:
    """
    Calculate slope factor directly from elevation difference between cell centers.
    - elevation_diff_m: target_elevation - source_elevation (positive = uphill).
    - distance_m: horizontal distance between cell centers (e.g. 500m or 707.1m).
    """
    if distance_m <= 0.0 or elevation_diff_m == 0.0:
        return 1.0

    tan_slope = elevation_diff_m / distance_m
    # Limit slope ratio to tan(60 deg) ~= 1.732
    clamped_tan = max(-1.732, min(1.732, tan_slope))

    if clamped_tan >= 0.0:
        ks = math.exp(uphill_coefficient * clamped_tan)
    else:
        ks = math.exp(-downhill_coefficient * abs(clamped_tan))

    return float(max(min_factor, min(max_factor, ks)))
