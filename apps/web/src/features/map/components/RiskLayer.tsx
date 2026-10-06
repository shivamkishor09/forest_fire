import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useMapContext } from '../hooks/useMapContext';
import { GeoJSONFeatureCollection, PolygonGeometry } from '../../../types/geo';
import { RiskPredictionProperties } from '../../../types/domain';
import { getRiskStyle } from '../utils/geoUtils';

export interface RiskLayerProps {
  riskData: GeoJSONFeatureCollection<PolygonGeometry, RiskPredictionProperties> | null;
  onSelectCell?: (cellProps: RiskPredictionProperties) => void;
  selectedCellId?: string | null;
}

export const RiskLayer: React.FC<RiskLayerProps> = ({
  riskData,
  onSelectCell,
  selectedCellId,
}) => {
  const { map, activeLayers } = useMapContext();
  const layerRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => {
    if (!map) return;

    if (layerRef.current) {
      map.removeLayer(layerRef.current);
      layerRef.current = null;
    }

    if (!riskData || !activeLayers.riskChoropleth || !riskData.features?.length) {
      return;
    }

    const geoJsonLayer = L.geoJSON(riskData as unknown as GeoJSON.GeoJsonObject, {
      style: (feature) => {
        const props = feature?.properties as RiskPredictionProperties | undefined;
        const baseStyle = getRiskStyle(props?.risk_class || 'LOW');
        const isSelected = props?.cell_id === selectedCellId;

        return {
          ...baseStyle,
          weight: isSelected ? 2.5 : 0.8,
          color: isSelected ? '#ffffff' : baseStyle.color,
          fillOpacity: isSelected ? 0.85 : baseStyle.fillOpacity,
        };
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties as RiskPredictionProperties;
        if (!props) return;

        layer.on({
          mouseover: (e) => {
            const target = e.target as L.Path;
            target.setStyle({ weight: 2, color: '#f8fafc', fillOpacity: 0.8 });
          },
          mouseout: (e) => {
            const target = e.target as L.Path;
            const isSelected = props.cell_id === selectedCellId;
            const style = getRiskStyle(props.risk_class);
            target.setStyle({
              weight: isSelected ? 2.5 : 0.8,
              color: isSelected ? '#ffffff' : style.color,
              fillOpacity: isSelected ? 0.85 : style.fillOpacity,
            });
          },
          click: () => {
            if (onSelectCell) {
              onSelectCell(props);
            }
          },
        });

        layer.bindTooltip(
          `<div class="font-mono text-xs leading-tight">
            <span class="font-bold uppercase tracking-wider text-txt-primary">${props.risk_class} RISK</span><br/>
            <span class="text-txt-secondary">Susceptibility: ${(props.risk_probability * 100).toFixed(1)}%</span><br/>
            <span class="text-txt-muted text-[10px]">Partition: ${props.cell_id}</span>
          </div>`,
          { sticky: true, className: 'leaflet-dark-tooltip' }
        );
      },
    });

    geoJsonLayer.addTo(map);
    layerRef.current = geoJsonLayer;

    return () => {
      if (layerRef.current && map) {
        map.removeLayer(layerRef.current);
      }
    };
  }, [map, riskData, activeLayers.riskChoropleth, onSelectCell, selectedCellId]);

  return null;
};
