import React, { useState, useMemo } from 'react';
import { RegionSummary } from '../../../types/domain';
import { SearchIcon } from '../../../components/common/Icons';

export interface RegionSelectorProps {
  regions: RegionSummary[];
  selectedRegionId: string;
  onSelectRegion: (id: string) => void;
  isLoading?: boolean;
  className?: string;
}

export const RegionSelector: React.FC<RegionSelectorProps> = ({
  regions,
  selectedRegionId,
  onSelectRegion,
  isLoading = false,
  className = '',
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  const filteredRegions = useMemo(() => {
    if (!searchQuery.trim()) return regions;
    const q = searchQuery.toLowerCase();
    return regions.filter(
      (r) =>
        r.name.toLowerCase().includes(q) ||
        r.code.toLowerCase().includes(q) ||
        (r.state && r.state.toLowerCase().includes(q))
    );
  }, [regions, searchQuery]);

  return (
    <div className={`flex items-center space-x-1.5 ${className}`}>
      <span className="text-txt-muted text-xs hidden md:inline">Sector:</span>

      {showSearch ? (
        <div className="flex items-center space-x-1">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter sector..."
            className="w-32 sm:w-40 bg-ops-panel border border-ops-border rounded-[3px] px-2 py-1 text-xs text-txt-primary placeholder-txt-muted focus:outline-none focus:border-forest"
            autoFocus
          />
          <button
            type="button"
            onClick={() => {
              setSearchQuery('');
              setShowSearch(false);
            }}
            className="text-txt-muted hover:text-txt-primary text-xs px-1"
            title="Close Search"
          >
            ✕
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setShowSearch(true)}
          className="text-txt-muted hover:text-txt-primary p-1 rounded-[3px] hover:bg-ops-surface transition-colors hidden sm:inline-flex items-center"
          title="Filter Region List"
          aria-label="Filter regions"
        >
          <SearchIcon className="w-3.5 h-3.5" />
        </button>
      )}

      <select
        value={selectedRegionId}
        disabled={isLoading || regions.length === 0}
        onChange={(e) => onSelectRegion(e.target.value)}
        className="bg-ops-panel border border-ops-border rounded-[3px] px-2.5 py-1 text-xs text-txt-primary font-medium focus:outline-none focus:border-forest cursor-pointer disabled:opacity-50 max-w-[180px] sm:max-w-[240px] truncate"
        aria-label="Select Monitored Forest Region"
      >
        {regions.length === 0 ? (
          <option value="">{isLoading ? 'Loading regions...' : 'No regions'}</option>
        ) : filteredRegions.length === 0 ? (
          <option value="">No matches</option>
        ) : (
          filteredRegions.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))
        )}
      </select>
    </div>
  );
};

