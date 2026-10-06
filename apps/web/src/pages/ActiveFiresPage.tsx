import React from 'react';
import { MapContainer } from '../features/map/components/MapContainer';
import { RegionLayer } from '../features/map/components/RegionLayer';
import { FireLayer } from '../features/map/components/FireLayer';
import { MapControls } from '../features/map/components/MapControls';
import { LayerControls } from '../features/map/components/LayerControls';
import { FireList } from '../features/fire/components/FireList';
import { FireDetailsCard } from '../features/fire/components/FireDetailsCard';
import { useActiveFires } from '../features/fire/hooks/useActiveFires';
import { RegionSummary, FireHotspotProperties, IgnitionPoint } from '../types/domain';
import { GeoJSONFeature, PolygonGeometry, MultiPolygonGeometry } from '../types/geo';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';
import { ErrorAlert } from '../components/feedback/ErrorAlert';

export interface ActiveFiresPageProps {
  selectedRegion: RegionSummary | null;
  boundary: GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary> | null;
  onNavigateToSimulation?: (ignition: IgnitionPoint) => void;
}

export const ActiveFiresPage: React.FC<ActiveFiresPageProps> = ({
  selectedRegion,
  boundary,
  onNavigateToSimulation,
}) => {
  const {
    filteredFeatures,
    selectedFire,
    setSelectedFire,
    confidenceFilter,
    setConfidenceFilter,
    isLoading,
    error,
    reload,
  } = useActiveFires(selectedRegion?.id);

  const handleSimulateFromFire = (fire: FireHotspotProperties) => {
    if (onNavigateToSimulation && fire.latitude !== undefined && fire.longitude !== undefined) {
      onNavigateToSimulation({ latitude: fire.latitude, longitude: fire.longitude });
    }
  };

  const hotspotPropertiesList = filteredFeatures.map((f: { properties: FireHotspotProperties }) => f.properties);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative bg-ops-bg">
      {/* Top Controls Bar */}
      <div className="h-9 bg-ops-panel border-b border-ops-border px-4 flex items-center justify-between shrink-0 text-xs z-10">
        <div className="flex items-center space-x-3">
          <span className="font-mono text-[11px] font-semibold text-txt-secondary uppercase tracking-wider">
            Satellite Sensor Feeds:
          </span>
          <span className="px-2 py-0.5 rounded-xs bg-ops-surface text-txt-primary font-mono text-[11px] border border-ops-border">
            VIIRS NOAA-20 · MODIS Aqua/Terra
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-txt-muted font-mono text-[11px] uppercase tracking-wider">
            Confidence:
          </span>
          <div className="inline-flex rounded-xs border border-ops-border bg-ops-bg p-0.5">
            {(['all', 'high', 'nominal'] as const).map((conf) => (
              <button
                key={conf}
                onClick={() => setConfidenceFilter(conf)}
                className={`px-2.5 py-0.5 text-[11px] font-mono uppercase tracking-wider rounded-xs transition-colors ${
                  confidenceFilter === conf
                    ? 'bg-amber text-ops-bg font-bold'
                    : 'text-txt-secondary hover:text-txt-primary hover:bg-ops-surface/50'
                }`}
              >
                {conf}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Split Layout: Map on left, Hotspots on right */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Map Viewport */}
        <div className="flex-1 relative overflow-hidden">
          {isLoading && (
            <div className="absolute inset-0 z-30 bg-ops-bg/75 flex items-center justify-center">
              <LoadingSpinner label="Fetching satellite thermal anomalies..." />
            </div>
          )}

          {error && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 w-full max-w-md px-4">
              <ErrorAlert
                title="Active Fires API Unavailable"
                message={error}
                onRetry={reload}
              />
            </div>
          )}

          <MapContainer>
            <RegionLayer boundaryFeature={boundary} />
            <FireLayer
              firesData={
                filteredFeatures.length > 0
                  ? { type: 'FeatureCollection', features: filteredFeatures }
                  : null
              }
              selectedFireId={selectedFire?.id}
              onSelectFire={(fire: FireHotspotProperties) => setSelectedFire(fire)}
            />

            {/* Map Controls */}
            <div className="absolute top-3 right-3 z-[400] flex flex-col space-y-2 pointer-events-auto">
              <LayerControls />
              <MapControls />
            </div>

            {/* Selected Fire Overlay */}
            {selectedFire && (
              <div className="absolute top-3 left-3 z-[400] max-w-xs pointer-events-auto">
                <FireDetailsCard
                  fire={selectedFire}
                  onClose={() => setSelectedFire(null)}
                  onSimulateFromFire={handleSimulateFromFire}
                />
              </div>
            )}
          </MapContainer>
        </div>

        {/* Right Hotspots List */}
        <div className="w-80 bg-ops-panel border-l border-ops-border flex flex-col shrink-0 z-10 overflow-hidden">
          <div className="p-3 border-b border-ops-border bg-ops-subtle flex items-center justify-between">
            <span className="font-semibold text-xs text-txt-primary uppercase tracking-wider font-mono">
              Hotspots ({filteredFeatures.length})
            </span>
            <span className="text-[10px] font-mono text-txt-muted uppercase tracking-wider">24H Window</span>
          </div>

          <div className="flex-1 overflow-y-auto">
            <FireList
              fires={hotspotPropertiesList}
              selectedFireId={selectedFire?.id}
              onSelectFire={(fire: FireHotspotProperties) => setSelectedFire(fire)}
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
