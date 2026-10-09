# Model Card: risk-xgboost-v002

## Model Details
- **Model Name:** risk-xgboost
- **Model Version:** risk-xgboost-v002
- **Architecture:** Gradient Boosted Decision Trees (XGBoost + CalibratedClassifierCV)
- **Release Date:** 2026-10-07T01:47:43.962411+00:00
- **Dataset Lineage:** `multiseason_v2`

## Intended Use
- **Primary Use:** 24-hour predictive susceptibility scoring for discrete 500m × 500m forest grid cells.
- **Users:** Forest department command officers, fire prevention planners, GIS analysts.
- **Out of Scope:** Active real-time wildfire propagation / flame front spread simulation (handled by the Cellular Automata engine in Phase 7).

## Factors & Precursor Features
- Topography: Elevation (m), slope (deg), continuous cyclical aspect sin/cos.
- Meteorology: Temperature (°C), relative humidity (%), wind speed (m/s), orthogonal U/V vectors, 24h & 7d precipitation.
- Vegetation: Sentinel-2 / Landsat NDVI, NDWI canopy moisture, standardized Indian fuel classification.
- Fire Weather: Canadian Fire Weather Index (FWI) composite.
- Historical Fire: 7-day and 30-day fire frequencies, spatial proximity to recent fires, days since last fire.

## Performance & Evaluation
- **Accuracy:** 0.9144
- **Recall:** 0.2361
- **Precision:** 0.2537
- **F1-Score:** 0.2446
- **ROC-AUC:** 0.7656

## Ethical & Safety Considerations
- Model output represents estimated susceptibility likelihood; it should complement rather than supersede human ground ranger patrols.
- High-risk alerts must be verified against satellite thermal detections and meteorological warnings.
