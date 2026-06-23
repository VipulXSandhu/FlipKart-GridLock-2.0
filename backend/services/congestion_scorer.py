"""
Congestion Scorer Service.
Calculates congestion severity with explicit parking-impact attribution,
so users can see exactly how much of the congestion is caused by
illegal/on-street parking.
"""

import logging
import math

logger = logging.getLogger(__name__)

CONGESTION_LEVELS = {
    "Low": (0, 25),
    "Medium": (26, 50),
    "High": (51, 75),
    "Critical": (76, 100),
}


class CongestionScorer:
    """Calculates congestion score with parking-impact decomposition."""

    def calculate(self, detection_result: dict, parking_result: dict) -> dict:
        """
        Calculate congestion score decomposed into parking-driven and
        volume-driven components.

        Factors:
            1. carriageway_blockage — direct road area lost to parked vehicles
            2. lane_reduction_impact — capacity lost from estimated lane reduction
            3. traffic_volume_pressure — moving vehicle volume vs remaining capacity

        The parking_impact_ratio tells the user what % of the total congestion
        is attributable to on-street parking.

        Args:
            detection_result: Output from VehicleDetector.
            parking_result: Output from ParkingIntelligence.

        Returns:
            Congestion score, level, factor breakdown, and parking impact ratio.
        """
        # ── Factor 1: Carriageway Blockage (0-40 points) ─────────────
        carriageway_blocked = parking_result.get("carriageway_blocked_pct", 0)
        blockage_score = carriageway_blocked * 40  # 100% blockage → 40 points

        # ── Factor 2: Lane Reduction Impact (0-30 points) ────────────
        lanes_lost = parking_result.get("estimated_lane_reduction", 0)
        # Each lane lost contributes proportionally (max 2 lanes = 30 pts)
        lane_reduction_score = min(lanes_lost * 15, 30)

        # ── Factor 3: Traffic Volume Pressure (0-30 points) ──────────
        # Weighted vehicle count (PCU — Passenger Car Units)
        weighted_moving = 0.0
        vehicles = detection_result.get("vehicles", [])
        for v in vehicles:
            if not v.get("is_parked", False):
                v_class = v.get("class", "car")
                if v_class == "truck":
                    weighted_moving += 2.5
                elif v_class == "bus":
                    weighted_moving += 3.0
                elif v_class == "motorcycle":
                    weighted_moving += 0.5
                elif v_class == "autorickshaw":
                    weighted_moving += 0.8
                else:
                    weighted_moving += 1.0

        # Available capacity = remaining carriageway after parking blockage
        available_capacity = max(1.0 - carriageway_blocked, 0.1)

        # Flow impedance — volume / capacity ratio
        flow_impedance = weighted_moving / available_capacity

        # Sigmoid-like mapping to 0-30 range
        volume_score = 30 * (1 - math.exp(-0.08 * flow_impedance))

        # ── Total Score ──────────────────────────────────────────────
        score = blockage_score + lane_reduction_score + volume_score
        score = min(round(score, 1), 100.0)

        # ── Parking Impact Ratio ─────────────────────────────────────
        # What fraction of the total score comes from parking-related factors?
        parking_driven = blockage_score + lane_reduction_score
        parking_impact_ratio = parking_driven / max(score, 0.1)
        parking_impact_ratio = min(round(parking_impact_ratio, 2), 1.0)

        # ── Level Classification ─────────────────────────────────────
        level = "Low"
        for lvl, (low, high) in CONGESTION_LEVELS.items():
            if low <= score <= high:
                level = lvl
                break

        factors = {
            "carriageway_blockage": round(blockage_score, 1),
            "lane_reduction_impact": round(lane_reduction_score, 1),
            "traffic_volume_pressure": round(volume_score, 1),
        }

        return {
            "score": score,
            "level": level,
            "factors": factors,
            "parking_impact_ratio": parking_impact_ratio,
            "flow_impedance": round(flow_impedance, 1),
        }
