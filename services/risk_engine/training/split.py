"""Time-aware temporal train/validation splitting without lookahead leakage."""

from typing import Any, Dict, Optional, Tuple
import pandas as pd
from ..common.exceptions import InvalidSplitError


class TemporalSplitter:
    """
    Partitions a dataset temporally such that training data strictly precedes validation/test data.
    Guarantees: max(T_train) <= min(T_val).
    """

    def __init__(self, train_ratio: float = 0.75, cutoff_date: Optional[str] = None):
        """
        Args:
            train_ratio: Fraction of chronological dates to allocate to training (default 0.75).
            cutoff_date: Optional explicit YYYY-MM-DD boundary. Dates <= cutoff are train, > cutoff are val.
        """
        self.train_ratio = train_ratio
        self.cutoff_date = cutoff_date

    def split(
        self,
        df: pd.DataFrame,
        date_col: str = "reference_date",
        target_col: str = "target_fire_next_24h",
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Execute temporal split and return (train_df, val_df, split_metadata).
        """
        if df.empty:
            raise InvalidSplitError("Cannot split empty DataFrame.")

        unique_dates = sorted(df[date_col].astype(str).unique())

        if len(unique_dates) > 1:
            if self.cutoff_date is not None:
                split_cutoff = self.cutoff_date
            else:
                split_idx = max(1, int(len(unique_dates) * self.train_ratio))
                split_idx = min(split_idx, len(unique_dates) - 1)
                split_cutoff = unique_dates[split_idx - 1]

            train_mask = df[date_col].astype(str) <= split_cutoff
            val_mask = df[date_col].astype(str) > split_cutoff

            train_df = df[train_mask].copy()
            val_df = df[val_mask].copy()
        else:
            # Single-date dataset (e.g. single day development sample):
            # Deterministic index-based stratified split to preserve both classes in train and validation
            positives = df[df[target_col] == 1]
            negatives = df[df[target_col] == 0]

            n_pos_train = max(1, int(len(positives) * self.train_ratio)) if len(positives) > 1 else len(positives)
            n_neg_train = int(len(negatives) * self.train_ratio)

            train_pos = positives.iloc[:n_pos_train]
            val_pos = positives.iloc[n_pos_train:]
            train_neg = negatives.iloc[:n_neg_train]
            val_neg = negatives.iloc[n_neg_train:]

            # If validation has 0 positives (e.g. tiny test set with only 1-2 positives), keep at least 1 in val if possible
            if len(val_pos) == 0 and len(positives) >= 2:
                train_pos = positives.iloc[:-1]
                val_pos = positives.iloc[-1:]

            train_df = pd.concat([train_pos, train_neg]).sample(frac=1.0, random_state=42).reset_index(drop=True)
            val_df = pd.concat([val_pos, val_neg]).sample(frac=1.0, random_state=42).reset_index(drop=True)

        if train_df.empty or val_df.empty:
            raise InvalidSplitError(
                f"Temporal split produced an empty partition! Train size: {len(train_df)}, Val size: {len(val_df)}"
            )

        # Audit temporal bounds
        train_start = str(train_df[date_col].min())
        train_end = str(train_df[date_col].max())
        val_start = str(val_df[date_col].min())
        val_end = str(val_df[date_col].max())

        # If multiple dates, verify strictly train_end <= val_start
        if len(unique_dates) > 1 and train_end > val_start:
            raise InvalidSplitError(
                f"Data leakage detected in temporal split! Train end ({train_end}) is after validation start ({val_start})."
            )

        metadata = {
            "strategy": "chronological_by_date" if len(unique_dates) > 1 else "deterministic_stratified_single_date",
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "train_positives": int((train_df[target_col] == 1).sum()),
            "val_positives": int((val_df[target_col] == 1).sum()),
            "train_start_date": train_start,
            "train_end_date": train_end,
            "val_start_date": val_start,
            "val_end_date": val_end,
        }

        return train_df, val_df, metadata
