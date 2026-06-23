"""
Image Processing Service.
Handles annotation overlay drawing on detected images using OpenCV.
Color-codes vehicles by parking violation type and generates
violation-weighted heatmaps.
"""

import logging
import cv2
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# Color palette for vehicle classes (BGR format for OpenCV)
VEHICLE_COLORS = {
    "car": (78, 205, 196),       # Teal
    "autorickshaw": (153, 255, 153), # Light green
    "truck": (255, 107, 107),    # Coral
    "bus": (255, 195, 0),        # Amber
    "motorcycle": (162, 155, 254), # Lavender
    "other": (200, 200, 200),    # Gray
}

# Violation-specific annotation colors (BGR)
VIOLATION_COLORS = {
    "no_parking_zone": (0, 0, 230),        # Bright red
    "double_parked": (0, 50, 255),          # Orange-red
    "carriageway_blocking": (0, 100, 255),  # Orange
    "intersection_blocking": (0, 165, 255), # Orange-yellow
    "legal": (0, 180, 0),                   # Green
}

# Human-readable violation labels for annotation
VIOLATION_LABELS = {
    "no_parking_zone": "NO-PARK ZONE",
    "double_parked": "DOUBLE PARKED",
    "carriageway_blocking": "BLOCKING ROAD",
    "intersection_blocking": "INTERSECT BLOCK",
    "legal": "LEGAL",
}

# Severity colors
SEVERITY_COLORS = {
    "Low": (0, 200, 83),         # Green
    "Medium": (255, 195, 0),     # Yellow
    "High": (255, 152, 0),       # Orange
    "Critical": (244, 67, 54),   # Red
}


class ImageProcessor:
    """Handles image annotation, heatmap generation, and overlays."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def draw_annotations(
        self,
        image_path: str,
        vehicles: list[dict],
        analysis_id: str,
    ) -> str:
        """
        Draw bounding boxes and labels on the detected image.
        Color-codes by violation type for parked vehicles.

        Args:
            image_path: Path to original image.
            vehicles: List of detected vehicles with bbox and metadata.
            analysis_id: Unique ID for this analysis run.

        Returns:
            Path to the annotated image.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        img_height, img_width = img.shape[:2]

        # Draw a semi-transparent overlay panel at the top
        overlay = img.copy()

        # ── Draw carriageway corridor boundaries ─────────────────────
        try:
            from services.parking_intelligence import CARRIAGEWAY_POLYGON_REL
            scaled_coords = np.array([
                [int(x * img_width), int(y * img_height)]
                for x, y in CARRIAGEWAY_POLYGON_REL
            ], dtype=np.int32)
        except Exception as e:
            logger.error(f"Failed to load CARRIAGEWAY_POLYGON_REL: {e}")
            scaled_coords = np.array([
                [int(img_width * 0.20), img_height],
                [int(img_width * 0.80), img_height],
                [int(img_width * 0.80), 0],
                [int(img_width * 0.20), 0]
            ], dtype=np.int32)

        corridor_overlay = overlay.copy()
        # Semi-transparent blue polygon outline
        cv2.polylines(corridor_overlay, [scaled_coords], isClosed=True,
                      color=(255, 200, 50), thickness=2, lineType=cv2.LINE_AA)
        # Label the carriageway at the bottom center of the polygon
        font = cv2.FONT_HERSHEY_SIMPLEX
        label_scale = max(0.35, min(img_width, img_height) / 2000)
        center_x = int((scaled_coords[0][0] + scaled_coords[1][0]) / 2)
        center_y = int(img_height - 30)
        cv2.putText(corridor_overlay, "CARRIAGEWAY", 
                    (center_x - 60, center_y),
                    font, label_scale, (255, 200, 50), 2, cv2.LINE_AA)
        overlay = cv2.addWeighted(corridor_overlay, 0.7, overlay, 0.3, 0)

        for vehicle in vehicles:
            bbox = vehicle["bbox"]
            x1, y1 = int(bbox["x1"]), int(bbox["y1"])
            x2, y2 = int(bbox["x2"]), int(bbox["y2"])
            vehicle_class = vehicle.get("class", "other")
            confidence = vehicle.get("confidence", 0)
            is_parked = vehicle.get("is_parked", False)
            violation_type = vehicle.get("parking_violation_type", "")

            # Determine color based on violation type for parked vehicles
            if is_parked and violation_type and violation_type != "legal":
                # Illegal parking — use violation color
                color = VIOLATION_COLORS.get(violation_type, (0, 0, 255))
            elif is_parked and violation_type == "legal":
                # Legal parking — green
                color = VIOLATION_COLORS["legal"]
            elif is_parked:
                # Parked but no violation type set yet
                color = (80, 80, 255)  # Red-ish for parked
            else:
                # Moving vehicle — use class color
                color = VEHICLE_COLORS.get(vehicle_class, VEHICLE_COLORS["other"])

            # Draw bounding box
            thickness = max(2, int(min(img_width, img_height) / 400))
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, thickness)

            # Build label text
            label = f"{vehicle_class} {confidence:.0%}"
            if is_parked:
                if violation_type and violation_type != "legal":
                    viol_label = VIOLATION_LABELS.get(violation_type, violation_type.upper())
                    label += f" [{viol_label}]"
                elif violation_type == "legal":
                    label += " [LEGAL P]"
                else:
                    label += " [P]"

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(0.4, min(img_width, img_height) / 1500)
            text_thickness = max(1, int(font_scale * 2))
            (text_w, text_h), baseline = cv2.getTextSize(
                label, font, font_scale, text_thickness
            )

            # Label background
            cv2.rectangle(
                overlay,
                (x1, y1 - text_h - 10),
                (x1 + text_w + 8, y1),
                color,
                -1,
            )

            # Label text
            cv2.putText(
                overlay,
                label,
                (x1 + 4, y1 - 5),
                font,
                font_scale,
                (255, 255, 255),
                text_thickness,
                cv2.LINE_AA,
            )

            # Draw corner accents for a modern look
            corner_len = max(10, int(min(x2 - x1, y2 - y1) * 0.15))
            corner_thickness = thickness + 1

            # Top-left corner
            cv2.line(overlay, (x1, y1), (x1 + corner_len, y1), color, corner_thickness)
            cv2.line(overlay, (x1, y1), (x1, y1 + corner_len), color, corner_thickness)
            # Top-right corner
            cv2.line(overlay, (x2, y1), (x2 - corner_len, y1), color, corner_thickness)
            cv2.line(overlay, (x2, y1), (x2, y1 + corner_len), color, corner_thickness)
            # Bottom-left corner
            cv2.line(overlay, (x1, y2), (x1 + corner_len, y2), color, corner_thickness)
            cv2.line(overlay, (x1, y2), (x1, y2 - corner_len), color, corner_thickness)
            # Bottom-right corner
            cv2.line(overlay, (x2, y2), (x2 - corner_len, y2), color, corner_thickness)
            cv2.line(overlay, (x2, y2), (x2, y2 - corner_len), color, corner_thickness)

        # Blend overlay with original for semi-transparent boxes
        alpha = 0.85
        result = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

        # Draw summary bar at top
        result = self._draw_summary_bar(result, vehicles)

        # Save annotated image
        output_path = self.output_dir / f"{analysis_id}_annotated.jpg"
        cv2.imwrite(str(output_path), result, [cv2.IMWRITE_JPEG_QUALITY, 92])
        logger.info(f"Annotated image saved: {output_path}")

        return str(output_path)

    def _draw_summary_bar(self, img: np.ndarray, vehicles: list[dict]) -> np.ndarray:
        """Draw a summary info bar at the top of the annotated image."""
        img_height, img_width = img.shape[:2]
        bar_height = max(36, int(img_height * 0.04))

        # Create semi-transparent black bar
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (img_width, bar_height), (20, 20, 30), -1)
        img = cv2.addWeighted(overlay, 0.8, img, 0.2, 0)

        total = len(vehicles)
        parked = sum(1 for v in vehicles if v.get("is_parked", False))
        moving = total - parked
        illegal = sum(
            1 for v in vehicles
            if v.get("is_parked", False)
            and v.get("parking_violation_type", "legal") != "legal"
        )

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.4, bar_height / 80)
        text_y = int(bar_height * 0.7)

        # Title
        cv2.putText(
            img,
            "AI-ParkSense",
            (10, text_y),
            font,
            font_scale,
            (56, 189, 248),  # Sky blue
            max(1, int(font_scale * 2)),
            cv2.LINE_AA,
        )

        # Stats — now includes illegal count
        stats = f"Vehicles: {total}  |  Parked: {parked}  |  Illegal: {illegal}  |  Moving: {moving}"
        text_x = int(img_width * 0.30)
        cv2.putText(
            img,
            stats,
            (text_x, text_y),
            font,
            font_scale,
            (241, 245, 249),  # Light gray
            max(1, int(font_scale * 2)),
            cv2.LINE_AA,
        )

        return img

    def generate_heatmap(
        self,
        image_path: str,
        vehicles: list[dict],
        analysis_id: str,
    ) -> str:
        """
        Generate a congestion-impact-weighted heatmap overlay.
        Parked vehicles are weighted by their traffic_flow_impact_score.
        Moving vehicles are faintly drawn to visualize the flow intersection.

        Args:
            image_path: Path to original image.
            vehicles: List of detected vehicles.
            analysis_id: Unique ID for this analysis.

        Returns:
            Path to the heatmap image.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        img_height, img_width = img.shape[:2]

        # Create separate heatmaps for congestion impact and traffic flow
        heatmap_impact = np.zeros((img_height, img_width), dtype=np.float32)
        heatmap_flow = np.zeros((img_height, img_width), dtype=np.float32)

        for vehicle in vehicles:
            is_parked = vehicle.get("is_parked", False)
            bbox = vehicle["bbox"]
            cx = int((bbox["x1"] + bbox["x2"]) / 2)
            cy = int((bbox["y1"] + bbox["y2"]) / 2)
            radius = int(max(bbox["x2"] - bbox["x1"], bbox["y2"] - bbox["y1"]) * 0.8)

            # Create Gaussian kernel
            y_coords, x_coords = np.ogrid[
                max(0, cy - radius): min(img_height, cy + radius),
                max(0, cx - radius): min(img_width, cx + radius),
            ]

            if y_coords.size == 0 or x_coords.size == 0:
                continue

            dist_sq = (x_coords - cx) ** 2 + (y_coords - cy) ** 2
            gaussian = np.exp(-dist_sq / (2 * (radius / 2) ** 2))

            y_start = max(0, cy - radius)
            y_end = min(img_height, cy + radius)
            x_start = max(0, cx - radius)
            x_end = min(img_width, cx + radius)

            if is_parked:
                # Weight by traffic_flow_impact_score. Base weight = 1.0, max weight ~ 10.0
                impact_score = vehicle.get("traffic_flow_impact_score", 0)
                weight = 1.0 + (impact_score / 10.0)
                heatmap_impact[y_start:y_end, x_start:x_end] += gaussian.astype(np.float32) * weight
            else:
                # Moving vehicles form the traffic flow lines (faint)
                heatmap_flow[y_start:y_end, x_start:x_end] += gaussian.astype(np.float32) * 1.5

        # Normalize both
        if heatmap_impact.max() > 0:
            heatmap_impact = heatmap_impact / heatmap_impact.max()
        if heatmap_flow.max() > 0:
            heatmap_flow = heatmap_flow / heatmap_flow.max()

        # Impact → HOT (red-orange) colormap
        impact_colored = cv2.applyColorMap(
            (heatmap_impact * 255).astype(np.uint8), cv2.COLORMAP_HOT
        )

        # Flow → COOL (ocean/blue) colormap
        flow_colored = cv2.applyColorMap(
            (heatmap_flow * 255).astype(np.uint8), cv2.COLORMAP_OCEAN
        )

        # Blend: Impact is prioritized over flow
        heatmap_colored = cv2.addWeighted(impact_colored, 0.7, flow_colored, 0.4, 0)

        # Blend with original image
        result = cv2.addWeighted(img, 0.5, heatmap_colored, 0.5, 0)

        # Add legend overlay
        result = self._draw_heatmap_legend(result)

        # Save
        output_path = self.output_dir / f"{analysis_id}_heatmap.jpg"
        cv2.imwrite(str(output_path), result, [cv2.IMWRITE_JPEG_QUALITY, 92])
        logger.info(f"Heatmap saved: {output_path}")

        return str(output_path)

    def _draw_heatmap_legend(self, img: np.ndarray) -> np.ndarray:
        """Draw a small legend on the heatmap explaining the color scheme."""
        img_height, img_width = img.shape[:2]
        legend_h = 50
        legend_w = 230
        x_start = img_width - legend_w - 10
        y_start = img_height - legend_h - 10

        # Semi-transparent background
        overlay = img.copy()
        cv2.rectangle(overlay, (x_start, y_start),
                      (x_start + legend_w, y_start + legend_h),
                      (20, 20, 30), -1)
        img = cv2.addWeighted(overlay, 0.8, img, 0.2, 0)

        font = cv2.FONT_HERSHEY_SIMPLEX
        fs = 0.35

        # High Impact
        cv2.rectangle(img, (x_start + 8, y_start + 8),
                      (x_start + 22, y_start + 18), (0, 0, 255), -1)
        cv2.putText(img, "High Congestion Impact",
                    (x_start + 28, y_start + 17), font, fs,
                    (220, 220, 220), 1, cv2.LINE_AA)

        # Traffic Flow
        cv2.rectangle(img, (x_start + 8, y_start + 28),
                      (x_start + 22, y_start + 38), (200, 120, 0), -1)
        cv2.putText(img, "Moving Traffic Flow",
                    (x_start + 28, y_start + 37), font, fs,
                    (180, 180, 180), 1, cv2.LINE_AA)

        return img

    def save_original(self, image_path: str, analysis_id: str) -> str:
        """Copy original image to output directory."""
        import shutil

        output_path = self.output_dir / f"{analysis_id}_original.jpg"
        shutil.copy2(image_path, str(output_path))
        return str(output_path)
