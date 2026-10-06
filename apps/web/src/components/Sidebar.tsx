import React from 'react';
import {
  GridIcon,
  ShieldIcon,
  ActivityIcon,
  FlameIcon,
  LayersIcon,
} from './common/Icons';

export type NavTab = 'overview' | 'risk' | 'simulation' | 'active_fires' | 'layers';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'overview', label: 'Overview', icon: <GridIcon className="w-4 h-4" /> },
    { id: 'risk', label: 'Fire Risk', icon: <ShieldIcon className="w-4 h-4" />, badge: '500m' },
    { id: 'simulation', label: 'Spread Simulation', icon: <ActivityIcon className="w-4 h-4" />, badge: 'CA' },
    { id: 'active_fires', label: 'Active Hotspots', icon: <FlameIcon className="w-4 h-4" /> },
    { id: 'layers', label: 'Layers', icon: <LayersIcon className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-60 bg-ops-panel border-r border-ops-border flex flex-col shrink-0 select-none z-20 font-sans">
      <div className="p-3 border-b border-ops-border bg-ops-subtle">
        <span className="text-[11px] font-semibold tracking-wider text-txt-secondary uppercase font-mono">
          Operations Nav
        </span>
      </div>

      <nav className="flex-1 py-2 space-y-0.5">
        {navItems.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2 text-xs font-mono tracking-wider uppercase transition-colors text-left ${
                isActive
                  ? 'bg-ops-surface text-txt-primary border-l-2 border-forest font-semibold'
                  : 'text-txt-secondary hover:text-txt-primary hover:bg-ops-surface/50 border-l-2 border-transparent'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <span className={isActive ? 'text-forest' : 'text-txt-muted'}>{item.icon}</span>
                <span>{item.label}</span>
              </div>
            </button>
          );
        })}
      </nav>

      <div className="p-3 border-t border-ops-border bg-ops-subtle space-y-1 font-mono text-[10px] text-txt-muted">
        <div className="flex justify-between">
          <span>GRID:</span>
          <span className="text-txt-secondary">500M × 500M</span>
        </div>
        <div className="flex justify-between">
          <span>PROJECTION:</span>
          <span className="text-txt-secondary">EPSG:4326</span>
        </div>
      </div>
    </aside>
  );
};

