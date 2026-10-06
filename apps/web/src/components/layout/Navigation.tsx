import React, { useState } from 'react';
import {
  GridIcon,
  ShieldIcon,
  FlameIcon,
  ActivityIcon,
  LayersIcon,
  ChevronRightIcon,
  ChevronLeftIcon,
} from '../common/Icons';

export type NavTab = 'overview' | 'risk' | 'active_fires' | 'simulation' | 'layers';

export interface NavigationProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  className?: string;
}

export const Navigation: React.FC<NavigationProps> = ({
  currentTab,
  onSelectTab,
  className = '',
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navItems: {
    id: NavTab;
    label: string;
    ariaLabel: string;
    icon: React.ReactNode;
  }[] = [
    {
      id: 'overview',
      label: 'OVERVIEW',
      ariaLabel: 'Overview',
      icon: <GridIcon className="w-4 h-4" />,
    },
    {
      id: 'risk',
      label: '24H FIRE RISK',
      ariaLabel: '24h Fire Risk',
      icon: <ShieldIcon className="w-4 h-4" />,
    },
    {
      id: 'active_fires',
      label: 'ACTIVE HOTSPOTS',
      ariaLabel: 'Active Hotspots',
      icon: <FlameIcon className="w-4 h-4" />,
    },
    {
      id: 'simulation',
      label: 'SPREAD SIMULATION',
      ariaLabel: '12h Simulation',
      icon: <ActivityIcon className="w-4 h-4" />,
    },
    {
      id: 'layers',
      label: 'ENVIRONMENTAL DATA',
      ariaLabel: 'Environmental Layers',
      icon: <LayersIcon className="w-4 h-4" />,
    },
  ];

  return (
    <aside
      className={`bg-ops-subtle border-r border-ops-border flex flex-col shrink-0 select-none z-20 transition-all duration-150 ${
        isCollapsed ? 'w-14' : 'w-56'
      } ${className}`}
    >
      {/* Collapse / Expand Control Header */}
      <div className="h-9 px-3 border-b border-ops-border flex items-center justify-between">
        {!isCollapsed && (
          <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-txt-muted">
            OPERATIONAL MODULES
          </span>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-txt-muted hover:text-txt-primary p-1 rounded-[2px] hover:bg-ops-surface transition-colors ml-auto text-xs flex items-center justify-center w-5 h-5"
          title={isCollapsed ? 'Expand Navigation' : 'Collapse Navigation'}
          aria-label={isCollapsed ? 'Expand Navigation' : 'Collapse Navigation'}
        >
          {isCollapsed ? (
            <ChevronRightIcon className="w-3.5 h-3.5" />
          ) : (
            <ChevronLeftIcon className="w-3.5 h-3.5" />
          )}
        </button>
      </div>

      {/* Navigation Module Links */}
      <nav className="flex-1 py-2 space-y-0.5">
        {navItems.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center ${
                isCollapsed ? 'justify-center py-2.5 px-0' : 'justify-start px-3 py-2'
              } text-[12px] font-medium tracking-wide transition-colors relative ${
                isActive
                  ? 'bg-ops-surface text-txt-primary font-semibold border-l-2 border-forest'
                  : 'text-txt-secondary hover:text-txt-primary hover:bg-ops-panel border-l-2 border-transparent'
              }`}
              title={item.label}
              aria-label={item.ariaLabel}
            >
              <div className="flex items-center space-x-2.5">
                <span className={isActive ? 'text-forest' : 'text-txt-muted'}>
                  {item.icon}
                </span>
                {!isCollapsed && <span>{item.label}</span>}
              </div>
            </button>
          );
        })}
      </nav>

      {/* Operational Reference Footer */}
      {!isCollapsed ? (
        <div className="p-3 border-t border-ops-border bg-ops-bg text-[10px] font-mono text-txt-muted space-y-1">
          <div className="flex justify-between">
            <span>GRID:</span>
            <span className="text-txt-secondary">500m × 500m</span>
          </div>
          <div className="flex justify-between">
            <span>PROJECTION:</span>
            <span className="text-txt-secondary">EPSG:4326</span>
          </div>
          <div className="flex justify-between">
            <span>STATUS:</span>
            <span className="text-forest font-semibold">ONLINE</span>
          </div>
        </div>
      ) : (
        <div className="p-2 border-t border-ops-border text-center text-[9px] font-mono text-txt-muted">
          500m
        </div>
      )}
    </aside>
  );
};

