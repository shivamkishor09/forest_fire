# Environmental Data Ingestion & Preprocessing Pipeline (Phase 4)

This service provides the standardized data extraction, spatial resampling, temporal compositing, and feature engineering foundation for the **Predictive Forest Fire Risk & Spread Simulation Platform**.

It prepares model-ready feature records aligned to a common **500m × 500m spatial grid** in WGS 84 (EPSG:4326) without lookahead leakage.

---

## 1. Architecture Overview

```
Raw Sources (MODIS, VIIRS, INSAT, ERA5, IMD, Sentinel-2, CartoDEM)
                            ↓
                     Source Adapters
  (Parsing, coordinate normalization, unit conversions, validation)
                            ↓
               Canonical Observation Models
 (CanonicalFireObservation, CanonicalWeatherObservation, CanonicalVegetationObservation, CanonicalTerrainObservation)
                            ↓
               Common 500m × 500m Spatial Grid
       (Metric UTM projection → regular tessellation → EPSG:4326)
                            ↓
               Preprocessing & Alignment
   - Spatial Aligner (IDW interpolation & nearest neighbor)
   - Temporal Aligner (Strict anti-leakage guards: T_obs <= T_ref)
   - Missing Data Handler (Traceable imputation & quality auditing)
                            ↓
                   Feature Engineering
   - Topography: Aspect sin/cos, elevation, slope gradient
   - Meteorology: U/V orthogonal wind vectors, temperature, RH, rainfall
   - Vegetation: Spectral NDVI, NDWI, Indian forest fuel categorization
   - Fire Weather: Complete Canadian Fire Weather Index (FFMC, ISI, DMC, DC, BUI, FWI)
   - Historical Fire: Spatial proximity & temporal frequencies (7d, 30d, days since fire)
   - Target Labeler: Binary 24-hour future fire occurrence (T_ref < T_fire <= T_ref + 24h)
                            ↓
                   Outputs & Provenance
   - Model-Ready Datasets (features.csv, features.parquet)
   - Spatial Boundary GeoJSON (grid_500m.geojson)
   - Reproducible Data Manifest (manifest.json)
   - Automated Data Quality Report (quality_report.json, quality_report.md)
```

---

## 2. Supported Data Sources & Adapters

| Category | Source Provider | Products / Instruments | Adapter Class |
|---|---|---|---|
| **Active Fire** | NASA FIRMS | MODIS MCD14DL (1km) | `ModisFireAdapter` |
| **Active Fire** | NASA / NOAA | VIIRS VNP14IMGTDL (375m I-band) | `ViirsFireAdapter` |
| **Active Fire** | ISRO | INSAT-3D / 3DR Imager (4km) | `InsatFireAdapter` |
| **Meteorology** | ECMWF | ERA5 Reanalysis / Forecast | `Era5WeatherAdapter` |
| **Meteorology** | IMD | Gridded 0.25° & AWS Stations | `ImdWeatherAdapter` |
| **Vegetation / Fuel** | ESA Coprenicus | Sentinel-2 MSI L2A (10-20m) | `SentinelVegetationAdapter` |
| **Vegetation / Fuel** | USGS / NASA | Landsat-8/9 OLI (30m) | `LandsatVegetationAdapter` |
| **Vegetation / Fuel** | ISRO NRSC | Bhuvan LULC 1:50k & Fuel Types | `BhuvanVegetationAdapter` |
| **Topography** | NASA | SRTM 1 Arc-Second (30m DEM) | `SrtmTerrainAdapter` |
| **Topography** | ISRO | CartoDEM Version 3R (30m DEM) | `CartoDemTerrainAdapter` |

---

## 3. Strict Anti-Leakage Protocol

A central design requirement is preventing **temporal target leakage**:

1. **Prediction Reference Time ($T_{ref}$):** Defines the exact forecast issuance timestamp (e.g., `2026-05-15 00:00:00 UTC`).
2. **Feature Records ($T_{obs} \le T_{ref}$):**
   - Observations occurring after $T_{ref}$ are strictly blocked from entering feature space.
   - If `strict_anti_leakage=True`, encountering any record with $T_{obs} > T_{ref}$ raises `DataLeakageError`.
   - In non-strict mode, future records are discarded with logged audit warnings.
3. **Target Label ($T_{ref} < T_{fire} \le T_{ref} + 24\text{h}$):**
   - Evaluates fire detections strictly occurring inside the subsequent 24-hour observation horizon.
   - Kept completely separate from feature calculations.

---

## 4. 500m Grid & Spatial Reference System

- **Metric Square Projection:** To avoid distortion from geographic degrees, grid tessellation is computed in the region's local UTM metric projection (e.g. `EPSG:32644` for Uttarakhand / Garhwal, `EPSG:32643` for Western Ghats).
- **Interchange & Database CRS:** All polygons and centroids are converted back to canonical `EPSG:4326` WGS 84.
- **Deterministic Cell Codes:** Standardized format `CELL_RRRR_CCCC` (e.g., `CELL_0012_0034`).

---

## 5. Canadian Fire Weather Index (FWI) Implementation

The `FwiCalculator` implements the full standard Canadian Forest Fire Weather Index equations tailored for Indian sub-tropical forest belts:

- **FFMC (Fine Fuel Moisture Code):** Relative moisture of surface forest litter (0–101 scale).
- **DMC (Duff Moisture Code):** Loosely compacted organic layer moisture.
- **DC (Drought Code):** Deep compact organic layers and seasonal drought.
- **ISI (Initial Spread Index):** Rate of spread combining wind velocity and FFMC.
- **BUI (Buildup Index):** Total fuel availability combining DMC and DC.
- **FWI (Fire Weather Index):** Composite indicator of frontal fireline intensity.

---

## 6. CLI Usage

Run the complete pipeline end-to-end on sample data:

```bash
# Run pipeline with sample Garhwal region data and generate 24h future labels
python -m services.data_pipeline.cli run \
    --region-file data/sample/region_garhwal.geojson \
    --reference-date 2026-05-15 \
    --generate-target \
    --output-dir data/processed/sample_run

# Generate standalone 500m grid GeoJSON for a region boundary
python -m services.data_pipeline.cli generate-grid \
    --region-file data/sample/region_garhwal.geojson \
    --output-file data/processed/grid_500m.geojson \
    --resolution 500
```

---

## 7. Python API Example

```python
from datetime import datetime, timezone
from services.data_pipeline.adapters.base import BoundingBox
from services.data_pipeline.adapters.fire.modis import ModisFireAdapter
from services.data_pipeline.grid.generator import GridGenerator
from services.data_pipeline.features.pipeline import FeaturePipeline

# 1. Generate 500m grid
bbox = BoundingBox(min_lon=78.6, min_lat=30.1, max_lon=78.85, max_lat=30.35)
cells = GridGenerator(resolution_meters=500).generate_grid_for_bbox(bbox, region_id="reg_garhwal")

# 2. Ingest observations
fires = ModisFireAdapter().parse_csv("data/sample/active_fires_sample.csv")

# 3. Process features
ref_time = datetime(2026, 5, 15, 0, 0, 0, tzinfo=timezone.utc)
pipeline = FeaturePipeline(strict_anti_leakage=False)
records, quality_report = pipeline.process(
    cells=cells,
    reference_time=ref_time,
    fire_observations=fires,
    weather_observations=[],
    vegetation_observations=[],
    terrain_observations=[],
    generate_target=True,
)

# 4. Convert to pandas DataFrame
df = pipeline.records_to_dataframe(records)
print(df.head())
```
