import React, { useState } from 'react';
import { useMapContext } from '../hooks/useMapContext';
import { LayersIcon, ChevronDownIcon, ChevronUpIcon } from '../../../components/common/Icons';

export interface LayerControlsProps {
  className?: string;
}

export const LayerControls: React.FC<LayerControlsProps> = ({ className = '' }) => {
  const { activeLayers, toggleLayer } = useMapContext();
  const [isOpen, setIsOpen] = useState(false);

  const layerItems = [
    { key: 'regionBoundary', label: 'Region Boundary', supported: true, color: '#3F7D58' },
    { key: 'riskChoropleth', label: '24h Risk Grid (500m)', supported: true, color: '#D99A2B' },
    { key: 'activeFires', label: 'Active Hotspots (FIRMS)', supported: true, color: '#D84A3A' },
    { key: 'simulationPerimeter', label: 'Spread Perimeter', supported: true, color: '#E06D2E' },
    { key: 'terrain', label: 'Elevation / Slope', supported: false, color: '#737C74' },
    { key: 'weather', label: 'Wind / FWI Vectors', supported: false, color: '#737C74' },
  ] as const;

  return (
    <div className={`z-[400] relative select-none ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="h-7 px-2.5 bg-ops-panel border border-ops-border rounded-[3px] shadow-md flex items-center space-x-1.5 text-xs font-medium text-txt-primary hover:bg-ops-surface transition-colors"
        title="Toggle Map Layers"
        aria-expanded={isOpen}
      >
        <LayersIcon className="w-3.5 h-3.5 text-txt-muted" />
        <span className="font-mono text-[11px]">LAYERS</span>
        {isOpen ? (
          <ChevronUpIcon className="w-3.5 h-3.5 text-txt-muted" />
        ) : (
          <ChevronDownIcon className="w-3.5 h-3.5 text-txt-muted" />
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-8 w-60 bg-ops-panel border border-ops-border rounded-[3px] shadow-xl p-3 text-xs">
          <div className="font-mono text-[11px] font-semibold text-txt-primary pb-2 mb-2 border-b border-ops-border flex justify-between items-center">
            <span>GIS OVERLAYS</span>
            <span className="text-[10px] text-txt-muted">EPSG:4326</span>
          </div>

          <div className="space-y-2">
            {layerItems.map((item) => {
              const isChecked = activeLayers[item.key as keyof typeof activeLayers];
              return (
                <div key={item.key} className="flex items-center justify-between">
                  <label className="flex items-center space-x-2.5 cursor-pointer flex-1">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      disabled={!item.supported}
                      onChange={() => toggleLayer(item.key as keyof typeof activeLayers)}
                      className="rounded-[2px] border-ops-border bg-ops-bg text-forest focus:ring-0 cursor-pointer disabled:cursor-not-allowed"
                    />
                    <span
                      className="w-2.5 h-2.5 rounded-[1px] shrink-0"
                      style={{ backgroundColor: item.color }}
                    />
                    <span
                      className={`text-[11px] ${
                        item.supported ? 'text-txt-primary' : 'text-txt-muted line-through'
                      }`}
                    >
                      {item.label}
                    </span>
                  </label>
                  {!item.supported && (
                    <span className="text-[9px] font-mono uppercase px-1 py-0.2 rounded bg-ops-bg text-txt-muted border border-ops-border">
                      N/A
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

