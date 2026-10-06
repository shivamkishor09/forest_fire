import React, { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import { MapContext } from '../hooks/useMapContext';
import { BaseMapType, MapState } from '../types/map';
import { APP_CONFIG } from '../../../app/config';
import { BaseMap } from './BaseMap';

export interface MapContainerProps {
  initialCenterLat?: number;
  initialCenterLng?: number;
  initialZoom?: number;
  onMapClick?: (lat: number, lng: number) => void;
  children?: React.ReactNode;
  className?: string;
}

export const MapContainer: React.FC<MapContainerProps> = ({
  initialCenterLat = APP_CONFIG.defaultViewport.lat,
  initialCenterLng = APP_CONFIG.defaultViewport.lng,
  initialZoom = APP_CONFIG.defaultViewport.zoom,
  onMapClick,
  children,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<L.Map | null>(null);
  const [baseMap, setBaseMap] = useState<BaseMapType>('darkMatter');
  const [activeLayers, setActiveLayers] = useState<MapState['activeLayers']>({
    regionBoundary: true,
    riskChoropleth: true,
    activeFires: true,
    simulationPerimeter: true,
    terrain: false,
    weather: false,
  });

  const [mapClickCallback, setMapClickCallback] = useState<
    ((lat: number, lng: number) => void) | undefined
  >(() => onMapClick);

  // Keep callback updated
  useEffect(() => {
    setMapClickCallback(() => onMapClick);
  }, [onMapClick]);

  const toggleLayer = useCallback((layerName: keyof MapState['activeLayers']) => {
    setActiveLayers((prev) => ({
      ...prev,
      [layerName]: !prev[layerName],
    }));
  }, []);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!containerRef.current) return;

    try {
      // Clear any prior leaflet internal ID on the DOM node to prevent StrictMode clashes
      if ((containerRef.current as unknown as { _leaflet_id?: number | null })._leaflet_id) {
        (containerRef.current as unknown as { _leaflet_id?: number | null })._leaflet_id = null;
      }

      const leafletMap = L.map(containerRef.current, {
        center: [initialCenterLat, initialCenterLng],
        zoom: initialZoom,
        zoomControl: false, // We use custom MapControls
        attributionControl: false,
      });

      // Add attribution in small font
      L.control
        .attribution({ position: 'bottomright', prefix: false })
        .addTo(leafletMap);

      setMap(leafletMap);

      // Force recalculation of container dimensions once mounted in DOM
      const timer = setTimeout(() => {
        leafletMap.invalidateSize();
      }, 150);

      // Handle map resize observer if available in environment
      let resizeObserver: ResizeObserver | null = null;
      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(() => {
          leafletMap.invalidateSize();
        });
        resizeObserver.observe(containerRef.current);
      }

      return () => {
        clearTimeout(timer);
        if (resizeObserver) resizeObserver.disconnect();
        leafletMap.remove();
        setMap(null);
      };
    } catch (err) {
      console.warn('Map initialization error:', err);
    }
  }, [initialCenterLat, initialCenterLng, initialZoom]);

  // Handle map click events
  useEffect(() => {
    if (!map) return;

    const handleClick = (e: L.LeafletMouseEvent) => {
      if (mapClickCallback) {
        mapClickCallback(e.latlng.lat, e.latlng.lng);
      }
    };

    map.on('click', handleClick);

    return () => {
      map.off('click', handleClick);
    };
  }, [map, mapClickCallback]);

  return (
    <MapContext.Provider
      value={{
        map,
        setMap,
        baseMap,
        setBaseMap,
        activeLayers,
        toggleLayer,
        onMapClick: mapClickCallback,
        setOnMapClick: setMapClickCallback,
      }}
    >
      <div
        className={`relative w-full h-full bg-ops-bg overflow-hidden select-none ${className}`}
        data-testid="map-container"
      >
        {/* Leaflet Mount Target */}
        <div ref={containerRef} className="w-full h-full z-0" />

        {/* BaseMap tile controller */}
        <BaseMap />

        {/* Child layers and controls rendered within MapContext */}
        {children}
      </div>
    </MapContext.Provider>
  );
};
