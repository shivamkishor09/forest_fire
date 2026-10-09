import { useState, useEffect, useCallback } from 'react';
import { fetchRegions, fetchRegionBoundary } from '../../../services/api/regions';
import { RegionSummary } from '../../../types/domain';
import { GeoJSONFeature, PolygonGeometry, MultiPolygonGeometry } from '../../../types/geo';

const DEFAULT_REGIONS: RegionSummary[] = [
  {
    id: '1fa85f64-5717-4562-b3fc-2c963f66afa1',
    code: 'ALL_INDIA_TERRAIN',
    name: 'All India (Free Map Exploration)',
    state: 'Pan-India',
    area_sqkm: 3287263.0,
  },
  {
    id: '3fa85f64-5717-4562-b3fc-2c963f66afa6',
    code: 'UTTARAKHAND_GARHWAL',
    name: 'Garhwal Forest Division',
    state: 'Uttarakhand',
    area_sqkm: 2840.5,
  },
  {
    id: '7ca85f64-5717-4562-b3fc-2c963f66afa7',
    code: 'WESTERN_GHATS_WAYANAD',
    name: 'Wayanad Wildlife Sanctuary',
    state: 'Kerala',
    area_sqkm: 344.4,
  },
  {
    id: '4da85f64-5717-4562-b3fc-2c963f66afa2',
    code: 'UTTARAKHAND_CORBETT',
    name: 'Jim Corbett National Park',
    state: 'Uttarakhand',
    area_sqkm: 1288.3,
  },
  {
    id: '5ea85f64-5717-4562-b3fc-2c963f66afa3',
    code: 'KARNATAKA_BANDIPUR',
    name: 'Bandipur National Park',
    state: 'Karnataka',
    area_sqkm: 874.2,
  },
  {
    id: '6fa85f64-5717-4562-b3fc-2c963f66afa4',
    code: 'MP_KANHA',
    name: 'Kanha Tiger Reserve',
    state: 'Madhya Pradesh',
    area_sqkm: 2074.0,
  },
  {
    id: '8ba85f64-5717-4562-b3fc-2c963f66afa5',
    code: 'ASSAM_KAZIRANGA',
    name: 'Kaziranga National Park',
    state: 'Assam',
    area_sqkm: 1085.5,
  },
  {
    id: '9ca85f64-5717-4562-b3fc-2c963f66afa8',
    code: 'ODISHA_SIMILIPAL',
    name: 'Similipal National Park',
    state: 'Odisha',
    area_sqkm: 2750.0,
  },
];

export function useRegions() {
  const [regions, setRegions] = useState<RegionSummary[]>(DEFAULT_REGIONS);
  const [selectedRegionId, setSelectedRegionId] = useState<string>('3fa85f64-5717-4562-b3fc-2c963f66afa6');
  const [boundary, setBoundary] = useState<
    GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary> | null
  >(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingBoundary, setIsLoadingBoundary] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load available regions
  const loadRegions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchRegions();
      if (data && data.length > 0) {
        setRegions(data);
        setSelectedRegionId((prev) => prev || data[0].id);
      }
    } catch (err: unknown) {
      console.warn('Could not refresh regions from API, using default regions:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRegions();
  }, [loadRegions]);

  // Load region boundary when selectedRegionId changes
  useEffect(() => {
    if (!selectedRegionId) {
      setBoundary(null);
      return;
    }

    let isMounted = true;
    setIsLoadingBoundary(true);

    fetchRegionBoundary(selectedRegionId)
      .then((feat: GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary>) => {
        if (isMounted) setBoundary(feat);
      })
      .catch((err: unknown) => {
        console.warn('Failed to fetch region boundary:', err);
        if (isMounted) setBoundary(null);
      })
      .finally(() => {
        if (isMounted) setIsLoadingBoundary(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedRegionId]);

  const selectedRegion = regions.find((r) => r.id === selectedRegionId) || null;

  return {
    regions,
    selectedRegionId,
    setSelectedRegionId,
    selectedRegion,
    boundary,
    isLoading,
    isLoadingBoundary,
    error,
    reload: loadRegions,
  };
}
