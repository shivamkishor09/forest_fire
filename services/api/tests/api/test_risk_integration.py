"""Phase 6 integration tests verifying Risk Engine -> FastAPI -> GeoJSON integration."""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)

GARHWAL_UUID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
GARHWAL_CODE = "UTTARAKHAND_GARHWAL"
WAYANAD_UUID = "7ca85f64-5717-4562-b3fc-2c963f66afa7"
SHIMLA_UUID = "8da85f64-5717-4562-b3fc-2c963f66afa8"


def test_health_reports_risk_model_available():
    """Verify GET /api/v1/health reports active risk model status."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    assert data["services"]["risk_model"] == "available"


def test_get_risk_layer_real_model_inference():
    """
    Verify GET /api/v1/risk/{region_id} executes real XGBoost inference and returns
    GeoJSON FeatureCollection with cell features and enriched properties.
    """
    resp = client.get(f"/api/v1/risk/{GARHWAL_CODE}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["type"] == "FeatureCollection"
    assert "properties" in data
    assert data["properties"]["model_version"] in ("risk-xgboost-v001", "risk-xgboost-v002")
    assert data["properties"]["total_cells"] > 0
    assert len(data["features"]) == data["properties"]["total_cells"]

    # Validate cell feature structure
    sample_cell = data["features"][0]
    assert sample_cell["type"] == "Feature"
    assert sample_cell["geometry"]["type"] == "Polygon"
    assert len(sample_cell["geometry"]["coordinates"][0]) >= 4

    props = sample_cell["properties"]
    assert "grid_cell_id" in props
    assert "risk_probability" in props
    assert 0.0 <= props["risk_probability"] <= 1.0
    assert props["risk_class"] in ("LOW", "MODERATE", "HIGH", "EXTREME")
    assert props["model_version"] in ("risk-xgboost-v001", "risk-xgboost-v002")

    # Verify 24-hour forecast window
    assert "forecast_start" in props
    assert "forecast_end" in props
    f_start = datetime.fromisoformat(props["forecast_start"])
    f_end = datetime.fromisoformat(props["forecast_end"])
    assert (f_end - f_start) == timedelta(hours=24)

    # Verify environmental features
    assert "elevation_m" in props
    assert "slope_deg" in props
    assert "fuel_type" in props
    assert "fwi" in props


def test_get_risk_layer_by_region_uuid():
    """Verify GET /api/v1/risk/{region_id} resolves region by UUID identifier."""
    resp = client.get(f"/api/v1/risk/{GARHWAL_UUID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0


def test_get_risk_layer_min_risk_filtering():
    """Verify min_risk query parameter filters grid cells above threshold."""
    # Filter with min_risk=LOW (should return all cells)
    resp_low = client.get(f"/api/v1/risk/{GARHWAL_CODE}?min_risk=LOW")
    assert resp_low.status_code == 200
    all_count = len(resp_low.json()["features"])

    # Filter with min_risk=EXTREME (should return only EXTREME cells)
    resp_ext = client.get(f"/api/v1/risk/{GARHWAL_CODE}?min_risk=EXTREME")
    assert resp_ext.status_code == 200
    ext_count = len(resp_ext.json()["features"])

    assert ext_count <= all_count


def test_post_risk_predict_execution():
    """Verify POST /api/v1/risk/predict triggers batch inference and persists results."""
    payload = {
        "region_id": GARHWAL_UUID,
        "target_date": "2026-10-06",
        "force_recompute": True,
        "model_name": "risk-xgboost-v002",
    }
    resp = client.post("/api/v1/risk/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "COMPLETED"
    assert data["cells_predicted"] > 0
    assert data["model_version"] in ("risk-xgboost-v001", "risk-xgboost-v002")
    assert 0.0 <= data["mean_risk_probability"] <= 1.0
    assert "job_id" in data
    assert "completed_at" in data


def test_risk_predict_idempotency():
    """Verify repeated prediction requests return existing results without duplicate work."""
    payload = {
        "region_id": GARHWAL_CODE,
        "target_date": "2026-10-06",
        "force_recompute": False,
        "model_name": "risk-xgboost-v002",
    }
    resp1 = client.post("/api/v1/risk/predict", json=payload)
    assert resp1.status_code == 200
    job_id1 = resp1.json()["job_id"]

    resp2 = client.post("/api/v1/risk/predict", json=payload)
    assert resp2.status_code == 200
    job_id2 = resp2.json()["job_id"]

    # When cached in memory, returns the exact same job ID
    assert job_id1 == job_id2


def test_get_risk_summary_endpoint():
    """Verify GET /api/v1/risk/{region_id}/summary returns regional class distributions."""
    resp = client.get(f"/api/v1/risk/{GARHWAL_CODE}/summary?target_date=2026-10-06")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_cells"] > 0
    assert data["model_version"] in ("risk-xgboost-v001", "risk-xgboost-v002")
    assert 0.0 <= data["mean_probability"] <= 1.0

    dist = data["risk_distribution"]
    assert "low" in dist
    assert "moderate" in dist
    assert "high" in dist
    assert "extreme" in dist
    assert (dist["low"] + dist["moderate"] + dist["high"] + dist["extreme"]) == data["total_cells"]


def test_risk_predict_unknown_region():
    """Verify POST /api/v1/risk/predict returns 404 for unknown region."""
    payload = {
        "region_id": "non-existent-region-id",
        "target_date": "2026-10-06",
    }
    resp = client.post("/api/v1/risk/predict", json=payload)
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_risk_layer_unknown_region():
    """Verify GET /api/v1/risk/{region_id} returns 404 for unknown region."""
    resp = client.get("/api/v1/risk/UNKNOWN_REGION_CODE")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_risk_predict_region_missing_environmental_features():
    """Verify region without model-ready features returns 404 DATA_NOT_FOUND."""
    payload = {
        "region_id": SHIMLA_UUID,
        "target_date": "2026-10-06",
    }
    resp = client.post("/api/v1/risk/predict", json=payload)
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "DATA_NOT_FOUND"


def test_risk_predict_unregistered_model_version():
    """Verify requesting an unregistered model version returns 503 MODEL_UNAVAILABLE."""
    payload = {
        "region_id": GARHWAL_UUID,
        "target_date": "2026-10-06",
        "model_name": "non_existent_model_v999",
    }
    resp = client.post("/api/v1/risk/predict", json=payload)
    assert resp.status_code == 503
    data = resp.json()
    assert data["error"]["code"] == "MODEL_UNAVAILABLE"
