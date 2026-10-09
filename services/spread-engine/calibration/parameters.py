"""Empirical calibration parameters for Cellular Automata fire spread simulation."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SimulationParameters:
    """
    Tuned simulation coefficients for 500m spatial grid and hourly propagation timesteps.
    These values calibrate empirical spread rates to observed Indian forest fire behavior
    (typically 0.3 km/h to 2.5 km/h depending on wind, topography, and fuel type).
    """
    # Baseline probability of ignition to an orthogonal neighbor per hour in calm flat terrain
    base_spread_probability: float = 0.28

    # Wind amplification coefficients
    wind_coefficient: float = 0.15
    backing_coefficient: float = 0.10

    # Slope acceleration/retardation coefficients
    slope_uphill_coeff: float = 2.0
    slope_downhill_coeff: float = 1.0

    # Aspect insolation coefficient (Northern Hemisphere)
    solar_aspect_coeff: float = 0.20

    # Cellular Automata temporal parameters
    sub_steps_per_hour: int = 2
    burning_duration_steps: int = 3  # Cell remains BURNING for 3 sub-steps (~1.5 hours) before transitioning to BURNED

    # Deterministic ignition threshold (when in deterministic mode)
    spread_threshold: float = 0.25
    accumulation_threshold: float = 0.85
    flash_ignition_threshold: float = 0.80

    # Radiative fire intensity coefficients (MW)
    base_intensity_mw: float = 4.0
    intensity_per_burning_cell_mw: float = 0.35
