import React from 'react';
import { RiskPredictionProperties } from '../../../types/domain';
import { Badge } from '../../../components/ui/Badge';
import { TargetIcon } from '../../../components/common/Icons';

export interface RiskCellInspectorProps {
  cell: RiskPredictionProperties | null;
  onClose: () => void;
  onSimulateFromCell?: (cell: RiskPredictionProperties) => void;
  className?: string;
}

export const RiskCellInspector: React.FC<RiskCellInspectorProps> = ({
  cell,
  onClose,
  onSimulateFromCell,
  className = '',
}) => {
  if (!cell) return null;

  const riskBadgeVariant =
    cell.risk_class === 'EXTREME'
      ? 'danger'
      : cell.risk_class === 'HIGH'
      ? 'danger'
      : cell.risk_class === 'MODERATE'
      ? 'warning'
      : 'success';

  return (
    <div
      className={`bg-ops-panel/95 border border-ops-border rounded-[3px] p-3 text-xs space-y-2.5 shadow-xl ${className}`}
      role="region"
      aria-label="Grid Cell Details Inspector"
    >
      <div className="flex items-center justify-between pb-1.5 border-b border-ops-border">
        <div>
          <h4 className="font-semibold text-txt-primary">CELL INSPECTOR</h4>
          <span className="text-[10px] font-mono text-txt-muted">ID: {cell.cell_id}</span>
        </div>
        <button
          onClick={onClose}
          className="text-txt-muted hover:text-txt-primary text-xs p-1 rounded hover:bg-ops-surface"
          aria-label="Close cell inspector"
        >
          ✕
        </button>
      </div>

      {/* Risk Estimation */}
      <div className="space-y-1 font-mono text-[11px]">
        <div className="flex justify-between items-center py-0.5 border-b border-ops-border">
          <span className="text-txt-muted">Susceptibility:</span>
          <Badge variant={riskBadgeVariant} size="sm">
            {cell.risk_class}
          </Badge>
        </div>
        <div className="flex justify-between items-center py-0.5 border-b border-ops-border">
          <span className="text-txt-muted">Probability:</span>
          <span className="font-bold text-amber text-xs">
            {(cell.risk_probability * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Environmental Parameters */}
      <div className="space-y-1 font-mono text-[11px] pt-1 border-t border-ops-border">
        <div className="flex justify-between items-center py-0.5">
          <span className="text-txt-muted">FWI Rating:</span>
          <span className="text-txt-primary">
            {cell.fwi_index !== null && cell.fwi_index !== undefined ? cell.fwi_index.toFixed(1) : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between items-center py-0.5">
          <span className="text-txt-muted">Elevation:</span>
          <span className="text-txt-primary">
            {cell.elevation !== null && cell.elevation !== undefined ? `${cell.elevation} m` : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between items-center py-0.5">
          <span className="text-txt-muted">Slope:</span>
          <span className="text-txt-primary">
            {cell.slope !== null && cell.slope !== undefined ? `${cell.slope}°` : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between items-center py-0.5">
          <span className="text-txt-muted">Fuel Class:</span>
          <span className="text-txt-primary truncate max-w-[140px]">
            {cell.fuel_type || 'Conifer High'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="pt-2 border-t border-ops-border flex items-center space-x-2">
        {onSimulateFromCell && (
          <button
            className="flex-1 py-1 px-2 rounded-[2px] bg-forest hover:bg-forest-hover text-txt-primary font-semibold text-[11px] transition-colors flex items-center justify-center space-x-1 border border-forest-border"
            onClick={() => onSimulateFromCell(cell)}
          >
            <TargetIcon className="w-3 h-3" />
            <span>Simulate Spread</span>
          </button>
        )}
        <button
          className="py-1 px-2 rounded-[2px] bg-ops-surface hover:bg-ops-hover text-txt-secondary border border-ops-border text-[11px] transition-colors"
          onClick={onClose}
        >
          Dismiss
        </button>
      </div>
    </div>
  );
};

