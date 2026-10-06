import React from 'react';
import { MapContainer } from '../features/map/components/MapContainer';
import { RegionLayer } from '../features/map/components/RegionLayer';
import { MapControls } from '../features/map/components/MapControls';
import { LayerControls } from '../features/map/components/LayerControls';
import { LayerManager } from '../features/layers/components/LayerManager';
import { useLayers } from '../features/layers/hooks/useLayers';
import { RegionSummary } from '../types/domain';
import { GeoJSONFeature, PolygonGeometry, MultiPolygonGeometry } from '../types/geo';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';
import { ErrorAlert } from '../components/feedback/ErrorAlert';
import { LayersIcon } from '../components/common/Icons';

export interface LayersPageProps {
  selectedRegion: RegionSummary | null;
  boundary: GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary> | null;
}

export const LayersPage: React.FC<LayersPageProps> = ({
  selectedRegion,
  boundary,
}) => {
  const {
    layers,
    selectedLayerId,
    setSelectedLayerId,
    selectedLayer,
    isLoading,
    error,
    reload,
  } = useLayers();

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative bg-ops-bg">
      {/* Top Ribbon */}
      <div className="h-9 bg-ops-panel border-b border-ops-border px-4 flex items-center justify-between shrink-0 text-xs z-10">
        <div className="flex items-center space-x-3">
          <span className="font-semibold text-txt-primary uppercase font-mono text-[11px] tracking-wider">
            Layer Catalog:
          </span>
          <span className="text-txt-muted font-mono text-[11px]">
            ISRO Bhuvan · CartoDEM · IMD ERA5 · NASA FIRMS
          </span>
        </div>

        <div className="text-txt-secondary font-mono text-[11px] hidden md:block">
          Sector: {selectedRegion?.name || 'Garhwal Division'} | 500m Native Rasters
        </div>
      </div>

      {/* Split Layout: Map on left, Layer Catalogue on right */}
      <div className="flex-1 flex overflow-hidden relative">
        <div className="flex-1 relative overflow-hidden">
          {isLoading && (
            <div className="absolute inset-0 z-30 bg-ops-bg/75 flex items-center justify-center">
              <LoadingSpinner label="Loading GIS layers metadata..." />
            </div>
          )}

          {error && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 w-full max-w-md px-4">
              <ErrorAlert
                title="Layers Service Unavailable"
                message={error}
                onRetry={reload}
              />
            </div>
          )}

          <MapContainer>
            <RegionLayer boundaryFeature={boundary} />

            {/* Floating Controls */}
            <div className="absolute top-4 right-4 z-[400] flex flex-col space-y-2 pointer-events-auto">
              <LayerControls />
              <MapControls />
            </div>

            {/* Selected Layer Properties Card */}
            {selectedLayer && (
              <div className="absolute top-4 left-4 z-[400] bg-ops-panel border border-ops-border rounded-xs p-3.5 shadow-2xl text-xs w-72 pointer-events-auto space-y-2">
                <div className="font-semibold text-txt-primary flex items-center space-x-2 font-mono text-[11px] uppercase tracking-wider pb-1.5 border-b border-ops-border">
                  <LayersIcon className="w-3.5 h-3.5 text-amber" />
                  <span>{selectedLayer.name}</span>
                </div>
                <p className="text-[11px] text-txt-secondary leading-relaxed">
                  {selectedLayer.description}
                </p>
                <div className="space-y-1 font-mono text-[10px] text-txt-muted pt-2 border-t border-ops-border">
                  <div className="flex justify-between">
                    <span className="uppercase">Source:</span>
                    <span className="text-txt-primary">{selectedLayer.source}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="uppercase">Resolution:</span>
                    <span className="text-txt-primary">{selectedLayer.resolution || '500m'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="uppercase">Status:</span>
                    <span className={selectedLayer.is_available ? 'text-forest font-semibold' : 'text-txt-muted'}>
                      {selectedLayer.is_available ? 'ONLINE' : 'STANDBY'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </MapContainer>
        </div>

        {/* Right Catalogue Sidebar */}
        <div className="w-80 bg-ops-panel border-l border-ops-border p-3.5 flex flex-col shrink-0 z-10 overflow-hidden">
          <div className="pb-2.5 border-b border-ops-border mb-3 flex items-center justify-between font-mono">
            <span className="font-semibold text-xs text-txt-primary uppercase tracking-wider">
              Datasets & Layers
            </span>
            <span className="text-[10px] text-txt-muted">{layers.length} Total</span>
          </div>

          <div className="flex-1 overflow-y-auto">
            <LayerManager
              layers={layers}
              selectedLayerId={selectedLayerId}
              onSelectLayer={setSelectedLayerId}
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

