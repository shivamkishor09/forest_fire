"""Cellular Automata transition rules and probability evaluation."""

from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from ..models.enums import CellState
from ..calibration.parameters import SimulationParameters
from ..physics.factors import StandardSpreadFactors
from .grid import SimulationGrid
from .neighbourhood import MOORE_NEIGHBOURS, NeighbourOffset, get_neighbour_cells
from .state import GridStateBuffer


class TransitionEvaluator:
    """Evaluates transition probabilities and advances Cellular Automata discrete state."""

    def __init__(
        self,
        parameters: Optional[SimulationParameters] = None,
        physics_factors: Optional[StandardSpreadFactors] = None,
        deterministic: bool = True,
        random_seed: Optional[int] = 42,
    ):
        self.params = parameters or SimulationParameters()
        self.physics = physics_factors or StandardSpreadFactors(
            wind_coefficient=self.params.wind_coefficient,
            slope_uphill_coeff=self.params.slope_uphill_coeff,
            slope_downhill_coeff=self.params.slope_downhill_coeff,
            solar_aspect_coeff=self.params.solar_aspect_coeff,
        )
        self.deterministic = deterministic
        self.rng = np.random.default_rng(random_seed if random_seed is not None else 42)

    def step(
        self,
        grid: SimulationGrid,
        buffer: GridStateBuffer,
        wind_speed_ms: Optional[float] = None,
        wind_dir_deg: Optional[float] = None,
    ) -> int:
        """
        Advance grid state by one discrete sub-step.
        Returns the count of newly ignited cells during this sub-step.
        """
        buffer.prepare_step()

        # Step 1: Decrement burn timers for active burning cells
        burning_mask = (buffer.current_state == CellState.BURNING.value)
        burning_indices = np.argwhere(burning_mask)

        for r, c in burning_indices:
            buffer.next_timer[r, c] -= 1
            if buffer.next_timer[r, c] <= 0:
                buffer.next_state[r, c] = CellState.BURNED.value

        # Step 2: Accumulate ignition probabilities for unburned candidate cells
        # Only cells adjacent to actively burning cells need to be evaluated
        candidate_probabilities: Dict[Tuple[int, int], List[float]] = {}

        for r, c in burning_indices:
            # Active burning source cell
            for nr, nc, offset in get_neighbour_cells(r, c, grid.rows, grid.cols):
                if buffer.current_state[nr, nc] == CellState.UNBURNED.value:
                    # Calculate propagation potential from (r, c) to (nr, nc)
                    target_fuel = str(grid.fuel[nr, nc])
                    target_slope = float(grid.slope[nr, nc])
                    target_aspect = float(grid.aspect[nr, nc])
                    elev_diff = float(grid.elevation[nr, nc] - grid.elevation[r, c])
                    dist_m = grid.resolution_meters * offset.distance_ratio

                    multiplier = self.physics.calculate_total_multiplier(
                        propagation_angle_deg=offset.angle_deg,
                        distance_weight=offset.weight,
                        fuel_type=target_fuel,
                        wind_speed_ms=wind_speed_ms,
                        wind_dir_deg=wind_dir_deg,
                        slope_deg=target_slope,
                        aspect_deg=target_aspect,
                        elevation_diff_m=elev_diff,
                        distance_m=dist_m,
                    )

                    p_single = min(0.95, max(0.0, self.params.base_spread_probability * multiplier))
                    if (nr, nc) not in candidate_probabilities:
                        candidate_probabilities[(nr, nc)] = []
                    candidate_probabilities[(nr, nc)].append(p_single)

        # Step 3: Evaluate ignition condition for all candidate cells
        newly_ignited_count = 0
        for (nr, nc), prob_list in candidate_probabilities.items():
            # Combined probability of ignition by at least one neighbor: 1 - prod(1 - P_k)
            prod_not_ignited = 1.0
            for p in prob_list:
                prod_not_ignited *= (1.0 - p)
            combined_p = 1.0 - prod_not_ignited

            should_ignite = False
            if self.deterministic:
                should_ignite = (combined_p >= self.params.spread_threshold)
            else:
                should_ignite = (self.rng.random() < combined_p)

            if should_ignite:
                buffer.next_state[nr, nc] = CellState.BURNING.value
                buffer.next_timer[nr, nc] = self.params.burning_duration_steps
                newly_ignited_count += 1

        # Step 4: Commit transitions simultaneously
        buffer.commit_step()
        return newly_ignited_count
