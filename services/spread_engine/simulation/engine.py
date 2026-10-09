"""Execution engine orchestrating 12-hour Cellular Automata fire spread simulation."""

from typing import Dict, List, Optional, Union
import numpy as np

from ..common.config import ENGINE_VERSION, SpreadEngineSettings
from ..common.validation import validate_simulation_inputs
from ..calibration.parameters import SimulationParameters
from ..models.config import SimulationInput
from ..models.inputs import SpreadSimulationInput, WindCondition
from ..models.enums import CellState, FuelClass
from ..physics.factors import StandardSpreadFactors
from .grid import SimulationGrid
from .state import GridStateBuffer
from .transitions import TransitionEvaluator
from .boundary import extract_fire_boundary_geojson
from .metrics import (
    calculate_burned_area_ha,
    calculate_active_burning_cells,
    calculate_spread_velocity_kmh,
    calculate_dominant_spread_direction_deg,
    calculate_fire_intensity_mw,
)
from .timesteps import SimulationResult, TimestepResult


class SpreadSimulationEngine:
    """
    Main orchestrator for Cellular Automata fire spread simulation.
    Simulates hourly fire propagation across a 500m grid for up to 12 hours.
    """

    def __init__(
        self,
        parameters: Optional[SimulationParameters] = None,
        settings: Optional[SpreadEngineSettings] = None,
    ):
        self.params = parameters or SimulationParameters()
        self.settings = settings or SpreadEngineSettings()
        self.physics = StandardSpreadFactors(
            wind_coefficient=self.params.wind_coefficient,
            slope_uphill_coeff=self.params.slope_uphill_coeff,
            slope_downhill_coeff=self.params.slope_downhill_coeff,
            solar_aspect_coeff=self.params.solar_aspect_coeff,
        )

    def execute(self, sim_input: Union[SpreadSimulationInput, SimulationInput]) -> SimulationResult:
        """
        Execute the complete simulation and generate hourly timestep snapshots.
        """
        # Normalize legacy SimulationInput if passed
        if isinstance(sim_input, SimulationInput):
            typed_input = SpreadSimulationInput.from_legacy_input(sim_input)
        else:
            typed_input = sim_input

        # Validate inputs
        wind_speed = typed_input.wind.speed_ms if typed_input.wind else None
        wind_dir = typed_input.wind.direction_deg if typed_input.wind else None

        validate_simulation_inputs(
            duration_hours=typed_input.duration_hours,
            grid_rows=typed_input.grid_rows,
            grid_cols=typed_input.grid_cols,
            grid_resolution_meters=typed_input.grid_resolution_meters,
            ignition_lat=typed_input.ignition.lat,
            ignition_lon=typed_input.ignition.lon,
            wind_speed_ms=wind_speed,
            wind_direction_deg=wind_dir,
        )

        # Initialize spatial grid centered on ignition coordinates
        grid = SimulationGrid(
            rows=typed_input.grid_rows,
            cols=typed_input.grid_cols,
            resolution_meters=typed_input.grid_resolution_meters,
            center_lat=typed_input.ignition.lat,
            center_lon=typed_input.ignition.lon,
            default_elevation_m=typed_input.terrain.elevation_m,
            default_slope_deg=typed_input.terrain.slope_deg,
            default_aspect_deg=typed_input.terrain.aspect_deg,
            default_fuel=typed_input.terrain.fuel_type,
        )

        # Populate custom terrain rasters if provided
        if typed_input.terrain_grid is not None:
            if typed_input.terrain_grid.elevation_matrix is not None:
                grid.elevation[:] = typed_input.terrain_grid.elevation_matrix
            if typed_input.terrain_grid.slope_matrix is not None:
                grid.slope[:] = typed_input.terrain_grid.slope_matrix
            if typed_input.terrain_grid.aspect_matrix is not None:
                grid.aspect[:] = typed_input.terrain_grid.aspect_matrix
            if typed_input.terrain_grid.fuel_matrix is not None:
                grid.fuel[:] = typed_input.terrain_grid.fuel_matrix

        # Map ignition point to grid coordinates
        if typed_input.ignition.row is not None and typed_input.ignition.col is not None:
            ign_r, ign_c = typed_input.ignition.row, typed_input.ignition.col
        else:
            ign_r, ign_c = grid.lat_lon_to_row_col(typed_input.ignition.lat, typed_input.ignition.lon)

        # Check critical spread threshold:
        # In calm/zero wind (wind_speed <= 0.5 m/s) with low flammability fuel (fuel_factor <= 0.40),
        # convective and radiative heat flux is insufficient to sustain wildfire propagation.
        # The fire does not propagate across the landscape, resulting in zero/minimum spread.
        fuel_factor = self.physics.calculate_fuel_factor(typed_input.terrain.fuel_type)
        is_calm_wind = (wind_speed is None or wind_speed <= 0.5)
        is_low_fuel = (fuel_factor <= 0.40)
        is_mild_slope = (abs(typed_input.terrain.slope_deg) < 15.0)
        heading_fallback = typed_input.wind.heading_deg if typed_input.wind else 0.0

        if is_calm_wind and is_low_fuel and is_mild_slope:
            empty_poly = {"type": "Polygon", "coordinates": []}
            timesteps: List[TimestepResult] = [
                TimestepResult(
                    step_hour=hour,
                    burned_area_ha=0.0,
                    spread_velocity_kmh=0.0,
                    spread_direction_deg=heading_fallback,
                    intensity_mw=0.0,
                    boundary_polygon=empty_poly,
                    active_burning_cells=0,
                    total_burned_cells=0,
                )
                for hour in range(1, typed_input.duration_hours + 1)
            ]
            return SimulationResult(
                simulation_id=typed_input.simulation_id,
                total_area_burned_ha=0.0,
                duration_hours=typed_input.duration_hours,
                peak_spread_velocity_kmh=0.0,
                timesteps=timesteps,
                engine_version=ENGINE_VERSION,
            )

        # Ignite initial cell
        grid.ignite(ign_r, ign_c, burning_steps=self.params.burning_duration_steps)

        # Initialize state double-buffer and transition evaluator
        buffer = GridStateBuffer.from_grid(grid.state, grid.burn_timer)
        evaluator = TransitionEvaluator(
            parameters=self.params,
            physics_factors=self.physics,
            deterministic=typed_input.deterministic,
            random_seed=typed_input.random_seed,
        )

        timesteps: List[TimestepResult] = []
        sub_steps = self.params.sub_steps_per_hour

        # Simulate hour by hour
        for hour in range(1, typed_input.duration_hours + 1):
            for _ in range(sub_steps):
                evaluator.step(
                    grid=grid,
                    buffer=buffer,
                    wind_speed_ms=wind_speed,
                    wind_dir_deg=wind_dir,
                )

            # Compute snapshot metrics
            burned_ha = calculate_burned_area_ha(grid)
            velocity_kmh = calculate_spread_velocity_kmh(grid, ign_r, ign_c, float(hour))
            direction_deg = calculate_dominant_spread_direction_deg(grid, ign_r, ign_c, heading_fallback)
            active_cells = calculate_active_burning_cells(grid)
            total_burned_cells = int(np.count_nonzero(
                (grid.state == CellState.BURNING.value) | (grid.state == CellState.BURNED.value)
            ))
            intensity_mw = calculate_fire_intensity_mw(
                active_burning_count=active_cells,
                wind_speed_ms=wind_speed,
                base_intensity_mw=self.params.base_intensity_mw,
                intensity_per_cell_mw=self.params.intensity_per_burning_cell_mw,
            )
            boundary = extract_fire_boundary_geojson(grid)

            timesteps.append(
                TimestepResult(
                    step_hour=hour,
                    burned_area_ha=burned_ha,
                    spread_velocity_kmh=velocity_kmh,
                    spread_direction_deg=direction_deg,
                    intensity_mw=intensity_mw,
                    boundary_polygon=boundary,
                    active_burning_cells=active_cells,
                    total_burned_cells=total_burned_cells,
                )
            )

        total_burned = timesteps[-1].burned_area_ha if timesteps else 0.0
        peak_velocity = max((ts.spread_velocity_kmh for ts in timesteps), default=0.0)

        return SimulationResult(
            simulation_id=typed_input.simulation_id,
            total_area_burned_ha=total_burned,
            duration_hours=typed_input.duration_hours,
            peak_spread_velocity_kmh=peak_velocity,
            timesteps=timesteps,
            engine_version=ENGINE_VERSION,
        )
