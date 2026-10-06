"""Cell state transitions and double-buffer state manager for Cellular Automata."""

from dataclasses import dataclass
from typing import Tuple
import numpy as np

from ..models.enums import CellState


@dataclass
class GridStateBuffer:
    """Double-buffered state and timer matrices ensuring simultaneous state updates."""
    current_state: np.ndarray
    next_state: np.ndarray
    current_timer: np.ndarray
    next_timer: np.ndarray

    @classmethod
    def from_grid(cls, state_matrix: np.ndarray, timer_matrix: np.ndarray) -> "GridStateBuffer":
        """Initialize double buffers from active grid arrays."""
        return cls(
            current_state=state_matrix,
            next_state=state_matrix.copy(),
            current_timer=timer_matrix,
            next_timer=timer_matrix.copy(),
        )

    def prepare_step(self) -> None:
        """Synchronize next buffers with current state prior to step evaluation."""
        np.copyto(self.next_state, self.current_state)
        np.copyto(self.next_timer, self.current_timer)

    def commit_step(self) -> None:
        """Commit all pending transitions simultaneously into the active grid state."""
        np.copyto(self.current_state, self.next_state)
        np.copyto(self.current_timer, self.next_timer)
