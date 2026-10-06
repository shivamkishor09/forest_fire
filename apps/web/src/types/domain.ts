/**
 * Domain entity types conforming to DATA_CONTRACTS.md and Phase 2 backend
 */

import { BoundingBox, GeoJSONFeature, PolygonGeometry, MultiPolygonGeometry } from './geo';

export type RiskClass = 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';

export type SimulationStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export type FireConfidence = 'low' | 'nominal' | 'high';

export type FireStatus = 'active' | 'contained' | 'extinguished';

// --- Region ---
export interface RegionSummary {
  id: string;
  code: string;
  name: string;
  state: string;
  area_sqkm: number;
  bbox?: BoundingBox;
  is_active?: boolean;
}

export interface RegionDetail extends RegionSummary {
  description?: string;
  grid_resolution_meters: number;
  total_cells?: number;
  boundary?: GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary>;
  created_at?: string;
  updated_at?: string;
}

// --- Active Fire Hotspots ---
export interface FireHotspotProperties {
  id: string;
  detection_time: string;
  satellite: string;
  confidence: FireConfidence | string;
  frp_mw: number | null;
  brightness_temperature_kelvin: number | null;
  status: FireStatus | string;
  region_id?: string | null;
  latitude?: number;
  longitude?: number;
  raw_properties?: Record<string, unknown>;
}

export interface FireEventDetail extends FireHotspotProperties {
  location: {
    type: 'Point';
    coordinates: [number, number]; // [lon, lat]
  };
  footprint?: {
    type: 'MultiPolygon';
    coordinates: number[][][][];
  } | null;
  created_at?: string;
}

// --- 24h Risk Prediction ---
export interface RiskPredictionProperties {
  cell_id: string;
  grid_cell_id?: string;
  risk_probability: number;
  risk_class: RiskClass;
  fwi_index?: number | null;
  fwi?: number | null;
  elevation?: number | null;
  elevation_m?: number | null;
  slope?: number | null;
  slope_deg?: number | null;
  aspect?: number | null;
  fuel_type?: string | null;
  model_version?: string;
  target_date?: string;
  forecast_start?: string;
  forecast_end?: string;
  prediction_timestamp?: string;
}


export interface RiskSummary {
  region_id: string;
  target_date: string;
  total_cells: number;
  high_risk_cells: number;
  extreme_risk_cells: number;
  mean_probability: number;
  max_probability?: number;
  risk_distribution: {
    low: number;
    moderate: number;
    high: number;
    extreme: number;
  };
}

// --- 12h Spread Simulation ---
export interface IgnitionPoint {
  latitude: number;
  longitude: number;
}

export interface SimulationCreateRequest {
  region_id: string;
  name?: string;
  ignition_point?: IgnitionPoint;
  ignition_points?: IgnitionPoint[];
  ignition_time?: string;
  duration_hours?: number;
  max_duration_hours?: number;
  temporal_step_minutes?: number;
  weather_scenario?: {
    wind_speed_ms?: number;
    wind_direction_deg?: number;
    temperature_c?: number;
    relative_humidity_pct?: number;
  };
  fuel_type?: string;
}

export interface SimulationJob {
  simulation_id: string;
  status: SimulationStatus;
  message?: string;
  created_at?: string;
  submitted_at?: string;
  duration_hours?: number;
  poll_url?: string;
}

export interface SimulationDetail {
  id?: string;
  simulation_id: string;
  region_id?: string;
  name?: string;
  status: SimulationStatus;
  progress_pct?: number;
  duration_hours: number;
  max_duration_hours?: number;
  temporal_step_minutes?: number;
  ignition_source?: string;
  ignition_point?: {
    type: 'Point';
    coordinates: [number, number]; // [lon, lat]
  };
  metrics?: {
    total_area_burned_ha: number;
    peak_spread_velocity_kmh: number;
    dominant_spread_direction_deg: number;
  } | null;
  engine_version?: string;
  completed_steps?: number;
  total_steps?: number;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface SimulationStepProperties {
  step_number: number;
  step_hour?: number;
  elapsed_minutes: number;
  cumulative_burned_area_ha: number;
  burned_area_ha?: number;
  active_front_cells_count?: number;
  spread_velocity_kmh?: number;
  spread_direction_deg?: number;
  intensity_mw?: number;
  max_rate_of_spread_meters_per_min?: number;
}

// --- GIS Layers Metadata ---
export interface LayerLegendItem {
  label: string;
  color: string;
  value?: string;
}

export interface LayerMetadata {
  id: string;
  name: string;
  category: 'risk' | 'fire' | 'terrain' | 'weather' | 'vegetation' | 'simulation';
  description: string;
  resolution?: string;
  source: string;
  is_available: boolean;
  legend?: LayerLegendItem[];
}
