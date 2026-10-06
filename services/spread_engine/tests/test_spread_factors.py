"""Unit tests for environmental physics spread factors: wind, slope, aspect, and fuel."""

import pytest
import math
from services.spread_engine.physics.wind import (
    calculate_circular_angle_diff,
    calculate_wind_factor,
)
from services.spread_engine.physics.slope import (
    calculate_slope_factor,
    calculate_elevation_slope_factor,
)
from services.spread_engine.physics.aspect import calculate_aspect_factor
from services.spread_engine.physics.fuel import (
    calculate_fuel_factor,
    normalize_fuel_type,
    FUEL_FLAMMABILITY_FACTORS,
)
from services.spread_engine.physics.factors import StandardSpreadFactors
from services.spread_engine.models.enums import FuelClass


class TestWindPhysics:
    """Verify wind amplification, directionality, and circular arithmetic."""

    def test_circular_angle_difference(self):
        """Verify minimal signed angular difference and 360-degree wrap-around."""
        # Collinear angles
        assert calculate_circular_angle_diff(90.0, 90.0) == 0.0
        # Right angles
        assert calculate_circular_angle_diff(90.0, 0.0) == 90.0
        assert calculate_circular_angle_diff(0.0, 90.0) == -90.0
        # Wrap-around boundary
        assert calculate_circular_angle_diff(1.0, 359.0) == 2.0
        assert calculate_circular_angle_diff(359.0, 1.0) == -2.0
        assert calculate_circular_angle_diff(10.0, 350.0) == 20.0

    def test_zero_wind_is_neutral(self):
        """Zero wind speed should return a neutral multiplier of 1.0 in all directions."""
        for angle in [0.0, 45.0, 90.0, 180.0, 270.0]:
            kw = calculate_wind_factor(wind_speed_ms=0.0, wind_direction_deg=180.0, propagation_angle_deg=angle)
            assert kw == 1.0

    def test_downwind_amplification(self):
        """
        Wind FROM South (180°) blows towards North (0°).
        Propagation heading North (0°) must be amplified, South (180°) must be retarded.
        """
        wind_speed = 10.0
        wind_from_deg = 180.0  # Blows toward 0° (North)

        kw_downwind = calculate_wind_factor(wind_speed, wind_from_deg, propagation_angle_deg=0.0)
        kw_flank = calculate_wind_factor(wind_speed, wind_from_deg, propagation_angle_deg=90.0)
        kw_upwind = calculate_wind_factor(wind_speed, wind_from_deg, propagation_angle_deg=180.0)

        assert kw_downwind > 1.0
        assert kw_downwind > kw_flank
        assert kw_flank > kw_upwind
        assert kw_upwind < 1.0

    def test_wind_velocity_scaling(self):
        """Higher downwind velocities must produce strictly greater amplification."""
        kw_low = calculate_wind_factor(wind_speed_ms=5.0, wind_direction_deg=270.0, propagation_angle_deg=90.0)
        kw_high = calculate_wind_factor(wind_speed_ms=15.0, wind_direction_deg=270.0, propagation_angle_deg=90.0)
        assert kw_high > kw_low


class TestSlopePhysics:
    """Verify uphill acceleration and downhill retardation."""

    def test_zero_slope_is_neutral(self):
        """Flat ground (slope=0°) must return factor of 1.0 regardless of angle."""
        ks = calculate_slope_factor(slope_deg=0.0, aspect_deg=180.0, propagation_angle_deg=0.0)
        assert ks == 1.0

    def test_uphill_acceleration_vs_downhill_retardation(self):
        """
        Slope facing downhill towards South (aspect=180°).
        Uphill bearing is North (0°).
        Propagation North (0°) is uphill (>1.0), South (180°) is downhill (<1.0).
        """
        ks_uphill = calculate_slope_factor(slope_deg=20.0, aspect_deg=180.0, propagation_angle_deg=0.0)
        ks_downhill = calculate_slope_factor(slope_deg=20.0, aspect_deg=180.0, propagation_angle_deg=180.0)
        ks_contour = calculate_slope_factor(slope_deg=20.0, aspect_deg=180.0, propagation_angle_deg=90.0)

        assert ks_uphill > 1.0
        assert ks_downhill < 1.0
        assert ks_uphill > ks_contour > ks_downhill

    def test_elevation_difference_slope_factor(self):
        """Positive elevation diff (uphill) must yield factor > 1.0, negative < 1.0."""
        ks_up = calculate_elevation_slope_factor(elevation_diff_m=100.0, distance_m=500.0)
        ks_down = calculate_elevation_slope_factor(elevation_diff_m=-100.0, distance_m=500.0)
        ks_flat = calculate_elevation_slope_factor(elevation_diff_m=0.0, distance_m=500.0)

        assert ks_up > 1.0
        assert ks_down < 1.0
        assert ks_flat == 1.0


class TestAspectPhysics:
    """Verify solar insolation aspect scaling in the Northern Hemisphere."""

    def test_south_facing_higher_than_north_facing(self):
        """South-facing slope (180°) receives peak solar radiation compared to North (0°)."""
        ka_south = calculate_aspect_factor(aspect_deg=180.0, slope_deg=20.0)
        ka_north = calculate_aspect_factor(aspect_deg=0.0, slope_deg=20.0)
        assert ka_south > 1.0
        assert ka_north < 1.0
        assert ka_south > ka_north

    def test_flat_aspect_is_neutral(self):
        """Aspect on flat ground (slope=0°) must return 1.0."""
        assert calculate_aspect_factor(aspect_deg=180.0, slope_deg=0.0) == 1.0


class TestFuelPhysics:
    """Verify fuel flammability multipliers and non-burnable behavior."""

    def test_flammability_rankings(self):
        """Conifer (Chir Pine) flammability must exceed broadleaf and grassland."""
        k_pine = calculate_fuel_factor(FuelClass.CONIFER_HIGH_FLAMMABILITY.value)
        k_grass = calculate_fuel_factor(FuelClass.GRASSLAND_FAST_SPREAD.value)
        k_broadleaf = calculate_fuel_factor(FuelClass.BROADLEAF_MODERATE_LITTER.value)
        k_crop = calculate_fuel_factor(FuelClass.AGRICULTURE_SEASONAL.value)

        assert k_pine > k_grass > k_broadleaf > k_crop
        assert k_broadleaf == 1.0  # Reference baseline

    def test_non_burnable_fuels_are_zero(self):
        """Water and barren rock/snow must have 0.0 combustibility."""
        assert calculate_fuel_factor(FuelClass.NON_BURNABLE_WATER.value) == 0.0
        assert calculate_fuel_factor(FuelClass.NON_BURNABLE_BARREN.value) == 0.0
        assert calculate_fuel_factor("WATER_RIVER") == 0.0
        assert calculate_fuel_factor("BARREN_ROCK_SNOW") == 0.0

    def test_raw_alias_normalization(self):
        """Raw data adapters must resolve to canonical FuelClass values."""
        assert normalize_fuel_type("CHIR_PINE") == FuelClass.CONIFER_HIGH_FLAMMABILITY.value
        assert normalize_fuel_type("SAL_DECIDUOUS") == FuelClass.BROADLEAF_HIGH_LITTER.value
        assert normalize_fuel_type("UNKNOWN_RANDOM") == FuelClass.UNKNOWN.value


class TestUnifiedSpreadFactors:
    """Verify composite multiplier calculation with all factors combined."""

    def test_total_multiplier_downwind_uphill(self):
        factors = StandardSpreadFactors()
        # Wind blowing to North (0°), Uphill to North (0°), Chir pine
        multiplier = factors.calculate_total_multiplier(
            propagation_angle_deg=0.0,
            distance_weight=1.0,
            fuel_type="CHIR_PINE",
            wind_speed_ms=8.0,
            wind_dir_deg=180.0,  # Blows toward 0°
            slope_deg=15.0,
            aspect_deg=180.0,    # Uphill is 0°
        )
        assert multiplier > 2.0  # Significant compound acceleration

    def test_total_multiplier_non_burnable_is_zero(self):
        factors = StandardSpreadFactors()
        multiplier = factors.calculate_total_multiplier(
            propagation_angle_deg=0.0,
            distance_weight=1.0,
            fuel_type="WATER_RIVER",
            wind_speed_ms=20.0,
            wind_dir_deg=180.0,
        )
        assert multiplier == 0.0
