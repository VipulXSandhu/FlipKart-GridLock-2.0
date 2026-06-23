import React from 'react';
import type { HotspotZone } from '../../types';

interface Props {
  zones: HotspotZone[];
}

export const ZoneMiniMap: React.FC<Props> = ({ zones }) => {
  // Define a 3x3 grid
  const grid = [
    { id: 1, region: 'top-left', col: 0, row: 0 },
    { id: 2, region: 'top-center', col: 1, row: 0 },
    { id: 3, region: 'top-right', col: 2, row: 0 },
    { id: 4, region: 'center-left', col: 0, row: 1 },
    { id: 5, region: 'center', col: 1, row: 1 },
    { id: 6, region: 'center-right', col: 2, row: 1 },
    { id: 7, region: 'bottom-left', col: 0, row: 2 },
    { id: 8, region: 'bottom-center', col: 1, row: 2 },
    { id: 9, region: 'bottom-right', col: 2, row: 2 },
  ];

  // Map DBSCAN cluster centroids into the 3x3 grid
  // center_x / center_y are pixel coordinates; we normalize to 0-1 range
  // and assign to grid cells
  const getGridCell = (zone: HotspotZone): number => {
    const cx = zone.center_x ?? 0.5;
    const cy = zone.center_y ?? 0.5;
    // Normalize: assume center_x/center_y are relative or large pixel values
    // Use a heuristic: values > 1 are pixel coords, normalize to 0-1
    const normX = cx > 1 ? Math.min(cx / 1920, 1) : cx; // assume max ~1920px width
    const normY = cy > 1 ? Math.min(cy / 1080, 1) : cy; // assume max ~1080px height
    const col = Math.min(Math.floor(normX * 3), 2);
    const row = Math.min(Math.floor(normY * 3), 2);
    return row * 3 + col + 1; // 1-indexed grid ID
  };

  // Build a map of grid cell ID → best (highest severity) zone
  const cellZoneMap = new Map<number, HotspotZone>();
  const severityOrder: Record<string, number> = { Critical: 4, High: 3, Medium: 2, Low: 1 };

  for (const zone of zones) {
    if (zone.center_x == null || zone.center_y == null) continue;
    const cellId = getGridCell(zone);
    const existing = cellZoneMap.get(cellId);
    if (!existing || (severityOrder[zone.severity] || 0) > (severityOrder[existing.severity] || 0)) {
      cellZoneMap.set(cellId, zone);
    }
  }

  const getZoneSeverityInfo = (cellId: number) => {
    const zone = cellZoneMap.get(cellId);
    if (!zone) return { color: 'bg-navy-800/50', border: 'border-white/5', opacity: 'opacity-50', label: '' };
    
    const count = zone.vehicle_count ?? 0;
    const label = count > 0 ? `${count}` : '';

    switch (zone.severity) {
      case 'Critical': return { color: 'bg-severity-critical/30', border: 'border-severity-critical/50', opacity: 'animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.4)]', label };
      case 'High': return { color: 'bg-severity-high/30', border: 'border-severity-high/50', opacity: '', label };
      case 'Medium': return { color: 'bg-severity-medium/30', border: 'border-severity-medium/50', opacity: '', label };
      case 'Low': return { color: 'bg-severity-low/30', border: 'border-severity-low/50', opacity: '', label };
      default: return { color: 'bg-navy-800/50', border: 'border-white/5', opacity: 'opacity-50', label: '' };
    }
  };

  return (
    <div className="glass-card p-4 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Live Zone Map
        </h3>
      </div>
      
      <div className="flex-1 flex items-center justify-center">
        <div className="grid grid-cols-3 gap-2 w-full max-w-[200px] aspect-square">
          {grid.map((cell) => {
            const style = getZoneSeverityInfo(cell.id);
            return (
              <div 
                key={cell.id} 
                className={`rounded-md border ${style.border} ${style.color} ${style.opacity} transition-all duration-500 relative group flex items-center justify-center`}
              >
                {style.label && (
                  <span className="text-[10px] font-bold text-white/70">{style.label}</span>
                )}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-navy-900/80 rounded-md text-[10px] text-white font-bold text-center p-1">
                  {cell.region.replace('-', ' ')}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
