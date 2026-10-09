"""Service layer orchestrating fire spread simulation sessions, validation, and Celery dispatch."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from shapely.geometry import Point, shape, Polygon

from ..repositories.simulation_repository import SimulationRepository
from ..repositories.region_repository import RegionRepository
from ..models.simulation import Simulation
from ..models.simulation_step import SimulationStep
from ..schemas.simulation import (
    SimulationCreateRequest,
    SimulationCreateResponse,
    SimulationStatusResponse,
    SimulationTimelineResponse,
    SimulationTimestepDetailResponse,
    SimulationTimestepItem,
    SimulationMetrics,
)
from ..schemas.geojson import GeoJSONPoint, GeoJSONFeature, GeoJSONFeatureCollection, to_geojson_geometry
from ..core.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    IgnitionOutsideRegionException,
)
from ..core.logging import logger
from ..core.celery_app import check_celery_broker
from ..tasks.simulation_tasks import (
    run_fire_spread_simulation,
    SIMULATION_CACHE,
)
from ..core.database import check_db_connection
from ..services.region_service import SAMPLE_REGIONS


class SimulationService:
    """Service orchestrating fire spread simulation lifecycle and validation."""

    def __init__(self, db: Optional[Session] = None):
        self.is_db_connected = check_db_connection() == "connected"
        self.db = db if self.is_db_connected else None
        self.repo = SimulationRepository(db) if (self.is_db_connected and db is not None) else None
        self.region_repo = RegionRepository(db) if (self.is_db_connected and db is not None) else None

    def _get_region_geometry(self, region_id_or_code: str) -> Optional[Any]:
        """Retrieve Shapely geometry for the specified region."""
        if self.is_db_connected and self.region_repo is not None:
            try:
                db_region = self.region_repo.get_by_id_or_code(region_id_or_code)
                if db_region is not None and db_region.boundary is not None:
                    geom_dict = to_geojson_geometry(db_region.boundary)
                    return shape(geom_dict)
            except Exception as e:
                logger.debug(f"Could not load region geometry from DB: {e}")

        # Check sample regions
        for r in SAMPLE_REGIONS:
            if r["id"] == region_id_or_code or r["code"] == region_id_or_code:
                coords = r["boundary"]
                return Polygon(coords[0])

        return None

    def create_simulation(self, request: SimulationCreateRequest) -> SimulationCreateResponse:
        """
        Validate simulation request parameters, verify ignition lies within region boundaries,
        persist QUEUED session, and dispatch to Celery background worker.
        """
        # Validate coordinates
        ign_point = request.ignition_point
        lat = ign_point.latitude
        lon = ign_point.longitude

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            raise ValidationException(f"Invalid ignition coordinates: ({lat}, {lon})")

        # Validate duration
        duration = request.duration_hours or 12
        if not (1 <= duration <= 12):
            raise ValidationException(f"Duration must be between 1 and 12 hours (received {duration}).")

        # Verify region exists and validate ignition location inside region boundary
        region_geom = self._get_region_geometry(request.region_id)
        if region_geom is None and request.region_id not in ("1fa85f64-5717-4562-b3fc-2c963f66afa1", "ALL_INDIA_TERRAIN", "india-all"):
            raise ResourceNotFoundException(f"Region '{request.region_id}' not found.")

        point = Point(lon, lat)
        is_pan_india = request.region_id in ("1fa85f64-5717-4562-b3fc-2c963f66afa1", "ALL_INDIA_TERRAIN", "india-all")
        if region_geom is not None and not is_pan_india:
            if not (region_geom.contains(point) or region_geom.buffer(1e-4).contains(point)):
                raise IgnitionOutsideRegionException(
                    f"Ignition coordinate ({lat:.4f}, {lon:.4f}) lies outside the boundary of region '{request.region_id}'."
                )

        sim_id = uuid.uuid4()
        now_dt = datetime.now(timezone.utc)

        # Parse region UUID
        try:
            reg_uuid = uuid.UUID(request.region_id)
        except (ValueError, AttributeError):
            reg_uuid = uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")

        # Persist simulation session in DB as QUEUED
        if self.is_db_connected and self.repo is not None:
            sim_record = Simulation(
                id=sim_id,
                region_id=reg_uuid,
                ignition_location=WKTElement(f"POINT({lon} {lat})", srid=4326),
                ignition_time=now_dt,
                duration_hours=duration,
                status="QUEUED",
                total_area_burned_ha=0.0,
                model_version="spread-ca-v001",
            )
            try:
                self.repo.add(sim_record)
                self.repo.commit()
            except Exception as e:
                self.repo.rollback()
                logger.warning(f"Could not persist simulation record (operating in detached mode): {e}")

        # Assemble Celery task payload
        weather = request.weather_scenario
        task_payload = {
            "region_id": str(reg_uuid),
            "ignition_lat": lat,
            "ignition_lon": lon,
            "duration_hours": duration,
            "wind_speed_ms": weather.wind_speed_ms if weather else 7.5,
            "wind_direction_deg": weather.wind_direction_deg if weather else 225.0,
            "fuel_type": request.fuel_type or "CONIFER_HIGH_FLAMMABILITY",
            "slope_deg": request.slope_deg or 0.0,
            "aspect_deg": request.aspect_deg or 180.0,
        }

        # Dispatch to Celery background worker
        broker_status = check_celery_broker()
        if broker_status == "connected":
            try:
                run_fire_spread_simulation.delay(str(sim_id), task_payload)
                logger.info(f"Dispatched simulation task to Celery broker for job: {sim_id}")
            except Exception as e:
                logger.error(f"Failed to enqueue Celery task: {e}")
                if self.is_db_connected and self.repo is not None:
                    self.repo.update_simulation_status(sim_id, status="FAILED")
                    self.db.commit()
                raise e
        else:
            # Asynchronous background thread when Redis is offline (detached dev / test mode)
            import threading
            logger.info(f"Celery broker unreachable; executing simulation task via background thread for job: {sim_id}")
            worker_thread = threading.Thread(
                target=run_fire_spread_simulation,
                args=(str(sim_id), task_payload),
                daemon=True,
            )
            worker_thread.start()
            worker_thread.join(timeout=2.0)

        return SimulationCreateResponse(
            simulation_id=str(sim_id),
            status="QUEUED",
            created_at=now_dt.isoformat(),
            duration_hours=duration,
            poll_url=f"/api/v1/simulations/{sim_id}",
        )

    def get_simulation_status(self, simulation_id: str) -> SimulationStatusResponse:
        """Query current lifecycle status and summary metrics for a simulation job."""
        # 1. Try DB
        if self.is_db_connected and self.repo is not None:
            try:
                sim = self.repo.get_by_id(simulation_id)
                if sim is not None:
                    steps = self.repo.get_steps(simulation_id)
                    completed_count = len(steps)
                    total_count = sim.duration_hours + 1  # Hour 0 to duration
                    progress = 100.0 if sim.status == "COMPLETED" else round((completed_count / max(1, total_count)) * 100.0, 1)

                    ignition_geom = to_geojson_geometry(sim.ignition_location)
                    coords = ignition_geom.get("coordinates", [78.7523, 30.2104])

                    peak_vel = max((float(s.spread_velocity_kmh) for s in steps), default=0.0)
                    dominant_dir = float(steps[-1].spread_direction_deg) if steps else 0.0

                    return SimulationStatusResponse(
                        simulation_id=str(sim.id),
                        status=sim.status,
                        progress_pct=progress,
                        duration_hours=sim.duration_hours,
                        created_at=sim.created_at.isoformat(),
                        completed_at=sim.completed_at.isoformat() if sim.completed_at else None,
                        ignition_point=GeoJSONPoint(coordinates=coords),
                        metrics=SimulationMetrics(
                            total_area_burned_ha=float(sim.total_area_burned_ha),
                            peak_spread_velocity_kmh=peak_vel,
                            dominant_spread_direction_deg=dominant_dir,
                        ),
                        engine_version=sim.model_version or "spread-ca-v001",
                        completed_steps=completed_count,
                        total_steps=total_count,
                    )
            except Exception as e:
                logger.debug(f"DB lookup failed for simulation {simulation_id}: {e}")

        # 2. Try in-memory cache
        if simulation_id in SIMULATION_CACHE:
            cached = SIMULATION_CACHE[simulation_id]
            timesteps = cached.get("timesteps", [])
            total_steps = cached["duration_hours"] + 1
            completed_steps = len(timesteps)
            progress = 100.0 if cached["status"] == "COMPLETED" else round((completed_steps / max(1, total_steps)) * 100.0, 1)

            coords = [cached["ignition"]["longitude"], cached["ignition"]["latitude"]]
            return SimulationStatusResponse(
                simulation_id=simulation_id,
                status=cached["status"],
                progress_pct=progress,
                duration_hours=cached["duration_hours"],
                created_at=cached["created_at"],
                completed_at=cached["completed_at"],
                ignition_point=GeoJSONPoint(coordinates=coords),
                metrics=SimulationMetrics(
                    total_area_burned_ha=float(cached["total_area_burned_ha"]),
                    peak_spread_velocity_kmh=float(cached["peak_spread_velocity_kmh"]),
                    dominant_spread_direction_deg=float(cached["dominant_spread_direction_deg"]),
                ),
                engine_version=cached["engine_version"],
                completed_steps=completed_steps,
                total_steps=total_steps,
                error_message=cached.get("error"),
            )

        raise ResourceNotFoundException(f"Simulation job '{simulation_id}' not found.")

    def get_simulation_timeline(self, simulation_id: str) -> SimulationTimelineResponse:
        """Retrieve hourly progression metrics for all timesteps."""
        # 1. Try DB
        if self.is_db_connected and self.repo is not None:
            try:
                sim = self.repo.get_by_id(simulation_id)
                if sim is not None:
                    db_steps = self.repo.get_steps(simulation_id)
                    timeline_items = [
                        SimulationTimestepItem(
                            step_hour=step.step_hour,
                            burned_area_ha=float(step.burned_area_ha),
                            spread_velocity_kmh=float(step.spread_velocity_kmh),
                            spread_direction_deg=float(step.spread_direction_deg),
                            intensity_mw=float(step.intensity_mw),
                        )
                        for step in db_steps
                    ]
                    return SimulationTimelineResponse(
                        simulation_id=str(sim.id),
                        total_steps=len(timeline_items),
                        timeline=timeline_items,
                    )
            except Exception as e:
                logger.debug(f"DB steps lookup failed for {simulation_id}: {e}")

        # 2. Try in-memory cache
        if simulation_id in SIMULATION_CACHE:
            cached = SIMULATION_CACHE[simulation_id]
            timeline_items = [
                SimulationTimestepItem(
                    step_hour=item["step_hour"],
                    burned_area_ha=item["burned_area_ha"],
                    spread_velocity_kmh=item["spread_velocity_kmh"],
                    spread_direction_deg=item["spread_direction_deg"],
                    intensity_mw=item["intensity_mw"],
                )
                for item in cached.get("timesteps", [])
            ]
            return SimulationTimelineResponse(
                simulation_id=simulation_id,
                total_steps=len(timeline_items),
                timeline=timeline_items,
            )

        raise ResourceNotFoundException(f"Simulation '{simulation_id}' not found.")

    def get_simulation_timestep(self, simulation_id: str, hour: int) -> SimulationTimestepDetailResponse:
        """Retrieve detailed GeoJSON boundary perimeter for a specific hour."""
        if not (0 <= hour <= 12):
            raise ValidationException(f"Timestep hour must be between 0 and 12 (received {hour}).")

        # 1. Try DB
        if self.is_db_connected and self.repo is not None:
            try:
                step = self.repo.get_step(simulation_id, hour)
                if step is not None:
                    geom_dict = to_geojson_geometry(step.perimeter_geom)
                    return SimulationTimestepDetailResponse(
                        simulation_id=str(simulation_id),
                        step_hour=hour,
                        metrics=SimulationTimestepItem(
                            step_hour=hour,
                            burned_area_ha=float(step.burned_area_ha),
                            spread_velocity_kmh=float(step.spread_velocity_kmh),
                            spread_direction_deg=float(step.spread_direction_deg),
                            intensity_mw=float(step.intensity_mw),
                        ),
                        perimeter=GeoJSONFeature(
                            id=f"sim-{simulation_id}-step-{hour}",
                            geometry=geom_dict,
                            properties={
                                "step_hour": hour,
                                "step_number": hour,
                                "elapsed_minutes": hour * 60,
                                "burned_area_ha": float(step.burned_area_ha),
                                "cumulative_burned_area_ha": float(step.burned_area_ha),
                                "spread_velocity_kmh": float(step.spread_velocity_kmh),
                                "spread_direction_deg": float(step.spread_direction_deg),
                                "intensity_mw": float(step.intensity_mw),
                            },
                        ),
                    )
            except Exception as e:
                logger.debug(f"DB step lookup failed for {simulation_id} hour {hour}: {e}")

        # 2. Try in-memory cache
        if simulation_id in SIMULATION_CACHE:
            cached = SIMULATION_CACHE[simulation_id]
            features = cached.get("steps_features", [])
            for feat in features:
                if feat["properties"]["step_hour"] == hour:
                    props = feat["properties"]
                    return SimulationTimestepDetailResponse(
                        simulation_id=simulation_id,
                        step_hour=hour,
                        metrics=SimulationTimestepItem(
                            step_hour=hour,
                            burned_area_ha=props["burned_area_ha"],
                            spread_velocity_kmh=props["spread_velocity_kmh"],
                            spread_direction_deg=props["spread_direction_deg"],
                            intensity_mw=props["intensity_mw"],
                        ),
                        perimeter=GeoJSONFeature(
                            id=feat.get("id", f"sim-{simulation_id}-step-{hour}"),
                            geometry=feat["geometry"],
                            properties=props,
                        ),
                    )

        raise ResourceNotFoundException(f"Timestep {hour} for simulation '{simulation_id}' not found.")

    def get_simulation_steps_collection(self, simulation_id: str) -> GeoJSONFeatureCollection:
        """Retrieve all timesteps as a GeoJSON FeatureCollection."""
        # 1. Try DB
        if self.is_db_connected and self.repo is not None:
            try:
                db_steps = self.repo.get_steps(simulation_id)
                if db_steps:
                    features = []
                    for s in db_steps:
                        geom_dict = to_geojson_geometry(s.perimeter_geom)
                        features.append(
                            GeoJSONFeature(
                                id=f"sim-{simulation_id}-step-{s.step_hour}",
                                geometry=geom_dict,
                                properties={
                                    "step_hour": s.step_hour,
                                    "step_number": s.step_hour,
                                    "elapsed_minutes": s.step_hour * 60,
                                    "burned_area_ha": float(s.burned_area_ha),
                                    "cumulative_burned_area_ha": float(s.burned_area_ha),
                                    "spread_velocity_kmh": float(s.spread_velocity_kmh),
                                    "spread_direction_deg": float(s.spread_direction_deg),
                                    "intensity_mw": float(s.intensity_mw),
                                },
                            )
                        )
                    return GeoJSONFeatureCollection(
                        type="FeatureCollection",
                        features=features,
                        properties={"simulation_id": str(simulation_id), "total_steps": len(features)},
                    )
            except Exception as e:
                logger.debug(f"DB steps collection lookup failed: {e}")

        # 2. Try in-memory cache
        if simulation_id in SIMULATION_CACHE:
            cached = SIMULATION_CACHE[simulation_id]
            features_raw = cached.get("steps_features", [])
            features = [
                GeoJSONFeature(
                    id=feat.get("id"),
                    geometry=feat["geometry"],
                    properties=feat["properties"],
                )
                for feat in features_raw
            ]
            return GeoJSONFeatureCollection(
                type="FeatureCollection",
                features=features,
                properties={"simulation_id": simulation_id, "total_steps": len(features)},
            )

        raise ResourceNotFoundException(f"Simulation '{simulation_id}' steps not found.")
