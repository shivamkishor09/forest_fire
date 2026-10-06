import React from 'react';
import { LayerMetadata } from '../../../types/domain';
import { Badge } from '../../../components/ui/Badge';
import { Skeleton } from '../../../components/feedback/Skeleton';
import {
  LayersIcon,
  FlameIcon,
  MountainIcon,
  WindIcon,
  LeafIcon,
  ShieldIcon,
  ActivityIcon,
} from '../../../components/common/Icons';

export interface LayerManagerProps {
  layers: LayerMetadata[];
  selectedLayerId: string;
  onSelectLayer: (id: string) => void;
  isLoading?: boolean;
  className?: string;
}

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'risk':
      return <ShieldIcon className="w-3.5 h-3.5 text-amber" />;
    case 'fire':
      return <FlameIcon className="w-3.5 h-3.5 text-danger" />;
    case 'terrain':
      return <MountainIcon className="w-3.5 h-3.5 text-txt-secondary" />;
    case 'weather':
      return <WindIcon className="w-3.5 h-3.5 text-txt-secondary" />;
    case 'vegetation':
      return <LeafIcon className="w-3.5 h-3.5 text-forest" />;
    case 'simulation':
      return <ActivityIcon className="w-3.5 h-3.5 text-amber" />;
    default:
      return <LayersIcon className="w-3.5 h-3.5 text-txt-muted" />;
  }
};

export const LayerManager: React.FC<LayerManagerProps> = ({
  layers,
  selectedLayerId,
  onSelectLayer,
  isLoading = false,
  className = '',
}) => {
  if (isLoading) {
    return (
      <div className={`space-y-3 p-4 ${className}`}>
        <Skeleton className="h-16 w-full" count={4} />
      </div>
    );
  }

  const layerUnits: Record<string, string> = {
    elevation: 'meters (m)',
    slope: 'degrees (°)',
    aspect: 'degrees (°)',
    weather: 'm/s, °C, %',
    wind: 'm/s',
    temperature: '°C',
    humidity: '%',
    fwi: 'FWI Index',
    ndvi: 'NDVI [-1, 1]',
    risk_layer: 'Prob [0-1]',
    active_fires: 'FRP (MW)',
    simulation: 'Area (ha)',
  };

  return (
    <div className={`space-y-2 overflow-y-auto ${className}`}>
      {layers.map((layer) => {
        const isSelected = layer.id === selectedLayerId;
        const unit = layerUnits[layer.id] || (layer.category === 'terrain' ? 'm / °' : null);

        return (
          <div
            key={layer.id}
            onClick={() => onSelectLayer(layer.id)}
            className={`p-3 rounded-xs border transition-all cursor-pointer ${
              isSelected
                ? 'bg-ops-surface border-ops-border border-l-2 border-l-forest'
                : 'bg-ops-bg border-ops-border hover:bg-ops-surface/50 border-l-2 border-l-transparent'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-xs text-txt-primary flex items-center space-x-2">
                {getCategoryIcon(layer.category)}
                <span>{layer.name}</span>
              </span>
              <Badge variant={layer.is_available ? 'success' : 'neutral'} size="sm">
                {layer.is_available ? 'ONLINE' : 'STANDBY'}
              </Badge>
            </div>

            <p className="text-[11px] text-txt-secondary leading-relaxed mb-2">
              {layer.description}
            </p>

            <div className="flex items-center justify-between text-[10px] font-mono text-txt-muted pt-1.5 border-t border-ops-border">
              <span>{layer.source}</span>
              <div className="flex items-center space-x-2">
                {unit && <span className="text-amber font-medium">{unit}</span>}
                <span className="text-txt-secondary">{layer.resolution || '500m'}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

