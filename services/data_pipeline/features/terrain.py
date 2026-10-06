"""Topographical feature engineering: continuous aspect transformations, slope scaling."""

import math
from typing import Optional, Tuple


def compute_cyclical_aspect(aspect_deg: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    Transform compass aspect (0°-360°) into continuous orthogonal sine and cosine components.
    Avoids artificial discontinuities where 359° and 1° appear distant in numerical feature space.
    aspect_sin = sin(aspect_rad)
    aspect_cos = cos(aspect_rad)
    """
    if aspect_deg is None:
        return None, None

    rad = math.radians(aspect_deg)
    return round(math.sin(rad), 4), round(math.cos(rad), 4)


def compute_slope_gradient_percent(slope_deg: Optional[float]) -> Optional[float]:
    """Convert slope in degrees to slope gradient percent (tan(slope) * 100)."""
    if slope_deg is None:
        return None
    rad = math.radians(min(max(slope_deg, 0.0), 89.9))
    return round(math.tan(rad) * 100.0, 2)
