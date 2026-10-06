import React, { useState } from 'react';
import { useMapContext } from '../hooks/useMapContext';
import { APP_CONFIG } from '../../../app/config';
import { ChevronDownIcon, ChevronUpIcon } from '../../../components/common/Icons';

export interface MapLegendProps {
  className?: string;
}

export const MapLegend: React.FC<MapLegendProps> = ({ className = '' }) => {
  const { activeLayers } = useMapContext();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const hasActiveLegends =
    activeLayers.riskChoropleth ||
    activeLayers.activeFires ||
    activeLayers.simulationPerimeter;

  if (!hasActiveLegends) return null;

  return (
    <div
      className={`z-[400] bg-ops-panel/95 border border-ops-border rounded-[3px] shadow-lg overflow-hidden transition-all text-xs select-none ${
        isCollapsed ? 'w-auto' : 'w-56'
      } ${className}`}
    >
      <div
        className="px-2.5 py-1.5 bg-ops-subtle border-b border-ops-border flex items-center justify-between cursor-pointer"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-txt-primary">
          MAP LEGEND
        </span>
        {isCollapsed ? (
          <ChevronUpIcon className="w-3.5 h-3.5 text-txt-muted" />
        ) : (
          <ChevronDownIcon className="w-3.5 h-3.5 text-txt-muted" />
        )}
      </div>

      {!isCollapsed && (
        <div className="p-2.5 space-y-3 font-mono text-[10px]">
          {/* 24h Fire Risk */}
          {activeLayers.riskChoropleth && (
            <div>
              <div className="font-semibold text-txt-primary text-[10px] tracking-wider mb-1.5 flex items-center justify-between">
                <span>24H FIRE RISK</span>
                <span className="text-txt-muted">500m</span>
              </div>
              <div className="space-y-1">
                {Object.entries(APP_CONFIG.riskColors).map(([key, config]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="flex items-center space-x-2">
                      <span
                        className="w-2.5 h-2.5 rounded-[1px] shrink-0"
                        style={{ backgroundColor: config.fillColor }}
                      />
                      <span className="text-txt-secondary uppercase">{config.label}</span>
                    </span>
                    <span className="text-txt-muted">{config.threshold}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active Hotspots */}
          {activeLayers.activeFires && (
            <div className="pt-2 border-t border-ops-border">
              <div className="font-semibold text-txt-primary text-[10px] tracking-wider mb-1.5 flex items-center justify-between">
                <span>THERMAL HOTSPOTS</span>
                <span className="text-txt-muted">FIRMS</span>
              </div>
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-danger shrink-0 border border-txt-primary/40" />
                    <span className="text-txt-secondary">High Confidence</span>
                  </span>
                  <span className="text-txt-muted">&gt;50 MW</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber shrink-0 border border-txt-primary/40" />
                    <span className="text-txt-secondary">Nominal</span>
                  </span>
                  <span className="text-txt-muted">&lt;50 MW</span>
                </div>
              </div>
            </div>
          )}

          {/* 12h Spread Simulation */}
          {activeLayers.simulationPerimeter && (
            <div className="pt-2 border-t border-ops-border">
              <div className="font-semibold text-txt-primary text-[10px] tracking-wider mb-1.5 flex items-center justify-between">
                <span>SPREAD SIMULATION</span>
                <span className="text-txt-muted">12H CA</span>
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-danger border border-txt-primary shrink-0" />
                  <span className="text-txt-secondary">Ignition Origin</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-3 h-1.5 bg-danger/80 border border-danger shrink-0" />
                  <span className="text-txt-secondary">Active Perimeter Front</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-3 h-1.5 bg-amber/40 border border-amber border-dashed shrink-0" />
                  <span className="text-txt-secondary">Cumulative Burn Area</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

