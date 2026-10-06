import React, { useEffect, useState } from 'react';
import { fetchHealth } from '../../services/api/health';
import { SystemHealth } from '../../types/api';
import { RegionSummary } from '../../types/domain';
import { RegionSelector } from '../../features/regions/components/RegionSelector';
import { FlameIcon } from '../common/Icons';

export interface HeaderProps {
  currentView: string;
  regions: RegionSummary[];
  selectedRegionId: string;
  onSelectRegion: (id: string) => void;
  isLoadingRegions?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentView: _currentView,
  regions,
  selectedRegionId,
  onSelectRegion,
  isLoadingRegions = false,
}) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [online, setOnline] = useState<boolean>(true);
  const [times, setTimes] = useState<{ utc: string; local: string }>(() => {
    const now = new Date();
    return {
      utc: now.toISOString().slice(11, 19),
      local: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }),
    };
  });

  useEffect(() => {
    let mounted = true;
    fetchHealth()
      .then((data) => {
        if (mounted) {
          setHealth(data);
          setOnline(data.status === 'healthy');
        }
      })
      .catch(() => {
        if (mounted) setOnline(false);
      });

    if (import.meta.env?.MODE !== 'test') {
      const timer = setInterval(() => {
        if (mounted) {
          const now = new Date();
          setTimes({
            utc: now.toISOString().slice(11, 19),
            local: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }),
          });
        }
      }, 1000);

      return () => {
        mounted = false;
        clearInterval(timer);
      };
    }

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="h-12 bg-ops-subtle border-b border-ops-border flex items-center justify-between px-4 select-none shrink-0 z-30">
      {/* LEFT: System Title & Operational Descriptor */}
      <div className="flex items-center space-x-3">
        <div className="w-7 h-7 rounded-[3px] bg-forest/20 border border-forest/40 flex items-center justify-center text-forest">
          <FlameIcon className="w-4 h-4" />
        </div>
        <div>
          <div className="text-[14px] font-semibold text-txt-primary tracking-tight leading-tight">
            Wildfire Operations Platform
          </div>
          <div className="text-[11px] text-txt-muted leading-tight">
            Predictive Fire Risk & Spread Modeling · ISRO Forest Fire Platform
          </div>
        </div>
      </div>

      {/* CENTER: Operational UTC / Local Clock & Horizon */}
      <div className="hidden md:flex items-center space-x-3 font-mono text-[11px] text-txt-secondary">
        <span className="text-txt-primary font-medium">{times.utc} UTC</span>
        <span className="text-ops-border">/</span>
        <span>{times.local} Local</span>
        <span className="text-ops-border">/</span>
        <span className="text-amber font-semibold">24H Horizon</span>
      </div>

      {/* RIGHT: Region Selector & Operational Status */}
      <div className="flex items-center space-x-3">
        <RegionSelector
          regions={regions}
          selectedRegionId={selectedRegionId}
          onSelectRegion={onSelectRegion}
          isLoading={isLoadingRegions}
        />

        {/* Operational Status */}
        <div
          className="flex items-center space-x-2 pl-2 border-l border-ops-border"
          title={`Backend Services: ${health?.status || 'Connected'}`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              online ? 'bg-forest' : 'bg-danger'
            }`}
          />
          <span className="font-mono text-[11px] font-semibold tracking-wider text-txt-primary">
            {online ? 'OPERATIONAL' : 'OFFLINE'}
          </span>
        </div>
      </div>
    </header>
  );
};

