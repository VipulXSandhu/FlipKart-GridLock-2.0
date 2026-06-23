import React, { useCallback, useState, useRef } from 'react';
import { Upload, Image as ImageIcon, Camera } from 'lucide-react';
import type { SampleImage } from '../../types';
import { MAX_FILE_SIZE_MB } from '../../utils/constants';

interface Props {
  samples: SampleImage[];
  onFileSelect: (file: File) => void;
  onSampleSelect: (sampleId: string) => void;
  disabled: boolean;
}

export const LeftPanel: React.FC<Props> = ({ samples, onFileSelect, onSampleSelect, disabled }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) {
        if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
          alert(`File too large. Max size: ${MAX_FILE_SIZE_MB}MB`);
          return;
        }
        onFileSelect(file);
      }
    },
    [disabled, onFileSelect],
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
          alert(`File too large. Max size: ${MAX_FILE_SIZE_MB}MB`);
          return;
        }
        onFileSelect(file);
      }
      e.target.value = '';
    },
    [onFileSelect],
  );

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col gap-4 p-4 overflow-y-auto">
      {/* Upload Zone */}
      <div className="glass-card hover-lift p-4">
        <div className="flex items-center gap-2 mb-3">
          <Upload className="w-4 h-4 text-accent-blue" />
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Upload Image</h3>
        </div>

        <div
          className={`upload-zone p-6 flex flex-col items-center gap-3 text-center
                     ${isDragOver ? 'drag-over' : ''} ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="w-12 h-12 rounded-xl bg-accent-blue/10 flex items-center justify-center">
            <Camera className="w-6 h-6 text-accent-blue" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-300">
              {isDragOver ? 'Drop image here' : 'Drag & drop or click'}
            </p>
            <p className="text-[10px] text-slate-500 mt-1">JPG, PNG, WebP • Max {MAX_FILE_SIZE_MB}MB</p>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileInput}
          className="hidden"
          id="image-upload-input"
        />
      </div>

      {/* Sample Images */}
      {samples.length > 0 && (
        <div className="glass-card hover-lift p-4">
          <div className="flex items-center gap-2 mb-3">
            <ImageIcon className="w-4 h-4 text-accent-purple" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Sample Images</h3>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {samples.map((sample) => (
              <button
                key={sample.id}
                onClick={() => onSampleSelect(sample.id)}
                disabled={disabled}
                className="group relative aspect-[4/3] rounded-lg overflow-hidden border border-white/[0.06]
                           hover:border-accent-purple/40 transition-all duration-300 disabled:opacity-50"
                id={`sample-btn-${sample.id}`}
              >
                <img
                  src={sample.thumbnail_url}
                  alt={sample.name}
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent
                                opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <span className="absolute bottom-1 left-1 right-1 text-[9px] text-white font-medium
                                 opacity-0 group-hover:opacity-100 transition-opacity duration-300 truncate">
                  {sample.name}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
};
