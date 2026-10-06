"""Unit tests for Risk Engine contracts and predictor interface."""

import pytest
from services.risk_engine.models.base import BaseRiskModel, ModelMetadata
from services.risk_engine.inference.predictor import RiskPredictor, RiskInferenceInput
from packages.shared_types.contracts import RiskClass


class MockRiskModel(BaseRiskModel):
    """Deterministic contract mock model for Phase 1 verification."""

    def predict_susceptibility(self, features):
        # Deterministic contract calculation (not fake ML)
        return 0.65


def test_risk_predictor_contract():
    """Verify that RiskPredictor validates features and yields standard contract."""
    metadata = ModelMetadata(
        model_name="mock-rf",
        model_version="v1.0.0",
        algorithm="RandomForest"
    )
    model = MockRiskModel(metadata)
    predictor = RiskPredictor(model)

    features = {
        "elevation_m": 1200.0,
        "slope_deg": 20.0,
        "temperature_c": 32.0,
        "relative_humidity_pct": 25.0,
        "wind_speed_ms": 5.0,
        "ndvi": 0.35,
        "fwi": 25.0,
    }

    input_data = RiskInferenceInput(
        grid_cell_id="cell-test-01",
        features=features,
        region_id="region-test-01"
    )

    result = predictor.predict_risk(input_data)
    assert result.grid_cell_id == "cell-test-01"
    assert result.probability == 0.65
    assert result.risk_class == RiskClass.HIGH
    assert result.model_version == "v1.0.0"


def test_risk_probability_classification():
    """Verify risk classification threshold boundaries."""
    assert RiskPredictor.classify_probability(0.10) == RiskClass.LOW
    assert RiskPredictor.classify_probability(0.30) == RiskClass.MODERATE
    assert RiskPredictor.classify_probability(0.60) == RiskClass.HIGH
    assert RiskPredictor.classify_probability(0.85) == RiskClass.EXTREME
