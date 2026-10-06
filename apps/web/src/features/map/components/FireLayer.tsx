import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useMapContext } from '../hooks/useMapContext';
import { GeoJSONFeatureCollection, PointGeometry } from '../../../types/geo';
import { FireHotspotProperties } from '../../../types/domain';
import { createHotspotIcon } from '../utils/geoUtils';

export interface FireLayerProps {
  firesData: GeoJSONFeatureCollection<PointGeometry, FireHotspotProperties> | null;
  onSelectFire?: (fireProps: FireHotspotProperties) => void;
  selectedFireId?: string | null;
}

export const FireLayer: React.FC<FireLayerProps> = ({
  firesData,
  onSelectFire,
  selectedFireId,
}) => {
  const { map, activeLayers } = useMapContext();
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!map) return;

    if (layerGroupRef.current) {
      map.removeLayer(layerGroupRef.current);
      layerGroupRef.current = null;
    }

    if (!firesData || !activeLayers.activeFires || !firesData.features?.length) {
      return;
    }

    const group = L.layerGroup();

    firesData.features.forEach((feature) => {
      const [lon, lat] = feature.geometry.coordinates;
      const props = feature.properties;
      const isSelected = props.id === selectedFireId;

      const icon = createHotspotIcon(props.confidence, props.frp_mw);
      const marker = L.marker([lat, lon], { icon });

      const popupContent = `
        <div class="p-1 space-y-1.5 font-mono text-xs">
          <div class="flex items-center justify-between pb-1 border-b border-ops-border">
            <span class="font-semibold text-danger uppercase text-[11px] tracking-wider">
              Thermal Hotspot
            </span>
            <span class="font-mono text-[10px] px-1.5 py-0.5 rounded-xs bg-ops-surface text-txt-secondary border border-ops-border">
              ${props.satellite || 'MODIS/VIIRS'}
            </span>
          </div>
          <div class="space-y-1 text-txt-secondary text-[11px]">
            <div class="flex justify-between">
              <span class="text-txt-muted">Coordinates:</span>
              <span class="text-txt-primary">${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E</span>
            </div>
            <div class="flex justify-between">
              <span class="text-txt-muted">Confidence:</span>
              <span class="capitalize text-amber font-semibold">${props.confidence || 'Nominal'}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-txt-muted">Radiative Power:</span>
              <span class="text-amber font-medium">${props.frp_mw !== null ? `${props.frp_mw.toFixed(1)} MW` : 'N/A'}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-txt-muted">Brightness Temp:</span>
              <span class="text-txt-primary">${props.brightness_temperature_kelvin !== null ? `${props.brightness_temperature_kelvin.toFixed(1)} K` : 'N/A'}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-txt-muted">Detection:</span>
              <span class="text-txt-secondary">${props.detection_time ? new Date(props.detection_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'} UTC</span>
            </div>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent, { className: 'custom-leaflet-popup' });

      marker.on('click', () => {
        if (onSelectFire) onSelectFire(props);
      });

      if (isSelected) {
        marker.openPopup();
      }

      marker.addTo(group);
    });

    group.addTo(map);
    layerGroupRef.current = group;

    return () => {
      if (layerGroupRef.current && map) {
        map.removeLayer(layerGroupRef.current);
      }
    };
  }, [map, firesData, activeLayers.activeFires, onSelectFire, selectedFireId]);

  return null;
};
