"""Unit tests for temporal splitting and anti-leakage verification."""

import pytest
import pandas as pd
from services.risk_engine.training.split import TemporalSplitter
from services.risk_engine.common.exceptions import InvalidSplitError


def test_multi_date_temporal_split():
    # Multi-date dataset across 4 dates
    rows = []
    dates = ["2026-05-10", "2026-05-11", "2026-05-12", "2026-05-13"]
    for d in dates:
        for i in range(10):
            rows.append({
                "grid_cell_id": f"cell_{i}",
                "reference_date": d,
                "target_fire_next_24h": 1 if i == 0 else 0,
            })
    df = pd.DataFrame(rows)

    splitter = TemporalSplitter(train_ratio=0.75)
    train_df, val_df, meta = splitter.split(df)

    assert meta["strategy"] == "chronological_by_date"
    assert meta["train_start_date"] == "2026-05-10"
    assert meta["train_end_date"] == "2026-05-12"
    assert meta["val_start_date"] == "2026-05-13"
    assert meta["val_end_date"] == "2026-05-13"

    # Strictly no overlap: train_end < val_start
    assert meta["train_end_date"] < meta["val_start_date"]
    assert len(train_df) == 30
    assert len(val_df) == 10


def test_single_date_stratified_split():
    # Single-date dataset
    rows = []
    for i in range(100):
        rows.append({
            "grid_cell_id": f"cell_{i}",
            "reference_date": "2026-05-15",
            "target_fire_next_24h": 1 if i < 10 else 0,
        })
    df = pd.DataFrame(rows)

    splitter = TemporalSplitter(train_ratio=0.70)
    train_df, val_df, meta = splitter.split(df)

    assert meta["strategy"] == "deterministic_stratified_single_date"
    assert len(train_df) + len(val_df) == 100
    assert meta["train_positives"] > 0
    assert meta["val_positives"] > 0


def test_empty_df_raises():
    splitter = TemporalSplitter()
    with pytest.raises(InvalidSplitError):
        splitter.split(pd.DataFrame())
