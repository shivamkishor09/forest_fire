"""Simulation runner coordinating fire spread execution."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models.config import SimulationInput
from ..simulation.timesteps import SimulationResult, TimestepResult
from ..simulation.engine import SpreadSimulationEngine
from ..calibration.parameters import SimulationParameters


class BaseSimulationRunner(ABC):
    """Abstract runner contract for fire spread simulation engines."""

    @abstractmethod
    def run_simulation(self, sim_input: SimulationInput) -> SimulationResult:
        """
        Execute fire spread simulation for the requested duration.
        """
        pass


class CellularAutomataRunner(BaseSimulationRunner):
    """
    Cellular Automata simulation runner.
    Executes physics-informed discrete cellular automata fire propagation.
    """

    def __init__(self, parameters: Optional[SimulationParameters] = None):
        self.engine = SpreadSimulationEngine(parameters=parameters)

    def run_simulation(self, sim_input: SimulationInput) -> SimulationResult:
        """
        Execute cellular automata fire spread simulation for up to 12 hours.
        """
        return self.engine.execute(sim_input)
