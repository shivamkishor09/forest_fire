"""Aspect and solar radiation factor calculations for fire spread."""

import math


def calculate_aspect_factor(
    aspect_deg: float,
    slope_deg: float = 15.0,
    solar_coefficient: float = 0.20,
    min_factor: float = 0.70,
    max_factor: float = 1.30,
) -> float:
    """
    Calculate solar insolation factor based on slope aspect in the Northern Hemisphere.

    In the Northern Hemisphere (Himalayan / Indian forest belt ~30°N):
    - South-facing slopes (azimuth 180°) receive peak midday solar insolation, drying fuel bed.
    - Southwest-facing slopes (azimuth ~200-225°) receive intense afternoon heating.
    - North-facing slopes (azimuth 0°/360°) receive minimal solar insolation and stay damp.

    Returns:
    - K_a: scalar factor in [min_factor, max_factor] (1.0 = neutral/flat/east-west).
    """
    if slope_deg <= 0.0:
        return 1.0

    # Solar peak heating azimuth in Northern Hemisphere (180° = South)
    peak_solar_azimuth_deg = 180.0
    angle_from_south = math.radians((aspect_deg - peak_solar_azimuth_deg) % 360.0)

    # Slope scaling: steeper slopes amplify solar contrast between N and S faces
    slope_scale = math.sin(math.radians(min(slope_deg, 45.0)))

    ka = 1.0 + solar_coefficient * slope_scale * math.cos(angle_from_south)
    return float(max(min_factor, min(max_factor, ka)))
