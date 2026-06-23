import React, { useState } from 'react';
import { Eye, Layers, Flame, ImageOff } from 'lucide-react';
import type { AnalysisResponse, ImageViewMode, AppStatus } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ExecutiveSummary } from '../metrics/ExecutiveSummary';

interface Props {
  status: AppStatus;
  result: AnalysisResponse | null;
}

export const MainSection: React.FC<Props> = ({ status, result }) => {
  const [viewMode, setViewMode] = useState<ImageViewMode>('annotated');

  const isAnalyzing = status === 'analyzing' || status === 'uploading';

  const imageUrl = result
    ? viewMode === 'original'
      ? result.image.original_url
      : viewMode === 'heatmap'
        ? result.image.heatmap_url
        : result.image.annotated_url
    : null;

  return (
    <section className="flex-1 flex flex-col gap-3 min-w-0 p-4">
      <ExecutiveSummary result={result} />
      
      {/* View mode tabs */}
      {result && (
        <div className="flex items-center gap-1 self-start">
          {([
            { mode: 'original' as ImageViewMode, icon: Eye, label: 'Original' },
            { mode: 'annotated' as ImageViewMode, icon: Layers, label: 'Detected' },
            { mode: 'heatmap' as ImageViewMode, icon: Flame, label: 'Heatmap' },
          ]).map(({ mode, icon: Icon, label }) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200
                ${viewMode === mode
                  ? 'bg-accent-blue/20 text-accent-blue border border-accent-blue/30'
                  : 'text-slate-400 hover:text-slate-300 hover:bg-white/[0.03]'
                }`}
              id={`view-mode-${mode}`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Image viewer */}
      <div className="glass-card flex-1 flex items-center justify-center overflow-hidden relative min-h-[300px]">
        {isAnalyzing && <LoadingSpinner />}

        {status === 'idle' && !result && (
          <div className="flex flex-col items-center gap-4 text-center p-8 animate-fade-in">
            <div className="w-20 h-20 rounded-2xl bg-navy-700/50 flex items-center justify-center">
              <ImageOff className="w-10 h-10 text-slate-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-400">No Image Selected</p>
              <p className="text-xs text-slate-600 mt-1">
                Upload a traffic image or select a sample to begin analysis
              </p>
            </div>
          </div>
        )}

        {result && imageUrl && (
          <img
            src={imageUrl}
            alt={`${viewMode} view`}
            className="max-w-full max-h-full object-contain animate-fade-in rounded-lg"
            id="analysis-image-view"
          />
        )}
      </div>
    </section>
  );
};
