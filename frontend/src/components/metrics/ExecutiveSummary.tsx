import React, { useState, useEffect } from 'react';
import { Bot } from 'lucide-react';
import type { AnalysisResponse } from '../../types';
import { VIOLATION_DISPLAY_NAMES } from '../../utils/constants';

interface Props {
  result: AnalysisResponse | null;
}

export const ExecutiveSummary: React.FC<Props> = ({ result }) => {
  const [displayedText, setDisplayedText] = useState('');
  
  useEffect(() => {
    if (!result) {
      setDisplayedText('');
      return;
    }

    // Generate the enforcement-focused summary
    const { detection, parking, congestion, hotspot, enforcement } = result;
    
    let summary = '';

    if (detection.total_vehicles === 0) {
      summary = 'Traffic scan complete. No vehicles detected in the immediate area.';
    } else {
      // ── Lead with the key question: illegal parking impact ──────
      const illegalCount = parking.illegal_parking_count;
      const totalParked = parking.parked_vehicles;
      const blockagePct = Math.round(parking.carriageway_blocked_pct * 100);
      const parkingImpactPct = Math.round(congestion.parking_impact_ratio * 100);
      const laneReduction = parking.estimated_lane_reduction;

      summary = `Detected ${detection.total_vehicles} vehicles — `;

      if (illegalCount > 0) {
        summary += `${illegalCount} of ${totalParked} parked vehicles are illegally parked. `;

        // Top violation type
        const violations = parking.violation_breakdown || {};
        const topViolation = Object.entries(violations).sort(([, a], [, b]) => b - a)[0];
        if (topViolation) {
          const violationName = VIOLATION_DISPLAY_NAMES[topViolation[0]] || topViolation[0];
          summary += `Most common violation: ${violationName} (${topViolation[1]} cases). `;
        }

        // Carriageway impact
        if (blockagePct > 0) {
          summary += `These vehicles block ${blockagePct}% of the carriageway`;
          if (laneReduction > 0) {
            summary += `, effectively reducing capacity by ~${laneReduction} lane${laneReduction > 1 ? 's' : ''}`;
          }
          summary += '. ';
        }

        // Parking → congestion attribution
        summary += `Parking accounts for ${parkingImpactPct}% of total congestion (score: ${Math.round(congestion.score)}/100). `;
      } else if (totalParked > 0) {
        summary += `${totalParked} vehicles parked legally with minimal traffic impact. `;
        summary += `Congestion score: ${Math.round(congestion.score)}/100. `;
      } else {
        summary += `all vehicles are moving. Congestion score: ${Math.round(congestion.score)}/100. `;
      }

      // ── Enforcement recommendation ─────────────────────────────
      if (enforcement.zone_targets && enforcement.zone_targets.length > 0) {
        const topZone = enforcement.zone_targets[0];
        summary += `Top enforcement target: ${topZone.region} (${topZone.illegal_count} violations, ${topZone.severity}). `;
      }

      // ── Final action call ──────────────────────────────────────
      if (enforcement.priority_rank <= 2) {
        summary += `⚡ ${enforcement.actions[0]}.`;
      } else if (enforcement.priority_rank === 3) {
        summary += `${enforcement.actions[0]}.`;
      } else {
        summary += 'Routine monitoring sufficient.';
      }
    }

    // Typing effect
    setDisplayedText('');
    let i = 0;
    const timer = setInterval(() => {
      setDisplayedText(summary.slice(0, i));
      i++;
      if (i > summary.length) {
        clearInterval(timer);
      }
    }, 20);

    return () => clearInterval(timer);
  }, [result]);

  if (!result) return null;

  // Determine border color based on illegal parking severity
  const borderColor = (result.parking.illegal_parking_count > 3)
    ? 'border-l-red-500'
    : (result.parking.illegal_parking_count > 0)
    ? 'border-l-amber-500'
    : 'border-l-accent-purple';

  return (
    <div className={`glass-card p-4 bg-gradient-to-r from-navy-800 to-navy-900 ${borderColor} border-l-4 mb-4 relative overflow-hidden`}>
      {/* Background decoration */}
      <div className="absolute -right-4 -top-4 opacity-5 pointer-events-none">
        <Bot className="w-32 h-32" />
      </div>
      
      <div className="flex items-start gap-3 relative z-10">
        <div className={`mt-1 p-2 rounded-lg ${
          result.parking.illegal_parking_count > 0
            ? 'bg-red-500/20'
            : 'bg-accent-purple/20'
        }`}>
          <Bot className={`w-5 h-5 ${
            result.parking.illegal_parking_count > 0
              ? 'text-red-400'
              : 'text-accent-purple'
          }`} />
        </div>
        <div className="flex-1">
          <h3 className="text-[11px] font-bold uppercase tracking-widest mb-1" style={{
            color: result.parking.illegal_parking_count > 0 ? '#f87171' : '#a78bfa'
          }}>
            {result.parking.illegal_parking_count > 0
              ? '🚨 Enforcement Intelligence Report'
              : '📊 AI Executive Summary'
            }
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed min-h-[40px]">
            {displayedText}
            <span className="inline-block w-1.5 h-4 ml-1 bg-accent-purple animate-pulse align-middle"></span>
          </p>
        </div>
      </div>
    </div>
  );
};
