import React, { useEffect, useState } from 'react';
import { apiClient } from '../services/apiClient';
import { SystemHealth } from '../types';
import { FlameIcon } from './common/Icons';

interface HeaderProps {
  currentView: string;
}

export const Header: React.FC<HeaderProps> = ({ currentView }) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [online, setOnline] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    apiClient
      .getHealth()
      .then((data) => {
        if (mounted) {
          setHealth(data);
          setOnline(data.status === 'healthy');
        }
      })
      .catch(() => {
        if (mounted) setOnline(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="h-10 bg-ops-panel border-b border-ops-border flex items-center justify-between px-4 select-none shrink-0 z-30 font-mono">
      <div className="flex items-center space-x-3">
        <div className="w-6 h-6 rounded-xs bg-forest flex items-center justify-center text-txt-primary">
          <FlameIcon className="w-3.5 h-3.5 text-txt-primary" />
        </div>
        <div>
          <h1 className="font-semibold text-xs text-txt-primary uppercase tracking-wider">
            Wildfire Operations Platform
          </h1>
          <p className="text-[10px] text-txt-muted">Spatial Risk & Spread Modeling</p>
        </div>
      </div>

      <div className="flex items-center space-x-3 text-xs">
        <span className="text-txt-secondary uppercase tracking-wider text-[10px] px-2 py-0.5 bg-ops-surface rounded-xs border border-ops-border">
          {currentView}
        </span>
        <div className="flex items-center space-x-2 bg-ops-surface px-2.5 py-1 rounded-xs border border-ops-border">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              online ? 'bg-forest' : 'bg-danger'
            }`}
          />
          <span className="text-txt-secondary font-mono text-[10px]">
            {online ? `API v${health?.version || '1.0'}` : 'OFFLINE'}
          </span>
        </div>
      </div>
    </header>
  );
};

