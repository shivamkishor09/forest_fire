import React from 'react';
import { useMapContext } from '../hooks/useMapContext';
import { BaseMapType } from '../types/map';
import { PlusIcon, MinusIcon, MaximizeIcon, MinimizeIcon, TargetIcon } from '../../../components/common/Icons';

export interface MapControlsProps {
  onResetView?: () => void;
  className?: string;
}

export const MapControls: React.FC<MapControlsProps> = ({ onResetView, className = '' }) => {
  const { map, baseMap, setBaseMap } = useMapContext();
  const [isFullscreen, setIsFullscreen] = React.useState(false);

  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  const handleToggleFullscreen = () => {
    if (typeof document === 'undefined') return;
    if (!document.fullscreenElement) {
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch(() => {});
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    }
  };

  const handleZoomIn = () => {
    if (map) map.zoomIn();
  };

  const handleZoomOut = () => {
    if (map) map.zoomOut();
  };

  return (
    <div className={`flex flex-col space-y-1.5 z-[400] select-none ${className}`}>
      {/* Zoom In / Out Controls */}
      <div className="bg-ops-panel border border-ops-border rounded-[3px] shadow-md flex flex-col overflow-hidden">
        <button
          onClick={handleZoomIn}
          className="w-7 h-7 flex items-center justify-center text-txt-secondary hover:bg-ops-surface hover:text-txt-primary transition-colors border-b border-ops-border"
          title="Zoom In"
          aria-label="Zoom In"
        >
          <PlusIcon className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={handleZoomOut}
          className="w-7 h-7 flex items-center justify-center text-txt-secondary hover:bg-ops-surface hover:text-txt-primary transition-colors"
          title="Zoom Out"
          aria-label="Zoom Out"
        >
          <MinusIcon className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Fullscreen GIS Toggle */}
      <button
        onClick={handleToggleFullscreen}
        className="w-7 h-7 bg-ops-panel border border-ops-border rounded-[3px] shadow-md flex items-center justify-center text-txt-secondary hover:bg-ops-surface hover:text-txt-primary transition-colors text-xs"
        title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen GIS'}
        aria-label="Toggle Fullscreen GIS"
      >
        {isFullscreen ? (
          <MinimizeIcon className="w-3.5 h-3.5" />
        ) : (
          <MaximizeIcon className="w-3.5 h-3.5" />
        )}
      </button>

      {/* Reset / Fit Region View */}
      {onResetView && (
        <button
          onClick={onResetView}
          className="w-7 h-7 bg-ops-panel border border-ops-border rounded-[3px] shadow-md flex items-center justify-center text-txt-secondary hover:bg-ops-surface hover:text-txt-primary transition-colors"
          title="Reset to Region Bounds"
          aria-label="Reset View"
        >
          <TargetIcon className="w-3.5 h-3.5 text-txt-muted" />
        </button>
      )}

      {/* Basemap switcher */}
      <div className="bg-ops-panel border border-ops-border rounded-[3px] shadow-md p-0.5 flex flex-col space-y-0.5">
        {(
          [
            { id: 'darkMatter', label: 'Dark' },
            { id: 'satellite', label: 'Sat' },
            { id: 'osm', label: 'Topo' },
          ] as const
        ).map((b) => (
          <button
            key={b.id}
            onClick={() => setBaseMap(b.id as BaseMapType)}
            className={`w-6 h-6 rounded-[2px] flex items-center justify-center text-[10px] font-mono transition-colors ${
              baseMap === b.id
                ? 'bg-forest text-txt-primary font-bold'
                : 'text-txt-muted hover:text-txt-primary hover:bg-ops-surface'
            }`}
            title={`Switch to ${b.label} basemap`}
            aria-label={`Switch to ${b.label} basemap`}
          >
            {b.label}
          </button>
        ))}
      </div>
    </div>
  );
};

