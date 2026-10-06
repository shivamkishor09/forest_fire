/**
 * Region API service
 */

import { httpClient } from './client';
import { RegionSummary, RegionDetail } from '../../types/domain';
import { GeoJSONFeature, PolygonGeometry, MultiPolygonGeometry } from '../../types/geo';

export async function fetchRegions(): Promise<RegionSummary[]> {
  const resp = await httpClient.get<
    RegionSummary[] | { count: number; results: RegionSummary[] }
  >('/regions');

  if (Array.isArray(resp)) {
    return resp;
  }
  if (resp && Array.isArray(resp.results)) {
    return resp.results;
  }
  return [];
}

export async function fetchRegionById(regionId: string): Promise<RegionDetail> {
  return httpClient.get<RegionDetail>(`/regions/${encodeURIComponent(regionId)}`);
}

export async function fetchRegionBoundary(
  regionId: string
): Promise<GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary>> {
  try {
    return await httpClient.get<GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary>>(
      `/regions/${encodeURIComponent(regionId)}/boundary`
    );
  } catch {
    const detail = await fetchRegionById(regionId);
    return detail.boundary as unknown as GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary>;
  }
}
