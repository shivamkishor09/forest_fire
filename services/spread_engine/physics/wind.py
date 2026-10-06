"""Wind influence factor calculations for Cellular Automata fire spread."""

import math


def calculate_circular_angle_diff(angle_1_deg: float, angle_2_deg: float) -> float:
    """
    Calculate the minimal signed angular difference between two compass bearings in degrees.
    Returns value in range [-180.0, 180.0].
    Correctly handles circular boundary conditions (e.g. 359° vs 1° yields +2°).
    """
    diff = ((angle_1_deg - angle_2_deg + 180.0) % 360.0) - 180.0
    return diff


def calculate_wind_factor(
    wind_speed_ms: float,
    wind_direction_deg: float,
    propagation_angle_deg: float,
    wind_coefficient: float = 0.15,
    backing_coefficient: float = 0.10,
    max_factor: float = 8.0,
    min_factor: float = 0.1,
) -> float:
    """
    Calculate directional spread amplification factor from wind vector.

    Convention:
    - wind_direction_deg is meteorological 'FROM' direction (0=N, 90=E, 180=S, 270=W).
    - Heading direction towards which wind blows is (wind_direction_deg + 180) % 360.
    - propagation_angle_deg is the direction from the burning cell to target cell.

    Returns:
    - K_w: scalar multiplier >= min_factor (1.0 = neutral/calm).
    """
    if wind_speed_ms <= 0.0:
        return 1.0

    # Compass heading towards which wind pushes fire
    wind_heading_deg = (wind_direction_deg + 180.0) % 360.0

    # Angular difference between propagation heading and wind direction
    angular_diff = calculate_circular_angle_diff(propagation_angle_deg, wind_heading_deg)
    cos_theta = math.cos(math.radians(angular_diff))

    if cos_theta >= 0.0:
        # Forward or flank spread: amplified by wind velocity
        kw = 1.0 + wind_coefficient * (wind_speed_ms ** 1.1) * cos_theta
    else:
        # Backing fire against wind: retarded by opposing airflow
        kw = 1.0 / (1.0 + backing_coefficient * wind_speed_ms * abs(cos_theta))

    # Clamp within physical stability bounds
    return float(max(min_factor, min(max_factor, kw)))
