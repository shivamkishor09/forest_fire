import React from 'react';
import { Header } from '../components/Header';
import { Sidebar, NavTab } from '../components/Sidebar';
import { ErrorBoundary } from '../components/ErrorBoundary';

interface MainLayoutProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  currentTab,
  onSelectTab,
  children,
}) => {
  const tabTitles: Record<NavTab, string> = {
    overview: 'Overview & Metrics',
    risk: '24-Hour Fire Susceptibility',
    simulation: '12-Hour Fire Spread Simulation',
    active_fires: 'Active Satellite Hotspots',
    layers: 'Environmental & Terrain Layers',
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-ops-bg overflow-hidden font-sans">
      <Header currentView={tabTitles[currentTab]} />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar currentTab={currentTab} onSelectTab={onSelectTab} />
        <main className="flex-1 flex flex-col overflow-hidden relative">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
};
