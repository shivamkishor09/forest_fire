"""Spatial alignment and spatial join linking observations onto the 500m grid cells."""

import math
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from ..common.types import (
    GridCellDefinition,
    CanonicalFireObservation,
    CanonicalWeatherObservation,
    CanonicalVegetationObservation,
    CanonicalTerrainObservation,
)
from ..grid.indexing import SpatialGridIndex, haversine_distance_meters


class SpatialAligner:
    """Aligns point, raster, and station observations onto 500m grid cells."""

    def __init__(self, index: SpatialGridIndex):
        self.index = index
        self.cells = index.cells

    def align_fire_observations(
        self,
        fires: List[CanonicalFireObservation]
    ) -> Dict[str, List[CanonicalFireObservation]]:
        """
        Group active fire observations by cell_id.
        Fires outside the grid are associated with their nearest cell or discarded.
        """
        cell_fires: Dict[str, List[CanonicalFireObservation]] = defaultdict(list)
        for fire in fires:
            cell = self.index.find_cell_for_point(fire.latitude, fire.longitude)
            if cell is not None:
                cell_fires[cell.cell_id].append(fire)
            else:
                # If within 500m of nearest cell, associate with nearest
                nearest = self.index.find_nearest_cell(fire.latitude, fire.longitude)
                if nearest is not None:
                    dist = haversine_distance_meters(
                        fire.latitude, fire.longitude,
                        nearest.centroid_lat, nearest.centroid_lon
                    )
                    if dist <= 750.0:
                        cell_fires[nearest.cell_id].append(fire)
        return dict(cell_fires)

    def align_weather_observations(
        self,
        weather_obs: List[CanonicalWeatherObservation],
        max_distance_meters: float = 100000.0,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Interpolate weather observations onto every grid cell.
        Uses Inverse Distance Weighting (IDW with power p=2) when multiple observations exist,
        or nearest neighbor fallback.
        """
        results: Dict[str, Dict[str, Any]] = {}
        if not weather_obs:
            return {c.cell_id: {} for c in self.cells}

        # Precompute obs points
        obs_points = [(o.latitude, o.longitude, o) for o in weather_obs]

        for cell in self.cells:
            # Calculate distances to all weather observations
            dists = [
                (haversine_distance_meters(cell.centroid_lat, cell.centroid_lon, lat, lon), obs)
                for lat, lon, obs in obs_points
            ]
            dists.sort(key=lambda x: x[0])

            # Check if nearest is exact (distance < 50m)
            nearest_dist, nearest_obs = dists[0]
            if nearest_dist < 50.0 or len(dists) == 1:
                results[cell.cell_id] = {
                    "temperature_c": nearest_obs.temperature_c,
                    "relative_humidity_pct": nearest_obs.relative_humidity_pct,
                    "wind_speed_ms": nearest_obs.wind_speed_ms,
                    "wind_direction_deg": nearest_obs.wind_direction_deg,
                    "wind_u_ms": nearest_obs.u_wind_ms,
                    "wind_v_ms": nearest_obs.v_wind_ms,
                    "precipitation_mm": nearest_obs.precipitation_mm,
                    "distance_to_station_m": nearest_dist,
                }
                continue

            # Inverse Distance Weighting (IDW, k=3 nearest)
            k_nearest = dists[:min(3, len(dists))]
            total_weight = 0.0
            weighted_temp = 0.0
            weighted_rh = 0.0
            weighted_wind_spd = 0.0
            weighted_u = 0.0
            weighted_v = 0.0
            weighted_precip = 0.0

            for d, obs in k_nearest:
                w = 1.0 / (max(d, 1.0) ** 2)
                total_weight += w
                if obs.temperature_c is not None:
                    weighted_temp += w * obs.temperature_c
                if obs.relative_humidity_pct is not None:
                    weighted_rh += w * obs.relative_humidity_pct
                if obs.wind_speed_ms is not None:
                    weighted_wind_spd += w * obs.wind_speed_ms
                if obs.u_wind_ms is not None:
                    weighted_u += w * obs.u_wind_ms
                if obs.v_wind_ms is not None:
                    weighted_v += w * obs.v_wind_ms
                if obs.precipitation_mm is not None:
                    weighted_precip += w * obs.precipitation_mm

            # Reconstruct meteorological wind direction from interpolated u and v vectors
            interpolated_u = round(weighted_u / total_weight, 2) if total_weight > 0 else None
            interpolated_v = round(weighted_v / total_weight, 2) if total_weight > 0 else None
            interpolated_spd = round(weighted_wind_spd / total_weight, 2) if total_weight > 0 else None
            interpolated_dir = None
            if interpolated_u is not None and interpolated_v is not None:
                interpolated_dir = round((math.degrees(math.atan2(-interpolated_u, -interpolated_v)) + 360.0) % 360.0, 1)

            results[cell.cell_id] = {
                "temperature_c": round(weighted_temp / total_weight, 2) if total_weight > 0 else None,
                "relative_humidity_pct": round(weighted_rh / total_weight, 2) if total_weight > 0 else None,
                "wind_speed_ms": interpolated_spd,
                "wind_direction_deg": interpolated_dir,
                "wind_u_ms": interpolated_u,
                "wind_v_ms": interpolated_v,
                "precipitation_mm": round(weighted_precip / total_weight, 2) if total_weight > 0 else 0.0,
                "distance_to_station_m": nearest_dist,
            }

        return results

    def align_vegetation_observations(
        self,
        veg_obs: List[CanonicalVegetationObservation]
    ) -> Dict[str, Dict[str, Any]]:
        """Associate vegetation indices and fuel classification to each grid cell."""
        results: Dict[str, Dict[str, Any]] = {}
        if not veg_obs:
            return {c.cell_id: {"fuel_type": "UNKNOWN"} for c in self.cells}

        veg_points = [(o.latitude, o.longitude, o) for o in veg_obs]

        for cell in self.cells:
            # Nearest neighbor for vegetation/fuel
            dists = [
                (haversine_distance_meters(cell.centroid_lat, cell.centroid_lon, lat, lon), obs)
                for lat, lon, obs in veg_points
            ]
            dists.sort(key=lambda x: x[0])
            nearest_dist, nearest_obs = dists[0]

            results[cell.cell_id] = {
                "ndvi": nearest_obs.ndvi,
                "ndwi": nearest_obs.ndwi,
                "fuel_type": nearest_obs.fuel_type or "UNKNOWN",
                "distance_to_sample_m": nearest_dist,
            }

        return results

    def align_terrain_observations(
        self,
        terrain_obs: List[CanonicalTerrainObservation]
    ) -> Dict[str, Dict[str, Any]]:
        """Associate DEM elevation, slope, and aspect to each grid cell."""
        results: Dict[str, Dict[str, Any]] = {}
        if not terrain_obs:
            return {c.cell_id: {} for c in self.cells}

        terrain_points = [(o.latitude, o.longitude, o) for o in terrain_obs]

        for cell in self.cells:
            dists = [
                (haversine_distance_meters(cell.centroid_lat, cell.centroid_lon, lat, lon), obs)
                for lat, lon, obs in terrain_points
            ]
            dists.sort(key=lambda x: x[0])
            nearest_dist, nearest_obs = dists[0]

            results[cell.cell_id] = {
                "elevation_m": nearest_obs.elevation_m,
                "slope_deg": nearest_obs.slope_deg,
                "aspect_deg": nearest_obs.aspect_deg,
                "distance_to_sample_m": nearest_dist,
            }

        return results
