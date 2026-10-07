# Risk Model Evaluation Report: `risk-xgboost-v002`

- **Model Name:** risk-xgboost
- **Algorithm:** XGBoost + CalibratedClassifierCV
- **Created At:** 2026-10-07T01:47:43.962411+00:00
- **Dataset Version:** multiseason_v2
- **Random Seed:** 42

## 1. Dataset & Temporal Split

- **Training Period:** 2022-05-01 to 2023-05-23
- **Validation Period:** 2024-03-01 to 2024-05-25
- **Total Evaluated Samples:** 1227
- **Positive Fire Samples:** 72 (5.87%)
- **Negative Non-Fire Samples:** 1155
- **Class Imbalance Strategy:** `controlled_negative_sampling_and_scale_pos_weight` (scale_pos_weight = 7.98)

## 2. Classification Performance Metrics

| Metric | Value |
|---|---|
| **Accuracy** | 0.9144 |
| **Precision** | 0.2537 |
| **Recall** | 0.2361 |
| **F1-Score** | 0.2446 |
| **ROC-AUC** | 0.7656 |
| **PR-AUC** | 0.1761 |

### Confusion Matrix

| | Predicted Negative (0) | Predicted Positive (1) |
|---|---|---|
| **Actual Negative (0)** | True Negatives: **1105** | False Positives: **50** |
| **Actual Positive (1)** | False Negatives: **55** | True Positives: **17** |

## 3. Top Feature Importance (Descriptive)

| Rank | Feature Name | Relative Importance |
|---|---|---|
| 1 | `dist_to_recent_fire_m` | 0.1264 |
| 2 | `aspect_deg` | 0.0740 |
| 3 | `aspect_sin` | 0.0644 |
| 4 | `aspect_cos` | 0.0631 |
| 5 | `elevation_m` | 0.0577 |
| 6 | `fire_count_30d` | 0.0551 |
| 7 | `days_since_last_fire` | 0.0522 |
| 8 | `wind_u_ms` | 0.0466 |
| 9 | `precipitation_24h_mm` | 0.0453 |
| 10 | `ndwi` | 0.0436 |

> **Note on Feature Importance:** Importance values indicate relative predictive split utility within the trained tree ensemble and do **not** imply direct causality.

## 4. Hyperparameters

```json
{
  "n_estimators": 150,
  "max_depth": 5,
  "learning_rate": 0.05,
  "subsample": 0.8,
  "colsample_bytree": 0.8,
  "scale_pos_weight": 7.98,
  "calibration_method": "isotonic",
  "operational_threshold": 0.1
}
```

## 5. Known Scientific & Practical Limitations

1. **Baseline Tabular Model:** Does not model spatio-temporal graph propagation or deep visual raster contexts (deferred to future spatial research).
2. **Threshold Sensitivity:** Probability classifications rely on standard engineering thresholds [0.25, 0.50, 0.75]; operational field thresholds must be calibrated with local forest division SOPs.
3. **Resolution:** Predictions operate at 500m × 500m spatial grid partition. Sub-pixel micro-topographical variations are aggregated.
4. **Sample Data Disclaimer:** If trained on development sample data, metrics demonstrate software correctness and pipeline reproducibility rather than operational field efficacy.
