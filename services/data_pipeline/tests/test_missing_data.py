"""Unit tests for missing data handling, imputation, and quality auditing."""

from services.data_pipeline.common.types import CanonicalFeatureRecord
from services.data_pipeline.preprocessing.missing_data import MissingDataHandler


def test_missing_data_imputation_and_tracking():
    handler = MissingDataHandler(imputation_strategy="regional_default")

    # Record with some missing fields
    r1 = CanonicalFeatureRecord(
        grid_cell_id="c1",
        cell_code="CELL_01",
        region_id="r1",
        reference_date="2026-05-15",
        centroid_lat=30.2,
        centroid_lon=78.7,
        elevation_m=1200.0,
        slope_deg=18.0,
        aspect_deg=180.0,
        aspect_sin=0.0,
        aspect_cos=-1.0,
        fuel_type="CHIR_PINE",
        ndvi=0.45,
        ndwi=-0.12,
        temperature_c=None,  # Missing
        relative_humidity_pct=None,  # Missing
        wind_speed_ms=4.0,
        wind_direction_deg=180.0,
        wind_u_ms=0.0,
        wind_v_ms=-4.0,
        precipitation_24h_mm=0.0,
        precipitation_7d_mm=0.0,
        fwi=25.0,
        fire_count_7d=0,
        fire_count_30d=0,
        days_since_last_fire=365.0,
        dist_to_recent_fire_m=50000.0,
    )

    audited, report = handler.audit_and_impute_records([r1], run_id="test_run", reference_date="2026-05-15")

    assert len(audited) == 1
    rec = audited[0]
    assert rec.temperature_c == 30.0  # Regional default
    assert rec.relative_humidity_pct == 35.0  # Regional default
    assert "temperature_c" in rec.imputed_fields
    assert "relative_humidity_pct" in rec.imputed_fields
    assert rec.quality_flag == "PARTIALLY_IMPUTED"

    assert report.total_records == 1
    assert report.imputed_records_pct == 100.0
    assert report.clean_records_pct == 0.0


def test_out_of_bounds_clamping():
    handler = MissingDataHandler()

    r_unphysical = CanonicalFeatureRecord(
        grid_cell_id="c2",
        cell_code="CELL_02",
        region_id="r1",
        reference_date="2026-05-15",
        centroid_lat=30.2,
        centroid_lon=78.7,
        elevation_m=1200.0,
        slope_deg=120.0,  # Unphysical slope (> 90°)
        aspect_deg=180.0,
        aspect_sin=0.0,
        aspect_cos=-1.0,
        fuel_type="CHIR_PINE",
        ndvi=0.45,
        ndwi=-0.12,
        temperature_c=85.0,  # Unphysical temperature (> 65°C)
        relative_humidity_pct=25.0,
        wind_speed_ms=4.0,
        wind_direction_deg=180.0,
        wind_u_ms=0.0,
        wind_v_ms=-4.0,
        precipitation_24h_mm=0.0,
        precipitation_7d_mm=0.0,
        fwi=25.0,
        fire_count_7d=0,
        fire_count_30d=0,
        days_since_last_fire=365.0,
        dist_to_recent_fire_m=50000.0,
    )

    audited, report = handler.audit_and_impute_records([r_unphysical])
    rec = audited[0]

    # Clamped to physical bounds
    assert rec.slope_deg == 90.0
    assert rec.temperature_c == 65.0
    assert "slope_deg_clamped" in rec.imputed_fields
    assert "temperature_c_clamped" in rec.imputed_fields
    assert report.out_of_bound_counts["slope_deg"] == 1
    assert report.out_of_bound_counts["temperature_c"] == 1
