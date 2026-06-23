import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  message: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<Props> = ({ message, onRetry }) => {
  return (
    <div className="glass-card border-severity-critical/30 p-4 animate-slide-up">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-severity-critical/10">
          <AlertTriangle className="w-5 h-5 text-severity-critical" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-severity-critical">Analysis Error</h4>
          <p className="text-xs text-slate-400 mt-1 break-words">{message}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium
                       rounded-lg bg-severity-critical/10 text-severity-critical
                       hover:bg-severity-critical/20 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        )}
      </div>
    </div>
  );
};
