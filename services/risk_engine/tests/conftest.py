"""Shared pytest fixtures and synthetic deterministic test datasets."""

import pytest
import numpy as np
import pandas as pd


@pytest.fixture
def sample_feature_matrix():
    np.random.seed(42)
    rows = []
    for i in range(150):
        temp = float(np.random.uniform(25.0, 42.0))
        rh = float(np.random.uniform(15.0, 60.0))
        fwi = float(np.random.uniform(10.0, 80.0))
        target = 1 if (temp > 35.0 and rh < 25.0 and fwi > 40.0) else 0

        rows.append({
            "grid_cell_id": f"cell_{i:04d}",
            "cell_code": f"CELL_{i:04d}",
            "reference_date": "2026-05-15",
            "elevation_m": float(np.random.uniform(600, 2400)),
            "slope_deg": float(np.random.uniform(5, 40)),
            "aspect_deg": float(np.random.uniform(0, 360)),
            "aspect_sin": float(np.sin(np.radians(180))),
            "aspect_cos": float(np.cos(np.radians(180))),
            "fuel_type": "CONIFER_HIGH_FLAMMABILITY" if i % 2 == 0 else "BROADLEAF_MODERATE_LITTER",
            "ndvi": float(np.random.uniform(0.2, 0.7)),
            "ndwi": float(np.random.uniform(-0.3, 0.1)),
            "temperature_c": temp,
            "relative_humidity_pct": rh,
            "wind_speed_ms": float(np.random.uniform(2.0, 10.0)),
            "wind_direction_deg": float(np.random.uniform(0, 360)),
            "wind_u_ms": -3.0,
            "wind_v_ms": -4.0,
            "precipitation_24h_mm": 0.0,
            "precipitation_7d_mm": 0.0,
            "fwi": fwi,
            "fire_count_7d": int(np.random.poisson(0.5)),
            "fire_count_30d": int(np.random.poisson(1.5)),
            "days_since_last_fire": float(np.random.uniform(5, 365)),
            "dist_to_recent_fire_m": float(np.random.uniform(500, 25000)),
            "target_fire_next_24h": target,
        })
    df = pd.DataFrame(rows)
    if (df["target_fire_next_24h"] == 1).sum() < 5:
        df.loc[:4, "target_fire_next_24h"] = 1
    return df
