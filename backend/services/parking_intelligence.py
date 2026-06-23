"""
Parking Intelligence Service.
Classifies parked vehicles as legal or illegal, estimates carriageway
blockage, and quantifies the spatial impact of parking on traffic flow.
"""

import logging
import math
from shapely.geometry import box
from shapely.ops import unary_union

logger = logging.getLogger(__name__)

# Density level thresholds
DENSITY_THRESHOLDS = {
    "Low": (0, 25),
    "Medium": (25, 50),
    "High": (50, 75),
    "Critical": (75, 100),
}

# Assumed standard lane width in pixels relative to image width
ASSUMED_LANES = 3  # typical urban road

# Perspective-aware carriageway polygon relative coordinates
# Defines a trapezoid mapping the active driving lanes into the horizon
# Order: bottom-left, bottom-right, top-right, top-left
CARRIAGEWAY_POLYGON_REL = [(0.15, 1.0), (0.85, 1.0), (0.55, 0.0), (0.45, 0.0)]


class ParkingIntelligence:
    """Analyzes parking patterns and classifies illegal parking from detection results."""

    def __init__(self, max_expected_vehicles: int = 30):
        self.max_expected_vehicles = max_expected_vehicles

    def analyze(self, detection_result: dict) -> dict:
        """
        Full parking analysis: occupancy, density, illegal classification,
        carriageway blockage, and lane reduction estimate.

        Args:
            detection_result: Output from VehicleDetector.detect()

        Returns:
            Parking analysis with illegal parking breakdown, blockage metrics,
            and density scoring.
        """
        vehicles = detection_result.get("vehicles", [])
        total = detection_result.get("total_vehicles", 0)
        img_width = detection_result.get("image_width", 1)
        img_height = detection_result.get("image_height", 1)

        if total == 0:
            return {
                "parked_vehicles": 0,
                "moving_vehicles": 0,
                "illegal_parking_count": 0,
                "legal_parking_count": 0,
                "violation_breakdown": {},
                "occupancy_rate": 0.0,
                "carriageway_blocked_pct": 0.0,
                "estimated_lane_reduction": 0,
                "density_score": 0.0,
                "density_level": "Low",
            }

        parked_vehicles = [v for v in vehicles if v.get("is_parked", False)]
        moving_vehicles = [v for v in vehicles if not v.get("is_parked", False)]
        parked = len(parked_vehicles)
        moving = len(moving_vehicles)

        # ── Classify each parked vehicle as legal or illegal ──────────
        # Generate the scaled polygon for the carriageway
        from shapely.geometry import Polygon
        scaled_coords = [(x * img_width, y * img_height) for x, y in CARRIAGEWAY_POLYGON_REL]
        carriageway_poly = Polygon(scaled_coords)

        self._classify_violations(parked_vehicles, moving_vehicles, img_width, img_height, carriageway_poly)

        illegal_vehicles = [v for v in parked_vehicles if v.get("parking_violation_type", "legal") != "legal"]
        legal_vehicles = [v for v in parked_vehicles if v.get("parking_violation_type", "legal") == "legal"]

        # Violation breakdown
        violation_breakdown = {}
        for v in illegal_vehicles:
            vtype = v.get("parking_violation_type", "unknown")
            violation_breakdown[vtype] = violation_breakdown.get(vtype, 0) + 1

        # ── Carriageway blockage ──────────────────────────────────────
        carriageway_area = carriageway_poly.area

        blocking_polys = []
        for v in parked_vehicles:
            b = v["bbox"]
            bbox_poly = box(b["x1"], b["y1"], b["x2"], b["y2"])
            intersection = carriageway_poly.intersection(bbox_poly)
            if not intersection.is_empty:
                blocking_polys.append(intersection)

        if blocking_polys:
            blocked_area = unary_union(blocking_polys).area
        else:
            blocked_area = 0.0

        carriageway_blocked_pct = min(blocked_area / max(carriageway_area, 1), 1.0)

        # Estimate lane reduction
        estimated_lane_reduction = 0
        if carriageway_blocked_pct > 0.05:
            estimated_lane_reduction = min(
                math.ceil(carriageway_blocked_pct * ASSUMED_LANES),
                ASSUMED_LANES - 1,  # At least 1 lane remains
            )

        # ── Occupancy rate (total parked area / usable road area) ─────
        image_area = img_width * img_height
        all_parked_boxes = []
        for v in parked_vehicles:
            b = v["bbox"]
            all_parked_boxes.append(box(b["x1"], b["y1"], b["x2"], b["y2"]))

        if all_parked_boxes:
            total_blocked_area = unary_union(all_parked_boxes).area
        else:
            total_blocked_area = 0.0

        occupancy_rate = min(total_blocked_area / max(image_area * 0.6, 1), 1.0)

        # ── Density score ─────────────────────────────────────────────
        count_factor = min(total / self.max_expected_vehicles, 1.0)
        parked_ratio = parked / max(total, 1)
        illegal_ratio = len(illegal_vehicles) / max(parked, 1)
        density_score = (
            count_factor * 0.3
            + parked_ratio * 0.2
            + occupancy_rate * 0.2
            + illegal_ratio * 0.15
            + carriageway_blocked_pct * 0.15
        ) * 100
        density_score = min(round(density_score, 1), 100.0)

        # Classify density level
        density_level = "Low"
        for level, (low, high) in DENSITY_THRESHOLDS.items():
            if low <= density_score < high:
                density_level = level
                break
        if density_score >= 75:
            density_level = "Critical"

        return {
            "parked_vehicles": parked,
            "moving_vehicles": moving,
            "illegal_parking_count": len(illegal_vehicles),
            "legal_parking_count": len(legal_vehicles),
            "violation_breakdown": violation_breakdown,
            "occupancy_rate": round(occupancy_rate, 3),
            "carriageway_blocked_pct": round(carriageway_blocked_pct, 3),
            "estimated_lane_reduction": estimated_lane_reduction,
            "density_score": density_score,
            "density_level": density_level,
        }

    def _classify_violations(
        self,
        parked_vehicles: list[dict],
        moving_vehicles: list[dict],
        img_width: int,
        img_height: int,
        carriageway_poly: any,
    ):
        """
        Tag each parked vehicle with a parking_violation_type and calculate its
        traffic_flow_impact_score.

        Rules (applied in priority order):
        1. no_parking_zone — parked inside the carriageway polygon
        2. double_parked — parked vehicle adjacent to another parked vehicle
           in the travel lane (both overlapping carriageway)
        3. carriageway_blocking — parked vehicle extends significantly into
           the travel lanes (>30% of its area inside carriageway)
        4. intersection_blocking — parked near many moving vehicles (chokepoint)
        5. legal — curbside parking completely outside the carriageway
        """
        from shapely.geometry import Point

        for v in parked_vehicles:
            b = v["bbox"]
            cx = (b["x1"] + b["x2"]) / 2
            cy = (b["y1"] + b["y2"]) / 2
            vw = b["x2"] - b["x1"]
            
            bbox_poly = box(b["x1"], b["y1"], b["x2"], b["y2"])
            intersection = carriageway_poly.intersection(bbox_poly)
            overlap_area = intersection.area if not intersection.is_empty else 0.0
            overlap_ratio = overlap_area / max(bbox_poly.area, 1.0)

            violation = "legal"
            impact_score = 0.0

            # Base impact from overlap
            impact_score += overlap_ratio * 30.0

            # Rule 1: Centroid is inside the carriageway polygon
            is_inside = carriageway_poly.contains(Point(cx, cy))
            if is_inside:
                # If the vast majority of it is in the road, it's parked in a no-parking zone (i.e. blocking a lane entirely)
                if overlap_ratio > 0.6:
                    violation = "no_parking_zone"
                    impact_score += 40.0

            # Rule 2: Double-parking detection
            if violation == "legal" and overlap_ratio > 0.2:
                # Check if there's another parked vehicle nearby
                for other in parked_vehicles:
                    if other["id"] == v["id"]:
                        continue
                    ob = other["bbox"]
                    # Vertically close and horizontally adjacent
                    vert_overlap = min(b["y2"], ob["y2"]) - max(b["y1"], ob["y1"])
                    horiz_gap = abs(cx - (ob["x1"] + ob["x2"]) / 2)
                    if vert_overlap > 0 and horiz_gap < vw * 2.5:
                        violation = "double_parked"
                        impact_score += 35.0
                        break

            # Rule 3: Carriageway blocking
            if violation == "legal" and overlap_ratio > 0.3:
                violation = "carriageway_blocking"
                impact_score += 20.0

            # Rule 4: Intersection blocking — near many moving vehicles
            nearby_moving = 0
            for mv in moving_vehicles:
                mb = mv["bbox"]
                mcx = (mb["x1"] + mb["x2"]) / 2
                mcy = (mb["y1"] + mb["y2"]) / 2
                dist = math.sqrt((cx - mcx) ** 2 + (cy - mcy) ** 2)
                proximity_threshold = max(img_width, img_height) * 0.12
                if dist < proximity_threshold:
                    nearby_moving += 1
                    # Impeding moving traffic adds dynamically to impact
                    impact_score += 15.0 * (1.0 - (dist / proximity_threshold))

            if violation == "legal" and nearby_moving >= 3:
                violation = "intersection_blocking"
                impact_score += 25.0

            v["parking_violation_type"] = violation
            
            # Cap impact score to 100 for normalization purposes
            v["traffic_flow_impact_score"] = min(round(impact_score, 1), 100.0)

