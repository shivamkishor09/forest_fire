# Predictive Forest Fire Risk & Spread Simulation Platform

[![Phase](https://img.shields.io/badge/Project%20Phase-Phase%2010%20Complete%20(Ready%20for%20Demo)-brightgreen.svg)](IMPLEMENTATION_PLAN.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](DEVELOPMENT.md)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](services/api)
[![React](https://img.shields.io/badge/React-18%20%2B%20TypeScript-blue.svg)](apps/web)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.4-blue.svg)](DATABASE_SCHEMA.md)
[![Tests](https://img.shields.io/badge/Tests-180%20Passed-brightgreen.svg)](docs/VALIDATION_REPORT.md)

An enterprise-grade geospatial artificial intelligence platform designed for predictive forest fire susceptibility modeling and 12-hour Cellular Automata fire spread simulation. Based on the ISRO Forest Fire Prediction Technical Blueprint and wildland fire science standards.

---

## 1. Core Capabilities

1. **24-Hour Forest Fire Susceptibility Prediction**: Daily spatial susceptibility forecasting across monitored forest regions on a standardized 500m × 500m common spatial grid.
2. **12-Hour Fire Spread Simulation**: Real-time physical/heuristic fire perimeter propagation initialized from active satellite detections or custom ignition points.
3. **Interactive GIS Dashboard**: High-performance mapping interface rendering risk choropleths, thermal hotspot markers, environmental layers, and 12-hour simulation progression.
4. **Multi-Source Data Fusion**: Harmonization of satellite observations (MODIS, VIIRS, INSAT-3D), meteorology (IMD, ERA5), vegetation/fuel indices (Sentinel-2, Landsat), and topography (CartoDEM, SRTM).
5. **Decoupled Asynchronous Processing**: Long-running simulations executed off the API thread via Celery and Redis.

---

## 2. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Leaflet / Mapbox GL JS.
- **Backend API**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, Uvicorn.
- **Spatial Storage**: PostgreSQL 16 + PostGIS 3.4 (`EPSG:4326` native geometry).
- **Asynchronous Task Processing**: Redis 7, Celery 5.
- **Data & Machine Learning Engines**: NumPy, Pandas, Scikit-learn, XGBoost (PyTorch reserved for future spatial/physics models).
- **Container Infrastructure**: Docker, Docker Compose.
- **Testing**: Pytest (Python), Vitest / React Testing Library (TypeScript).

---

## 3. Architecture Overview

The platform uses a **modular monorepo** architecture ensuring clean service ownership and strict dependency boundaries:

```
[ External Data Sources: MODIS, VIIRS, IMD, DEM ]
                       │
                       ▼
            [ Data Pipeline Service ]
       (Adapters, 500m Grid Resampling, FWI)
         │                               │
         ▼                               ▼
 [ Risk Engine (24h) ]       [ Spread Engine (12h) ]
  (XGBoost / Random Forest)    (Cellular Automata + Rothermel)
         │                               ▲
         ▼                               │ (Dispatched via Celery)
 [ PostGIS Spatial Storage ] <─── [ FastAPI Backend ]
                                         │
                                         ▼ (REST / GeoJSON)
                                 [ React GIS Client ]
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for detailed architectural blueprints and diagrams.

---

## 4. Repository Structure

```
forest-fire-platform/
├── apps/
│   └── web/                   # React + TypeScript + Vite GIS Dashboard
├── services/
│   ├── api/                   # FastAPI application & REST endpoints
│   ├── data-pipeline/         # Ingestion adapters, preprocessing, feature engineering
│   ├── risk-engine/           # 24-hour fire risk machine learning engine
│   └── spread-engine/         # 12-hour Cellular Automata fire spread simulation engine
├── packages/
│   ├── shared-types/          # Shared domain schemas & dataclasses
│   ├── geo-utils/             # GIS math, bounding boxes, 500m grid cell geometry
│   └── config/                # Environment configurations
├── database/
│   ├── migrations/            # Database schema migrations
│   ├── schema/                # PostGIS DDL initialization scripts
│   └── seed/                  # Reference regions and sample seed data
├── data/                      # Raw, processed, and sample GIS data directories
├── models/                    # Risk model weights and spread configurations
├── docker-compose.yml         # Local container orchestration
├── .env.example               # Environment variable templates
├── ARCHITECTURE.md            # System architecture specification
├── API_CONTRACT.md            # OpenAPI REST endpoint contracts
├── DATA_CONTRACTS.md          # Canonical domain contracts
├── DATABASE_SCHEMA.md         # PostGIS relational database schema
├── DEVELOPMENT.md             # Developer workflow & setup guide
└── IMPLEMENTATION_PLAN.md     # 10-Phase project implementation roadmap
```

---

## 5. Quickstart & Local Setup

### Option A: Using Docker Compose (Recommended)

1. Clone and enter the repository:
   ```bash
   cd forest_fire
   ```
2. Create your environment configuration:
   ```bash
   cp .env.example .env
   ```
3. Start all services:
   ```bash
   docker compose up --build
   ```
4. Access the applications:
   - GIS Dashboard: `http://localhost:5173`
   - FastAPI Documentation: `http://localhost:8000/docs`
   - API Health Check: `http://localhost:8000/api/v1/health`

### Option B: Local Native Setup

#### 1. Backend (FastAPI):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt
uvicorn services.api.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend (React + Vite):
```bash
cd apps/web
npm install
npm run dev
```

---

## 6. Running Automated Tests

### Python Test Suite (API, Data Pipeline, Risk Engine, Spread Engine):
```bash
source .venv/bin/activate
pytest
```

### Frontend Test Suite & Production Build:
```bash
cd apps/web
npm test
npm run build
```

---

## 7. Documentation & Operational Reference Index

### Architecture & Contracts
- [System Architecture Specification](ARCHITECTURE.md)
- [REST API Contract](API_CONTRACT.md)
- [Shared Domain Data Contracts](DATA_CONTRACTS.md)
- [PostGIS Database Schema](DATABASE_SCHEMA.md)
- [Developer & Contribution Guide](DEVELOPMENT.md)
- [10-Phase Roadmap & Milestones](IMPLEMENTATION_PLAN.md)
- [Project Status Matrix](docs/PROJECT_STATUS.md)

### Release, Demo & Deployment
- [End-to-End System Demo Walkthrough](DEMO.md)
- [Project Changelog](CHANGELOG.md)
- [Production Deployment Runbook](docs/DEPLOYMENT.md)
- [Release Readiness Checklist](docs/RELEASE_CHECKLIST.md)
- [Production Environment Template](.env.production.example)

### Model Governance, Verification & Security
- [Spread Engine Model Card (`spread-ca-v001`)](docs/SPREAD_ENGINE_CARD.md)
- [Data Pipeline Card](docs/DATA_CARD.md)
- [Validation & Verification Report](docs/VALIDATION_REPORT.md)
- [Performance & Benchmark Report](docs/PERFORMANCE_REPORT.md)
- [Security Review & Vulnerability Assessment](docs/SECURITY_REVIEW.md)
- [Platform Limitations & Constraints](docs/LIMITATIONS.md)
- [Known Issues & Operational Guidance](docs/KNOWN_ISSUES.md)
- [Future Work & Research Roadmap](docs/FUTURE_WORK.md)

<img width="1920" height="1020" alt="Screenshot 2026-10-10 183712" src="https://github.com/user-attachments/assets/cf40de9e-001c-43d6-8a24-da8705841bbd" />
<img width="1920" height="1020" alt="Screenshot 2026-10-10 183639" src="https://github.com/user-attachments/assets/ca95748b-d234-48c0-a01d-b8eab7e6c7db" />
