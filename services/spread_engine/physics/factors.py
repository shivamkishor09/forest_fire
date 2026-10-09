"""Spread influence factors interface and standard physics factor implementation."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from .wind import calculate_wind_factor
from .slope import calculate_slope_factor, calculate_elevation_slope_factor
from .aspect import calculate_aspect_factor
from .fuel import calculate_fuel_factor, normalize_fuel_type


class SpreadFactors(ABC):
    """Abstract interface calculating propagation coefficients from terrain and meteorology."""

    @abstractmethod
    def calculate_wind_factor(self, wind_speed_ms: float, wind_dir_deg: float, propagation_angle_deg: float) -> float:
        """Calculate directional spread amplification from wind vector."""
        pass

    @abstractmethod
    def calculate_slope_factor(self, slope_deg: float, aspect_deg: float, propagation_angle_deg: float) -> float:
        """Calculate uphill acceleration vs downhill retardation factor."""
        pass

    @abstractmethod
    def calculate_fuel_factor(self, fuel_type: str) -> float:
        """Calculate combustibility coefficient for specified fuel model."""
        pass


class StandardSpreadFactors(SpreadFactors):
    """Production implementation of environmental spread factors for Cellular Automata."""

    def __init__(
        self,
        wind_coefficient: float = 0.15,
        slope_uphill_coeff: float = 2.0,
        slope_downhill_coeff: float = 1.0,
        solar_aspect_coeff: float = 0.20,
    ):
        self.wind_coefficient = wind_coefficient
        self.slope_uphill_coeff = slope_uphill_coeff
        self.slope_downhill_coeff = slope_downhill_coeff
        self.solar_aspect_coeff = solar_aspect_coeff

    def calculate_wind_factor(
        self,
        wind_speed_ms: float,
        wind_dir_deg: float,
        propagation_angle_deg: float,
    ) -> float:
        return calculate_wind_factor(
            wind_speed_ms=wind_speed_ms,
            wind_direction_deg=wind_dir_deg,
            propagation_angle_deg=propagation_angle_deg,
            wind_coefficient=self.wind_coefficient,
        )

    def calculate_slope_factor(
        self,
        slope_deg: float,
        aspect_deg: float,
        propagation_angle_deg: float,
    ) -> float:
        return calculate_slope_factor(
            slope_deg=slope_deg,
            aspect_deg=aspect_deg,
            propagation_angle_deg=propagation_angle_deg,
            uphill_coefficient=self.slope_uphill_coeff,
            downhill_coefficient=self.slope_downhill_coeff,
        )

    def calculate_fuel_factor(self, fuel_type: str) -> float:
        return calculate_fuel_factor(fuel_type)

    def calculate_aspect_factor(self, aspect_deg: float, slope_deg: float = 15.0) -> float:
        return calculate_aspect_factor(
            aspect_deg=aspect_deg,
            slope_deg=slope_deg,
            solar_coefficient=self.solar_aspect_coeff,
        )

    def calculate_total_multiplier(
        self,
        propagation_angle_deg: float,
        distance_weight: float,
        fuel_type: str,
        wind_speed_ms: Optional[float] = None,
        wind_dir_deg: Optional[float] = None,
        slope_deg: Optional[float] = None,
        aspect_deg: Optional[float] = None,
        elevation_diff_m: Optional[float] = None,
        distance_m: Optional[float] = None,
    ) -> float:
        """
        Compute aggregate propagation potential multiplier.
        Returns 0.0 if target cell is non-burnable.
        """
        fuel_factor = self.calculate_fuel_factor(fuel_type)
        if fuel_factor <= 0.0:
            return 0.0

        # Physical extinction condition:
        # In calm wind (<= 0.5 m/s or zero wind) with low-flammability fuel (fuel_factor <= 0.40),
        # flame tilt and radiative heat flux are insufficient to overcome moisture and ignite
        # adjacent 500m cells. Spread multiplier drops to 0.0, suppressing wildfire propagation.
        is_calm_wind = (wind_speed_ms is None or wind_speed_ms <= 0.5)
        is_low_fuel = (fuel_factor <= 0.40)
        is_mild_slope = (slope_deg is None or abs(slope_deg) < 15.0) and (elevation_diff_m is None or elevation_diff_m <= 0)
        if is_calm_wind and is_low_fuel and is_mild_slope:
            return 0.0

        wind_factor = 1.0
        if wind_speed_ms is not None and wind_dir_deg is not None:
            wind_factor = self.calculate_wind_factor(
                wind_speed_ms, wind_dir_deg, propagation_angle_deg
            )

        slope_factor = 1.0
        if elevation_diff_m is not None and distance_m is not None:
            slope_factor = calculate_elevation_slope_factor(
                elevation_diff_m, distance_m,
                uphill_coefficient=self.slope_uphill_coeff,
                downhill_coefficient=self.slope_downhill_coeff,
            )
        elif slope_deg is not None and aspect_deg is not None:
            slope_factor = self.calculate_slope_factor(
                slope_deg, aspect_deg, propagation_angle_deg
            )

        aspect_factor = 1.0
        if aspect_deg is not None:
            eff_slope = slope_deg if slope_deg is not None else 15.0
            aspect_factor = self.calculate_aspect_factor(aspect_deg, eff_slope)

        return float(wind_factor * slope_factor * aspect_factor * fuel_factor * distance_weight)
