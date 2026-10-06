import React, { useState } from 'react';
import { IgnitionPoint } from '../../../types/domain';
import { Button } from '../../../components/ui/Button';
import { TargetIcon, CheckIcon } from '../../../components/common/Icons';

export interface IgnitionSelectorProps {
  ignitionPoint: IgnitionPoint | null;
  onSetIgnition: (point: IgnitionPoint) => void;
  onClearIgnition: () => void;
  className?: string;
}

export const IgnitionSelector: React.FC<IgnitionSelectorProps> = ({
  ignitionPoint,
  onSetIgnition,
  onClearIgnition,
  className = '',
}) => {
  const [manualLat, setManualLat] = useState<string>('');
  const [manualLon, setManualLon] = useState<string>('');
  const [inputError, setInputError] = useState<string | null>(null);

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const lat = parseFloat(manualLat);
    const lon = parseFloat(manualLon);

    if (isNaN(lat) || lat < -90 || lat > 90) {
      setInputError('Latitude must be between -90 and 90');
      return;
    }
    if (isNaN(lon) || lon < -180 || lon > 180) {
      setInputError('Longitude must be between -180 and 180');
      return;
    }

    setInputError(null);
    onSetIgnition({ latitude: lat, longitude: lon });
    setManualLat('');
    setManualLon('');
  };

  return (
    <div
      className={`bg-ops-panel border border-ops-border rounded-xs p-3.5 text-xs space-y-3 ${className}`}
    >
      <div className="flex items-center justify-between pb-2 border-b border-ops-border">
        <div className="flex items-center space-x-1.5 font-semibold text-txt-primary font-mono text-[11px] uppercase tracking-wider">
          <TargetIcon className="w-3.5 h-3.5 text-amber" />
          <span>Ignition Origin</span>
        </div>
        {ignitionPoint && (
          <button
            onClick={onClearIgnition}
            className="text-[11px] font-mono text-danger hover:underline transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {ignitionPoint ? (
        <div className="p-2.5 rounded-xs bg-ops-bg border border-ops-border space-y-1 font-mono text-[11px]">
          <div className="flex justify-between">
            <span className="text-txt-muted">Latitude:</span>
            <span className="text-txt-primary font-medium">{ignitionPoint.latitude.toFixed(5)}°N</span>
          </div>
          <div className="flex justify-between">
            <span className="text-txt-muted">Longitude:</span>
            <span className="text-txt-primary font-medium">{ignitionPoint.longitude.toFixed(5)}°E</span>
          </div>
          <div className="text-[10px] text-forest pt-1 border-t border-ops-border flex items-center space-x-1 font-semibold">
            <CheckIcon className="w-3 h-3" />
            <span>ORIGIN POINT PLACED ON MAP</span>
          </div>
        </div>
      ) : (
        <div className="p-3 rounded-xs bg-ops-bg border border-dashed border-ops-border text-center space-y-1">
          <p className="font-medium text-txt-primary text-[11px]">Click map or input coordinates</p>
          <p className="text-[10px] text-txt-muted">
            Sets origin cell for 12h cellular spread model.
          </p>
        </div>
      )}

      {/* Manual Coordinate Form */}
      <form onSubmit={handleManualSubmit} className="pt-1 space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-[10px] text-txt-muted font-mono block mb-1 uppercase">Latitude</label>
            <input
              type="number"
              step="any"
              placeholder="e.g. 30.2241"
              value={manualLat}
              onChange={(e) => setManualLat(e.target.value)}
              className="w-full bg-ops-bg border border-ops-border rounded-xs px-2 py-1 text-txt-primary font-mono text-[11px] focus:outline-none focus:border-forest"
            />
          </div>
          <div>
            <label className="text-[10px] text-txt-muted font-mono block mb-1 uppercase">Longitude</label>
            <input
              type="number"
              step="any"
              placeholder="e.g. 78.7842"
              value={manualLon}
              onChange={(e) => setManualLon(e.target.value)}
              className="w-full bg-ops-bg border border-ops-border rounded-xs px-2 py-1 text-txt-primary font-mono text-[11px] focus:outline-none focus:border-forest"
            />
          </div>
        </div>

        {inputError && (
          <p className="text-[10px] text-danger font-mono">{inputError}</p>
        )}

        <Button
          type="submit"
          variant="secondary"
          size="sm"
          className="w-full font-mono text-[11px]"
          disabled={!manualLat || !manualLon}
        >
          Set Coordinates
        </Button>
      </form>
    </div>
  );
};

