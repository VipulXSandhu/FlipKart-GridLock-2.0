"""
Enforcement Ranking Service.
Generates enforcement priority recommendations based on analysis.
Provides both global priority and per-zone targeted enforcement.
"""

import logging
import math

logger = logging.getLogger(__name__)


ENFORCEMENT_LEVELS = [
    {
        "rank": 1,
        "label": "Priority 1",
        "severity": "Critical Congestion",
        "range": (76, 100),
        "recommendation": "Immediate enforcement required. Critical congestion impact detected with illegal parking significantly blocking active traffic flow.",
        "actions": [
            "Deploy parking enforcement officers immediately",
            "Target towing for vehicles directly blocking traffic lanes",
            "Issue digital parking violation notices",
            "Coordinate with traffic control room",
        ],
    },
    {
        "rank": 2,
        "label": "Priority 2",
        "severity": "High Congestion",
        "range": (51, 75),
        "recommendation": "Priority patrol dispatch recommended. High congestion impact from parked vehicles causing traffic flow disruption.",
        "actions": [
            "Dispatch enforcement patrol team",
            "Issue parking violation warnings and tickets",
            "Activate no-parking zone signage",
            "Monitor area for escalation of traffic impedance",
        ],
    },
    {
        "rank": 3,
        "label": "Priority 3",
        "severity": "Moderate Congestion",
        "range": (26, 50),
        "recommendation": "Scheduled monitoring advised. Moderate congestion impact with potential for traffic flow degradation.",
        "actions": [
            "Schedule periodic patrol rounds",
            "Document parking patterns and flow impedance",
            "Prepare enforcement resources",
        ],
    },
    {
        "rank": 4,
        "label": "Priority 4",
        "severity": "Low Congestion",
        "range": (0, 25),
        "recommendation": "Routine monitoring. Low congestion impact with minimal traffic flow disruption.",
        "actions": [
            "Routine area check during patrol",
            "Log for trend analysis",
        ],
    },
]

# Per-zone enforcement action templates keyed by severity
ZONE_ACTIONS = {
    "Critical": [
        "Deploy tow trucks to this zone immediately",
        "Issue violation notices to all illegally parked vehicles",
        "Set up temporary no-parking barriers",
    ],
    "High": [
        "Dispatch enforcement patrol to this zone",
        "Issue warnings and begin ticketing",
        "Activate digital no-parking signage",
    ],
    "Medium": [
        "Schedule patrol for this zone in next round",
        "Document parking violations for records",
    ],
    "Low": [
        "Include in routine patrol check",
    ],
}


class EnforcementRanker:
    """Generates enforcement priority rankings and recommendations."""

    def rank(self, congestion_result: dict, parking_result: dict, hotspot_result: dict = None) -> dict:
        """
        Generate enforcement priority based on congestion, parking, and hotspots.
        Also generates per-zone enforcement priorities.

        Formula:
            priority_score = (Congestion_Impact) * (Hotspot_Intensity) * weights

        Args:
            congestion_result: Output from CongestionScorer.
            parking_result: Output from ParkingIntelligence.
            hotspot_result: Output from hotspot classification.

        Returns:
            Enforcement priority with score, rank, recommendation, actions,
            and per-zone enforcement targets.
        """
        congestion_score = congestion_result.get("score", 0)
        parking_impact = congestion_result.get("parking_impact_ratio", 0)
        illegal_count = parking_result.get("illegal_parking_count", 0)
        carriageway_blocked = parking_result.get("carriageway_blocked_pct", 0)

        if hotspot_result:
            hotspot_intensity = hotspot_result.get("score", 0)
        else:
            # Fallback
            density_score = parking_result.get("density_score", 0)
            hotspot_intensity = density_score
            
        # Multi-Criteria Priority Index (Normalized to 100)
        # Using a multiplicative model to emphasize the interaction between congestion and clustering
        # P = sqrt(Congestion * Hotspot) ensures it scales 0-100
        priority_score = math.sqrt((congestion_score / 100.0) * (hotspot_intensity / 100.0)) * 100
        priority_score = min(round(priority_score, 1), 100.0)

        # Match to enforcement level
        matched = ENFORCEMENT_LEVELS[-1]  # Default to lowest
        for level in ENFORCEMENT_LEVELS:
            low, high = level["range"]
            if low <= priority_score <= high:
                matched = level
                break

        # ── Build contextual recommendation ──────────────────────────
        # Override the generic template with data-driven insights
        if illegal_count > 0:
            context_rec = (
                f"{matched['recommendation']} "
                f"{illegal_count} illegal parking violation(s) detected, "
                f"blocking {round(carriageway_blocked * 100, 1)}% of the carriageway. "
                f"Parking accounts for {round(parking_impact * 100)}% of total congestion."
            )
        else:
            context_rec = matched["recommendation"]

        # ── Per-zone enforcement targets ─────────────────────────────
        zone_enforcement = []
        if hotspot_result and hotspot_result.get("zones"):
            for zone in hotspot_result["zones"]:
                zone_severity = zone.get("severity", "Low")
                zone_illegal = zone.get("illegal_count", 0)
                zone_actions = ZONE_ACTIONS.get(zone_severity, ZONE_ACTIONS["Low"])

                zone_enforcement.append({
                    "zone_id": zone["zone_id"],
                    "region": zone.get("region", "Unknown"),
                    "severity": zone_severity,
                    "illegal_count": zone_illegal,
                    "vehicle_count": zone.get("vehicle_count", 0),
                    "actions": zone_actions,
                    "priority_label": f"Zone P{1 if zone_severity == 'Critical' else 2 if zone_severity == 'High' else 3 if zone_severity == 'Medium' else 4}",
                })

        return {
            "priority_score": priority_score,
            "priority_rank": matched["rank"],
            "recommendation": context_rec,
            "actions": matched["actions"],
            "zone_targets": zone_enforcement,
        }
