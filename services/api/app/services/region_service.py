"""Service layer orchestrating region business logic and GeoJSON transforms."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from shapely.geometry import shape

from ..repositories.region_repository import RegionRepository
from ..models.region import Region
from ..schemas.region import RegionListItem, RegionListResponse, RegionDetailResponse
from ..schemas.geojson import GeoJSONPoint, GeoJSONFeature, to_geojson_geometry
from ..core.exceptions import ResourceNotFoundException

# Fallback development reference regions
SAMPLE_REGIONS = [
    {
        "id": "1fa85f64-5717-4562-b3fc-2c963f66afa1",
        "code": "ALL_INDIA_TERRAIN",
        "alias": "india-all",
        "name": "All India (Free Map Exploration)",
        "state": "Pan-India",
        "area_sqkm": 3287263.0,
        "centroid": [78.9629, 22.5937],
        "boundary": [
            [[68.0, 7.0], [97.5, 7.0], [97.5, 37.5], [68.0, 37.5], [68.0, 7.0]]
        ],
        "total_cells": 13149052,
    },
    {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "code": "UTTARAKHAND_GARHWAL",
        "alias": "reg-01",
        "name": "Garhwal Forest Division",
        "state": "Uttarakhand",
        "area_sqkm": 2840.5,
        "centroid": [78.7842, 30.2241],
        "boundary": [
            [[78.50, 30.10], [79.10, 30.10], [79.10, 30.40], [78.50, 30.40], [78.50, 30.10]]
        ],
        "total_cells": 11362,
    },
    {
        "id": "7ca85f64-5717-4562-b3fc-2c963f66afa7",
        "code": "WESTERN_GHATS_WAYANAD",
        "alias": "reg-02",
        "name": "Wayanad Wildlife Sanctuary",
        "state": "Kerala",
        "area_sqkm": 344.4,
        "centroid": [76.2418, 11.6854],
        "boundary": [
            [[76.15, 11.60], [76.35, 11.60], [76.35, 11.80], [76.15, 11.80], [76.15, 11.60]]
        ],
        "total_cells": 1378,
    },
    {
        "id": "4da85f64-5717-4562-b3fc-2c963f66afa2",
        "code": "UTTARAKHAND_CORBETT",
        "alias": "reg-03",
        "name": "Jim Corbett National Park",
        "state": "Uttarakhand",
        "area_sqkm": 1288.3,
        "centroid": [78.9500, 29.5300],
        "boundary": [
            [[78.70, 29.35], [79.20, 29.35], [79.20, 29.70], [78.70, 29.70], [78.70, 29.35]]
        ],
        "total_cells": 5153,
    },
    {
        "id": "5ea85f64-5717-4562-b3fc-2c963f66afa3",
        "code": "KARNATAKA_BANDIPUR",
        "alias": "reg-04",
        "name": "Bandipur National Park",
        "state": "Karnataka",
        "area_sqkm": 874.2,
        "centroid": [76.6300, 11.6700],
        "boundary": [
            [[76.45, 11.50], [76.85, 11.50], [76.85, 11.85], [76.45, 11.85], [76.45, 11.50]]
        ],
        "total_cells": 3496,
    },
    {
        "id": "6fa85f64-5717-4562-b3fc-2c963f66afa4",
        "code": "MP_KANHA",
        "alias": "reg-05",
        "name": "Kanha Tiger Reserve",
        "state": "Madhya Pradesh",
        "area_sqkm": 2074.0,
        "centroid": [80.6100, 22.3300],
        "boundary": [
            [[80.35, 22.10], [80.90, 22.10], [80.90, 22.55], [80.35, 22.55], [80.35, 22.10]]
        ],
        "total_cells": 8296,
    },
    {
        "id": "8ba85f64-5717-4562-b3fc-2c963f66afa5",
        "code": "ASSAM_KAZIRANGA",
        "alias": "reg-06",
        "name": "Kaziranga National Park",
        "state": "Assam",
        "area_sqkm": 1085.5,
        "centroid": [93.1700, 26.6500],
        "boundary": [
            [[92.90, 26.50], [93.45, 26.50], [93.45, 26.80], [92.90, 26.80], [92.90, 26.50]]
        ],
        "total_cells": 4342,
    },
    {
        "id": "9ca85f64-5717-4562-b3fc-2c963f66afa8",
        "code": "ODISHA_SIMILIPAL",
        "alias": "reg-07",
        "name": "Similipal National Park",
        "state": "Odisha",
        "area_sqkm": 2750.0,
        "centroid": [86.3500, 21.8500],
        "boundary": [
            [[86.05, 21.50], [86.65, 21.50], [86.65, 22.20], [86.05, 22.20], [86.05, 21.50]]
        ],
        "total_cells": 11000,
    },
]


class RegionService:
    """Service managing regional operations."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.repo = RegionRepository(db) if db is not None else None

    def list_regions(self, state: Optional[str] = None, limit: int = 50, offset: int = 0) -> RegionListResponse:
        if self.repo is not None:
            try:
                db_regions = self.repo.list_regions(state=state, limit=limit, offset=offset)
                if db_regions:
                    total_count = self.repo.count_regions(state=state)
                    items = []
                    for reg in db_regions:
                        geom = to_geojson_geometry(reg.boundary)
                        # Compute centroid from geometry coordinates
                        coords = geom.get("coordinates", [[]])[0]
                        if coords:
                            mean_lon = sum(c[0] for c in coords) / len(coords)
                            mean_lat = sum(c[1] for c in coords) / len(coords)
                        else:
                            mean_lon, mean_lat = 78.0, 30.0

                        items.append(
                            RegionListItem(
                                id=str(reg.id),
                                code=reg.code,
                                name=reg.name,
                                state=reg.state,
                                area_sqkm=float(reg.area_sqkm),
                                centroid=GeoJSONPoint(coordinates=[round(mean_lon, 4), round(mean_lat, 4)]),
                                created_at=reg.created_at.isoformat() if reg.created_at else None,
                            )
                        )
                    return RegionListResponse(count=total_count, results=items)
            except Exception:
                # Fallback to sample reference set if database tables not yet seeded
                pass

        # Reference data fallback
        filtered = SAMPLE_REGIONS
        if state:
            filtered = [r for r in filtered if r["state"].lower() == state.lower()]

        items = [
            RegionListItem(
                id=r["id"],
                code=r["code"],
                name=r["name"],
                state=r["state"],
                area_sqkm=r["area_sqkm"],
                centroid=GeoJSONPoint(coordinates=r["centroid"]),
                created_at="2026-01-15T00:00:00Z",
            )
            for r in filtered[offset : offset + limit]
        ]
        return RegionListResponse(count=len(filtered), results=items)

    def get_region(self, region_id: str) -> RegionDetailResponse:
        if self.repo is not None:
            try:
                reg = self.repo.get_by_id_or_code(region_id)
                if reg is not None:
                    boundary_geom = to_geojson_geometry(reg.boundary)
                    cell_count = self.repo.count_grid_cells(reg.id) or int(float(reg.area_sqkm) * 4)
                    return RegionDetailResponse(
                        id=str(reg.id),
                        code=reg.code,
                        name=reg.name,
                        state=reg.state,
                        area_sqkm=float(reg.area_sqkm),
                        boundary=GeoJSONFeature(
                            id=str(reg.id),
                            geometry=boundary_geom,
                            properties={"code": reg.code, "name": reg.name, "state": reg.state},
                        ),
                        grid_resolution_meters=500,
                        total_cells=cell_count,
                    )
            except Exception:
                pass

        # Reference data fallback
        match = next(
            (r for r in SAMPLE_REGIONS if r["id"] == region_id or r["code"] == region_id or r.get("alias") == region_id),
            None,
        )
        if not match:
            raise ResourceNotFoundException(f"Region '{region_id}' was not found.")

        return RegionDetailResponse(
            id=match["id"],
            code=match["code"],
            name=match["name"],
            state=match["state"],
            area_sqkm=match["area_sqkm"],
            boundary=GeoJSONFeature(
                id=match["id"],
                geometry={"type": "Polygon", "coordinates": match["boundary"]},
                properties={"code": match["code"], "name": match["name"]},
            ),
            grid_resolution_meters=500,
            total_cells=match["total_cells"],
        )
