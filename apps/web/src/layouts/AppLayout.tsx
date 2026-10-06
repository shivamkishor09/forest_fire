import React from 'react';
import { Header } from '../components/layout/Header';
import { Navigation, NavTab } from '../components/layout/Navigation';
import { StatusBar } from '../components/layout/StatusBar';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { RegionSummary } from '../types/domain';

export interface AppLayoutProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  regions: RegionSummary[];
  selectedRegionId: string;
  onSelectRegion: (id: string) => void;
  isLoadingRegions?: boolean;
  selectedRegion?: RegionSummary | null;
  activeLayerName?: string;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  currentTab,
  onSelectTab,
  regions,
  selectedRegionId,
  onSelectRegion,
  isLoadingRegions = false,
  selectedRegion,
  activeLayerName,
  children,
}) => {
  const tabTitles: Record<NavTab, string> = {
    overview: 'Overview & Operational Status',
    risk: '24-Hour Fire Susceptibility',
    active_fires: 'Active Satellite Hotspots',
    simulation: '12-Hour Spread Simulation',
    layers: 'Environmental & Terrain Layers',
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-ops-bg overflow-hidden font-sans">
      <Header
        currentView={tabTitles[currentTab]}
        regions={regions}
        selectedRegionId={selectedRegionId}
        onSelectRegion={onSelectRegion}
        isLoadingRegions={isLoadingRegions}
      />
      <div className="flex-1 flex overflow-hidden relative">
        <Navigation currentTab={currentTab} onSelectTab={onSelectTab} />
        <main className="flex-1 flex flex-col overflow-hidden relative">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
      <StatusBar
        regionName={selectedRegion?.name}
        activeLayerName={activeLayerName || tabTitles[currentTab]}
      />
    </div>
  );
};
