import React from 'react';
import { NavTab } from '../../../components/layout/Navigation';
import { AlertCircleIcon, AlertTriangleIcon, InfoIcon, ChevronRightIcon } from '../../../components/common/Icons';

export interface OperationalAttentionBannerProps {
  regionName?: string;
  activeFireCount: number;
  highRiskCellCount: number;
  extremeRiskCellCount: number;
  maxProbability: number;
  forecastDate?: string;
  onNavigateTab: (tab: NavTab) => void;
  className?: string;
}

export const OperationalAttentionBanner: React.FC<OperationalAttentionBannerProps> = ({
  regionName = 'Monitored Sector',
  activeFireCount,
  highRiskCellCount,
  extremeRiskCellCount,
  maxProbability,
  forecastDate: _forecastDate,
  onNavigateTab,
  className = '',
}) => {
  const elevatedRiskTotal = highRiskCellCount + extremeRiskCellCount;

  // Determine operational attention level
  let severity: 'HIGH_ATTENTION' | 'WARNING' | 'INFO' = 'INFO';
  let title = 'Sector Operational Baseline';
  let message = `Normal baseline state for ${regionName}. No active thermal hotspots or elevated fire fronts detected.`;
  let actionLabel = 'Environmental Data';
  let targetTab: NavTab = 'layers';
  let icon = <InfoIcon className="w-4 h-4 text-forest" />;

  if (extremeRiskCellCount > 0 || (highRiskCellCount > 0 && activeFireCount > 0)) {
    severity = 'HIGH_ATTENTION';
    title = 'High Operational Attention Required';
    message = `${elevatedRiskTotal} cells exhibit elevated fire risk in ${regionName} (Peak: ${(maxProbability * 100).toFixed(0)}%)${
      activeFireCount > 0 ? ` with ${activeFireCount} active thermal hotspots` : ''
    }.`;
    actionLabel = 'Inspect 24h Risk Layer';
    targetTab = 'risk';
    icon = <AlertCircleIcon className="w-4 h-4 text-danger" />;
  } else if (activeFireCount > 0) {
    severity = 'WARNING';
    title = 'Active Satellite Thermal Anomalies Detected';
    message = `${activeFireCount} thermal hotspots detected by satellite sensors in ${regionName}.`;
    actionLabel = 'View Active Hotspots';
    targetTab = 'active_fires';
    icon = <AlertTriangleIcon className="w-4 h-4 text-amber" />;
  } else if (highRiskCellCount > 0) {
    severity = 'WARNING';
    title = 'Elevated Risk Detected';
    message = `${highRiskCellCount} grid cells are estimated in the high susceptibility class in ${regionName}.`;
    actionLabel = 'Inspect 24h Risk Layer';
    targetTab = 'risk';
    icon = <AlertTriangleIcon className="w-4 h-4 text-amber" />;
  }

  const severityStyles = {
    HIGH_ATTENTION: {
      border: 'border-danger/40 bg-danger/10',
      badge: 'bg-danger/20 text-danger border-danger/40',
      title: 'text-danger font-semibold',
      btn: 'bg-danger hover:bg-danger-hover text-txt-primary border-danger-border',
    },
    WARNING: {
      border: 'border-amber/40 bg-amber/10',
      badge: 'bg-amber/20 text-amber border-amber/40',
      title: 'text-amber font-semibold',
      btn: 'bg-amber hover:bg-amber-hover text-ops-bg border-amber-border font-semibold',
    },
    INFO: {
      border: 'border-ops-border bg-ops-subtle',
      badge: 'bg-ops-surface text-txt-secondary border-ops-border',
      title: 'text-txt-primary font-medium',
      btn: 'bg-ops-surface hover:bg-ops-hover text-txt-primary border-ops-border',
    },
  };

  const style = severityStyles[severity];

  return (
    <div
      className={`rounded-[3px] border px-3.5 py-2 transition-colors ${style.border} ${className}`}
      role="region"
      aria-label="Operational Status"
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5">
        <div className="space-y-0.5">
          <div className="flex items-center space-x-2">
            {icon}
            <span className={`text-[10px] font-mono uppercase font-semibold px-1.5 py-0.2 rounded-[2px] border ${style.badge}`}>
              {severity === 'HIGH_ATTENTION' ? 'CRITICAL' : severity === 'WARNING' ? 'WARNING' : 'NORMAL'}
            </span>
            <span className={`text-xs ${style.title}`}>
              {title}
            </span>
          </div>
          <p className="text-xs text-txt-secondary leading-normal">
            {message}
          </p>
        </div>

        <button
          onClick={() => onNavigateTab(targetTab)}
          className={`shrink-0 px-2.5 py-1 rounded-[3px] border text-xs font-medium transition-colors flex items-center space-x-1 ${style.btn}`}
        >
          <span>{actionLabel}</span>
          <ChevronRightIcon className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

