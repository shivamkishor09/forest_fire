import React from 'react';

export const LoadingSpinner: React.FC<{ label?: string }> = ({ label = 'Loading geospatial data...' }) => (
  <div className="flex flex-col items-center justify-center p-8 space-y-3">
    <div className="w-8 h-8 border-4 border-forest/20 border-t-forest rounded-full animate-spin" />
    <span className="text-xs text-txt-secondary font-mono tracking-wide">{label}</span>
  </div>
);
