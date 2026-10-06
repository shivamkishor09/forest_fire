import React, { useEffect } from 'react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxWidth?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  maxWidth = 'max-w-lg',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ops-bg/85 animate-fadeIn">
      <div
        className={`w-full ${maxWidth} bg-ops-panel border border-ops-border rounded-xs shadow-2xl overflow-hidden flex flex-col`}
        role="dialog"
        aria-modal="true"
      >
        <div className="px-4 py-3 border-b border-ops-border bg-ops-subtle flex items-center justify-between">
          <div className="text-xs font-semibold text-txt-primary uppercase tracking-wider">{title}</div>
          <button
            onClick={onClose}
            className="text-txt-muted hover:text-txt-primary transition-colors p-1 rounded-xs hover:bg-ops-surface"
            aria-label="Close dialog"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div className="p-4 flex-1 overflow-y-auto text-xs text-txt-secondary">{children}</div>
        {footer && (
          <div className="px-4 py-2.5 border-t border-ops-border bg-ops-subtle flex items-center justify-end space-x-2">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};
