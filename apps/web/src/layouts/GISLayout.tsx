import React from 'react';

export interface GISLayoutProps {
  mapContent: React.ReactNode;
  topBar?: React.ReactNode;
  overlayPanels?: React.ReactNode;
  bottomBar?: React.ReactNode;
}

export const GISLayout: React.FC<GISLayoutProps> = ({
  mapContent,
  topBar,
  overlayPanels,
  bottomBar,
}) => {
  return (
    <div className="flex-1 flex flex-col h-full w-full overflow-hidden relative">
      {topBar && (
        <div className="shrink-0 z-10 bg-ops-panel border-b border-ops-border">
          {topBar}
        </div>
      )}

      <div className="flex-1 relative w-full h-full overflow-hidden">
        {/* Full map canvas */}
        {mapContent}

        {/* Floating overlays (inspectors, legends, filters) */}
        {overlayPanels && (
          <div className="pointer-events-none absolute inset-0 z-20 p-4">
            {overlayPanels}
          </div>
        )}

        {/* Bottom floating control (e.g. timeline) */}
        {bottomBar && (
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 w-full max-w-2xl px-4 pointer-events-auto">
            {bottomBar}
          </div>
        )}
      </div>
    </div>
  );
};
