# 24-Hour Forest Fire Risk Prediction Engine (Phase 5)

This service provides the machine learning training, temporal evaluation, model registry, and high-performance inference engine for 24-hour forest fire risk forecasting across 500m × 500m spatial grid cells.

The risk engine is designed to be fully standalone and decoupled from the FastAPI web service, Celery worker, and PostGIS database, allowing it to run offline, in batch workflows, in CI/CD pipelines, and across distributed training nodes.

---

## 1. Architecture Overview

```
                      Canonical Features (Phase 4)
             (data/processed/<run>/features.parquet / features.csv)
                                     ↓
  +-----------------------------------------------------------------------+
  | services/risk-engine/                                                 |
  |                                                                       |
  |  1. Features & Validation                                             |
  |     - RiskFeatureSchema & FeatureSpec (physical bounds, missing rules) |
  |     - Canonical feature ordering (20 numerical + 10 fuel categories)  |
  |     - RiskFeatureValidator (rejects NaN, Inf, out-of-range anomalies) |
  |                                                                       |
  |  2. Training Pipeline                                                 |
  |     - TrainingDataset (duplicate checks, class balance verification)  |
  |     - TemporalSplitter (strict chronological train/val splits)        |
  |     - FeaturePreprocessor (deterministic one-hot matrix encoding)     |
  |     - XGBoostRiskTrainer (scale_pos_weight imbalance handling)        |
  |     - RandomForestRiskTrainer (baseline comparative benchmark)        |
  |                                                                       |
  |  3. Evaluation & Reporting                                            |
  |     - ClassificationMetrics (ROC-AUC, PR-AUC, F1, Recall, Precision)  |
  |     - RiskModelEvaluator (confusion matrix, probability calibration)  |
  |     - EvaluationReportGenerator (metrics.json, evaluation_report.md)  |
  |     - ModelCardGenerator (comprehensive MODEL_CARD.md generation)     |
  |                                                                       |
  |  4. Model Packaging & Registry                                        |
  |     - ModelArtifactSerializer (native XGBoost model.json, safe JSON)  |
  |     - ModelMetadataManager (provenance, seeds, feature names)         |
  |     - ModelRegistry (filesystem registry at models/risk/<version>/)   |
  |                                                                       |
  |  5. High-Performance Inference                                        |
  |     - ModelLoader (in-memory cached lazy loader)                      |
  |     - RiskPredictor (single-cell, batch, and vectorized DataFrame)   |
  |     - Probability to RiskClass classification (LOW/MODERATE/HIGH/EXTREME)|
  +-----------------------------------------------------------------------+
                                     ↓
              Standardized Prediction Contracts (DATA_CONTRACTS.md)
   (grid_cell_id, probability, risk_class, forecast_window, model_version)
```

---

## 2. Directory Structure

```
services/risk-engine/
├── common/
│   ├── config.py             # RiskEngineSettings & threshold classification
│   ├── exceptions.py         # Domain error hierarchy
│   ├── logging.py            # Structured logging
│   └── types.py              # Pydantic schemas (RiskPrediction, Metadata, Metrics)
├── features/
│   ├── ordering.py           # Canonical continuous & categorical column orders
│   ├── schema.py             # FeatureSpec & physical bounding definitions
│   └── validation.py         # Input validation & anomaly detection
├── training/
│   ├── dataset.py            # Dataset loading, label verification, duplicate guards
│   ├── split.py              # Temporal chronological train/val split
│   ├── preprocessing.py      # Numerical alignment & one-hot fuel encoding
│   ├── trainer.py            # XGBoost & Random Forest trainer implementations
│   └── pipeline.py           # End-to-end load -> split -> train -> evaluate -> register
├── evaluation/
│   ├── metrics.py            # ROC-AUC, PR-AUC, F1, confusion matrix
│   ├── evaluation.py         # RiskModelEvaluator
│   └── reports.py            # Markdown evaluation reports & MODEL_CARD.md generator
├── models/
│   ├── base.py               # BaseRiskModel abstract base class
│   ├── artifact.py           # Safe native JSON model serialization
│   ├── metadata.py           # Metadata management
│   └── registry.py           # Model artifact registry
├── inference/
│   ├── loader.py             # Cached model artifact loader
│   ├── validation.py         # Inference-time feature validation
│   └── predictor.py          # Vectorized batch & single-cell prediction engine
├── tests/                    # 30 comprehensive unit & integration tests
├── cli.py                    # Unified CLI (train, evaluate, predict, info)
└── requirements.txt          # Python dependencies
```

---

## 3. Feature Contract & Physical Definitions

The model consumes 20 continuous numerical features and 1 categorical fuel type feature (encoded into 10 orthogonal indicator columns):

| Feature Name | Type | Physical Meaning | Valid Range | Missing Strategy |
|---|---|---|---|---|
| `elevation_m` | Continuous | Terrain elevation above sea level | [-500, 9000] m | Median imputation |
| `slope_deg` | Continuous | Topographical slope inclination | [0, 90] degrees | Median imputation |
| `aspect_deg` | Continuous | Topographical slope azimuth (North=0°) | [0, 360] degrees | Cyclical encoding |
| `aspect_sin` | Continuous | $\sin(\text{aspect})$ orthogonal coordinate | [-1.0, 1.0] | Auto-derived |
| `aspect_cos` | Continuous | $\cos(\text{aspect})$ orthogonal coordinate | [-1.0, 1.0] | Auto-derived |
| `ndvi` | Continuous | Normalized Difference Vegetation Index | [-1.0, 1.0] | Seasonal mean |
| `ndwi` | Continuous | Normalized Difference Water/Moisture Index | [-1.0, 1.0] | Seasonal mean |
| `temperature_c` | Continuous | 2-meter air temperature | [-50, 60] °C | Spatial IDW |
| `relative_humidity_pct` | Continuous | Relative air humidity | [0, 100] % | Spatial IDW |
| `wind_speed_ms` | Continuous | 10-meter horizontal wind speed | [0, 100] m/s | Spatial IDW |
| `wind_direction_deg` | Continuous | Compass direction wind originates from | [0, 360] degrees | Vector decomposition |
| `wind_u_ms` | Continuous | Zonal orthogonal wind vector component | [-100, 100] m/s | Auto-derived |
| `wind_v_ms` | Continuous | Meridional orthogonal wind vector component | [-100, 100] m/s | Auto-derived |
| `precipitation_24h_mm` | Continuous | Accumulated precipitation over last 24h | [0, 1000] mm | Zero-fill |
| `precipitation_7d_mm` | Continuous | Accumulated precipitation over last 7 days | [0, 5000] mm | Zero-fill |
| `fwi` | Continuous | Canadian Fire Weather Index | [0, 200] | Computed |
| `fire_count_7d` | Continuous | Active fire hotspots within 5km over 7 days | [0, 1000] | Zero-fill |
| `fire_count_30d` | Continuous | Active fire hotspots within 5km over 30 days | [0, 5000] | Zero-fill |
| `days_since_last_fire` | Continuous | Days elapsed since most recent fire event | [0, 3650] days | Default 365.0 |
| `dist_to_recent_fire_m` | Continuous | Distance to closest historical fire hotspot | [0, 100000] m | Default 50000.0 |
| `fuel_type` | Categorical | Dominant vegetation flammability class | 10 classes | One-hot encoded |

---

## 4. Imbalance Strategy & Temporal Splitting

1. **Temporal Validation Splitting:**
   - Standard random train/test splits cause extreme optimistic data leakage when evaluating spatial-temporal phenomena.
   - `TemporalSplitter` sorts samples chronologically by `reference_date` and enforces:
     $$\max(T_{\text{train}}) \le \min(T_{\text{val}})$$
   - Zero observations from future dates leak into the training feature distribution.

2. **Extreme Class Imbalance Handling:**
   - Forest fire occurrence is an extreme rare-event problem ($< 0.1\%$ positive fire cells per day under normal conditions).
   - The trainer automatically calculates the positive class weighting ratio:
     $$\text{scale\_pos\_weight} = \frac{N_{\text{negatives}}}{N_{\text{positives}}}$$
   - This scales gradient updates on positive fire cells without discarding genuine negative samples.

---

## 5. Risk Classification Thresholds

Susceptibility probabilities ($P \in [0.0, 1.0]$) are categorized into operational risk classes:

| Risk Class | Probability Range | Operational Action / Meaning |
|---|---|---|
| `LOW` | $[0.00, 0.25)$ | Routine monitoring; standard baseline conditions |
| `MODERATE` | $[0.25, 0.50)$ | Elevated fire weather; monitor fire-prone slopes |
| `HIGH` | $[0.50, 0.75)$ | Fire danger high; pre-position patrol units |
| `EXTREME` | $[0.75, 1.00]$ | Severe fire danger; rapid suppression readiness |

---

## 6. Model Artifact Package

Trained models are packaged in `models/risk/<model_version>/` containing:
- `model.json`: Native XGBoost binary/tree structure (safe, non-pickle)
- `metadata.json`: Hyperparameters, training dates, seeds, feature names, and confusion matrix
- `feature_schema.json`: Complete serialized feature specification
- `preprocessor.json`: Categorical mappings and column ordering
- `metrics.json`: Precision, recall, F1, ROC-AUC, PR-AUC
- `evaluation_report.md`: Human-readable markdown evaluation report
- `MODEL_CARD.md`: Production model card documenting intended use and scientific limitations

---

## 7. Command-Line Interface (CLI)

### Train a New Model
```bash
python -m services.risk_engine.cli train \
    --input data/processed/sample_run/features.parquet \
    --model-version risk-xgboost-v001 \
    --train-ratio 0.75 \
    --include-rf
```

### Evaluate Registered Model
```bash
python -m services.risk_engine.cli evaluate \
    --model-version risk-xgboost-v001 \
    --dataset data/processed/sample_run/features.parquet \
    --threshold 0.5
```

### Run Batch Prediction from Parquet / CSV / JSON
```bash
python -m services.risk_engine.cli predict \
    --model-version risk-xgboost-v001 \
    --input data/processed/sample_run/features.parquet \
    --output predictions_output.csv
```

### Run Single-Cell Prediction from JSON String
```bash
python -m services.risk_engine.cli predict \
    --model-version risk-xgboost-v001 \
    --input '{"grid_cell_id": "cell_01", "elevation_m": 1200.0, "slope_deg": 25.0, "aspect_deg": 180.0, "fuel_type": "CONIFER_HIGH_FLAMMABILITY", "ndvi": 0.45, "ndwi": -0.1, "temperature_c": 36.5, "relative_humidity_pct": 18.0, "wind_speed_ms": 12.0, "wind_direction_deg": 270.0, "precipitation_24h_mm": 0.0, "precipitation_7d_mm": 0.0, "fwi": 38.5, "fire_count_7d": 2, "fire_count_30d": 5, "days_since_last_fire": 3, "dist_to_recent_fire_m": 450.0}'
```

### Display Model Metadata & Feature Importance
```bash
python -m services.risk_engine.cli info --model-version risk-xgboost-v001
```

---

## 8. Python Inference API

```python
from services.risk_engine.inference.loader import ModelLoader
from services.risk_engine.inference.predictor import RiskPredictor, RiskInferenceInput

# 1. Load registered model
model = ModelLoader.load_model("risk-xgboost-v001")
predictor = RiskPredictor(model)

# 2. Predict single grid cell
input_data = RiskInferenceInput(
    grid_cell_id="reg_garhwal_001_CELL_0001_0005",
    region_id="reg_garhwal_001",
    features={
        "elevation_m": 1250.0,
        "slope_deg": 18.5,
        "aspect_deg": 210.0,
        "fuel_type": "CONIFER_HIGH_FLAMMABILITY",
        "ndvi": 0.52,
        "ndwi": -0.05,
        "temperature_c": 34.0,
        "relative_humidity_pct": 22.0,
        "wind_speed_ms": 9.5,
        "wind_direction_deg": 240.0,
        "precipitation_24h_mm": 0.0,
        "precipitation_7d_mm": 2.5,
        "fwi": 32.0,
        "fire_count_7d": 1,
        "fire_count_30d": 3,
        "days_since_last_fire": 5,
        "dist_to_recent_fire_m": 850.0,
    }
)
prediction = predictor.predict_risk(input_data)
print(f"Cell: {prediction.grid_cell_id}")
print(f"Risk: {prediction.risk_class.value} (Probability: {prediction.probability})")
print(f"Forecast Window: {prediction.forecast_start} -> {prediction.forecast_end}")
```

---

## 9. Verification & Test Suite

The test suite contains 30 unit, integration, and edge-case tests:

```bash
# Run risk-engine tests
pytest services/risk-engine/tests/ -v

# Run full project backend regression test suite
pytest -v
```

Tests cover:
- Canonical schema validation, range checks, and NaN rejection
- Fuel category mapping and normalization
- Temporal train/val split chronology and zero-overlap guarantees
- XGBoost and Random Forest training, evaluation, and convergence
- Single-cell and vectorized batch inference contracts
- Native JSON serialization and registry round-trips
- Imbalanced label guards and empty dataset handling
