"""
Vehicle Detection Service using YOLOv8.
Detects vehicles in traffic images and classifies them.
"""

import logging
from pathlib import Path
from ultralytics import YOLO
import numpy as np
import cv2

logger = logging.getLogger(__name__)

# COCO class IDs for vehicles
VEHICLE_CLASSES = {
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Extended mapping for display
VEHICLE_DISPLAY_NAMES = {
    "bicycle": "Bicycle",
    "car": "Car",
    "autorickshaw": "Autorickshaw",
    "motorcycle": "Motorcycle",
    "bus": "Bus",
    "truck": "Truck",
}


class VehicleDetector:
    """YOLOv8-based vehicle detection service."""

    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.35):
        self.model_name = model_name
        self.confidence = confidence
        self.iou_threshold = 0.45
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load YOLOv8 model (downloads on first run)."""
        try:
            self.model = YOLO(self.model_name)
            logger.info(f"YOLOv8 model '{self.model_name}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            raise

    def detect(self, image_path: str) -> dict:
        """
        Run vehicle detection on an image.

        Args:
            image_path: Path to the input image.

        Returns:
            Dictionary with detection results including vehicles,
            bounding boxes, confidence scores, and breakdown.
        """
        if self.model is None:
            raise RuntimeError("YOLOv8 model is not loaded.")

        # Run inference
        results = self.model(
            image_path,
            conf=self.confidence,
            iou=self.iou_threshold,
            verbose=False,
        )

        # Get image dimensions first for heuristics
        img_shape = results[0].orig_shape if results else (0, 0)
        img_height, img_width = img_shape[0], img_shape[1]

        # Load image with OpenCV for color heuristics
        cv_img = cv2.imread(image_path)
        hsv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV) if cv_img is not None else None

        vehicles = []
        breakdown = {"light_vehicles": 0, "heavy_vehicles": 0, "motorcycles": 0, "other": 0}
        vehicle_id = 0

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())

                # Filter to vehicle classes only
                if cls_id not in VEHICLE_CLASSES:
                    continue

                vehicle_class = VEHICLE_CLASSES[cls_id]
                conf = float(boxes.conf[i].item())
                x1, y1, x2, y2 = boxes.xyxy[i].tolist()

                # --- Improved Autorickshaw & Vehicle Heuristics ---
                width = x2 - x1
                height = y2 - y1
                aspect_ratio = width / max(height, 1.0)
                vehicle_area = width * height
                image_area = img_width * img_height if img_width > 0 else 1

                if vehicle_class in ["car", "truck"] and hsv_img is not None:
                    # Safe cropping
                    y1_c, y2_c = max(0, int(y1)), min(img_height, int(y2))
                    x1_c, x2_c = max(0, int(x1)), min(img_width, int(x2))
                    crop = hsv_img[y1_c:y2_c, x1_c:x2_c]
                    
                    if crop.size > 0:
                        total_pixels = crop.size / 3

                        # Yellow mask (Autorickshaw body — bright yellow)
                        lower_yellow = np.array([18, 80, 80])
                        upper_yellow = np.array([35, 255, 255])
                        mask_yellow = cv2.inRange(crop, lower_yellow, upper_yellow)
                        yellow_ratio = cv2.countNonZero(mask_yellow) / total_pixels

                        # Green mask (Autorickshaw bottom/hood — olive to bright green)
                        lower_green = np.array([35, 50, 50])
                        upper_green = np.array([85, 255, 255])
                        mask_green = cv2.inRange(crop, lower_green, upper_green)
                        green_ratio = cv2.countNonZero(mask_green) / total_pixels

                        # Black mask (Autorickshaw roof/canopy)
                        lower_black = np.array([0, 0, 0])
                        upper_black = np.array([180, 255, 50])
                        mask_black = cv2.inRange(crop, lower_black, upper_black)
                        black_ratio = cv2.countNonZero(mask_black) / total_pixels

                        # Autorickshaw detection: require strong yellow AND
                        # either significant black (yellow+black autos) or green (green+yellow autos)
                        is_yellow_black_auto = yellow_ratio > 0.15 and black_ratio > 0.10
                        is_yellow_green_auto = yellow_ratio > 0.10 and green_ratio > 0.08
                        
                        is_auto_color = is_yellow_black_auto or is_yellow_green_auto

                        # Only reclassify if color evidence is strong AND shape is compact
                        if is_auto_color and aspect_ratio < 1.6:
                            vehicle_class = "autorickshaw"

                # Handle truck vs bus confusion based on aspect ratio
                if vehicle_class in ["truck", "bus"]:
                    if aspect_ratio > 2.0:
                        vehicle_class = "bus"   # Long horizontal side-profile → bus
                    elif aspect_ratio < 0.45:
                        vehicle_class = "bus"   # Tall vertical top-down view → bus

                # Mock License Plate Recognition (ANPR)
                license_plate = ""
                if vehicle_class in ["car", "truck", "bus", "motorcycle", "autorickshaw"]:
                    # Generate a deterministic mock license plate based on vehicle ID
                    # Format: KA-XX-AB-1234
                    region_code = (vehicle_id % 90) + 10
                    letters = chr(65 + (vehicle_id % 26)) + chr(65 + ((vehicle_id + 5) % 26))
                    numbers = f"{(vehicle_id * 137 % 9000) + 1000:04d}"
                    license_plate = f"KA-{region_code}-{letters}-{numbers}"

                vehicle = {
                    "id": vehicle_id,
                    "class": vehicle_class,
                    "confidence": round(conf, 3),
                    "license_plate": license_plate,
                    "bbox": {
                        "x1": round(x1, 1),
                        "y1": round(y1, 1),
                        "x2": round(x2, 1),
                        "y2": round(y2, 1),
                    },
                    "is_parked": False,  # Will be set by parking intelligence
                }

                vehicles.append(vehicle)
                vehicle_id += 1

                # Update breakdown based on requested categories
                if vehicle_class in ["car", "autorickshaw"]:
                    breakdown["light_vehicles"] += 1
                elif vehicle_class in ["motorcycle", "bike", "scooty"]:
                    breakdown["motorcycles"] += 1
                elif vehicle_class in ["truck", "bus"]:
                    breakdown["heavy_vehicles"] += 1
                else:
                    breakdown["other"] += 1

        # Estimate parked vs moving using heuristics
        vehicles = self._estimate_parked_status(vehicles, img_width, img_height)

        return {
            "total_vehicles": len(vehicles),
            "vehicles": vehicles,
            "vehicle_breakdown": breakdown,
            "image_width": img_width,
            "image_height": img_height,
        }

    def _estimate_parked_status(
        self, vehicles: list[dict], img_width: int, img_height: int
    ) -> list[dict]:
        """
        Estimate which vehicles are parked using spatial heuristics.

        Heuristics used:
        1. Vehicles outside the perspective carriageway polygon → likely parked
        2. Vehicles with certain aspect ratios → profile suggests parking
        """
        if not vehicles or img_width == 0 or img_height == 0:
            return vehicles

        try:
            from services.parking_intelligence import CARRIAGEWAY_POLYGON_REL
            from shapely.geometry import Polygon, box
            scaled_coords = [(x * img_width, y * img_height) for x, y in CARRIAGEWAY_POLYGON_REL]
            carriageway_poly = Polygon(scaled_coords)
        except Exception as e:
            logger.error(f"Failed to load carriageway polygon for detection: {e}")
            carriageway_poly = None

        for vehicle in vehicles:
            bbox = vehicle["bbox"]
            center_x = (bbox["x1"] + bbox["x2"]) / 2
            center_y = (bbox["y1"] + bbox["y2"]) / 2
            width = bbox["x2"] - bbox["x1"]
            height = bbox["y2"] - bbox["y1"]
            aspect_ratio = width / max(height, 1)

            is_parked = False

            # Heuristic 1: Very wide aspect ratio → side-parked vehicle
            if aspect_ratio > 1.8:
                is_parked = True

            # Heuristic 2: Outside the perspective carriageway
            if carriageway_poly:
                bbox_poly = box(bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"])
                intersection = carriageway_poly.intersection(bbox_poly)
                # If mostly outside the carriageway (< 40% overlap), it's likely parked
                overlap_ratio = intersection.area / max(bbox_poly.area, 1.0)
                if overlap_ratio < 0.4:
                    is_parked = True
            else:
                # Fallback to naive edges if shapely fails
                if center_x < img_width * 0.20 or center_x > img_width * 0.80:
                    is_parked = True

            vehicle["is_parked"] = is_parked

        return vehicles

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None
