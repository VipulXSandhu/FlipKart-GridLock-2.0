"""
AI-ParkSense Backend
FastAPI application for intelligent parking hotspot detection
and congestion impact analysis.
"""

import logging
import uuid
import shutil
import tempfile
import asyncio
import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from services.detector import VehicleDetector
from services.image_processor import ImageProcessor
from services.parking_intelligence import ParkingIntelligence
from services.congestion_scorer import CongestionScorer
from services.enforcement_ranker import EnforcementRanker
from services.dataset_analytics import DatasetAnalytics
from storage.history import HistoryStorage

# ─── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("parksense")

# ─── Paths ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
SAMPLE_DIR = BASE_DIR / "sample_images"

# Create directories
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

# ─── Dataset path ───────────────────────────────────────────────────
PROJECT_ROOT = BASE_DIR.parent
CSV_FILES = list(PROJECT_ROOT.glob("*.csv"))
DATASET_PATH = str(CSV_FILES[0]) if CSV_FILES else None

# ─── Initialize Services ────────────────────────────────────────────
logger.info("Initializing AI-ParkSense services...")

detector = VehicleDetector(model_name="yolov8m.pt", confidence=0.35)
image_processor = ImageProcessor(output_dir=str(OUTPUTS_DIR))
parking_intel = ParkingIntelligence(max_expected_vehicles=30)
congestion_scorer = CongestionScorer()
enforcement_ranker = EnforcementRanker()
history_storage = HistoryStorage(str(DATA_DIR / "history.json"))

dataset_analytics = None
if DATASET_PATH:
    logger.info(f"Loading dataset from: {DATASET_PATH}")
    dataset_analytics = DatasetAnalytics(DATASET_PATH)
else:
    logger.warning("No CSV dataset found in project root.")

# ─── FastAPI App ─────────────────────────────────────────────────────
app = FastAPI(
    title="AI-ParkSense API",
    description="Intelligent Parking Hotspot Detection & Congestion Impact Analysis",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
app.mount("/static/samples", StaticFiles(directory=str(SAMPLE_DIR)), name="samples")

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ─── WebSocket Connection Manager ────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()


# ─── Routes ──────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "online",
        "model_loaded": detector.is_loaded,
        "dataset_loaded": dataset_analytics.is_loaded if dataset_analytics else False,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Core analysis endpoint.
    Accepts a traffic image, runs full detection + analysis pipeline.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Generate unique analysis ID
    analysis_id = str(uuid.uuid4())[:12]
    timestamp = datetime.now(timezone.utc).isoformat()

    # Save uploaded file temporarily
    upload_path = UPLOADS_DIR / f"{analysis_id}{ext}"
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        with open(upload_path, "wb") as f:
            f.write(contents)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")

    # ── Run Analysis Pipeline ──────────────────────────────────────
    try:
        # 1. Vehicle Detection
        logger.info(f"[{analysis_id}] Running vehicle detection...")
        detection_result = await asyncio.to_thread(detector.detect, str(upload_path))

        # 2. Parking Intelligence (BEFORE annotation so violation types are set)
        logger.info(f"[{analysis_id}] Analyzing parking patterns...")
        parking_result = parking_intel.analyze(detection_result)

        # 3. Image Annotation (now vehicles have parking_violation_type)
        logger.info(f"[{analysis_id}] Generating annotated image...")
        image_processor.save_original(str(upload_path), analysis_id)
        annotated_path = image_processor.draw_annotations(
            str(upload_path), detection_result["vehicles"], analysis_id
        )

        # 4. Heatmap Generation (violation-weighted)
        logger.info(f"[{analysis_id}] Generating heatmap...")
        heatmap_path = image_processor.generate_heatmap(
            str(upload_path), detection_result["vehicles"], analysis_id
        )

        # 5. Congestion Scoring
        logger.info(f"[{analysis_id}] Calculating congestion score...")
        congestion_result = congestion_scorer.calculate(
            detection_result, parking_result
        )

        # 6. Hotspot Classification
        hotspot_result = _classify_hotspots(
            detection_result, parking_result, congestion_result
        )

        # 7. Enforcement Ranking (now with hotspot data for per-zone targets)
        logger.info(f"[{analysis_id}] Generating enforcement ranking...")
        enforcement_result = enforcement_ranker.rank(
            congestion_result, parking_result, hotspot_result
        )

        # Build response
        response = {
            "id": analysis_id,
            "timestamp": timestamp,
            "image": {
                "original_url": f"/static/outputs/{analysis_id}_original.jpg",
                "annotated_url": f"/static/outputs/{analysis_id}_annotated.jpg",
                "heatmap_url": f"/static/outputs/{analysis_id}_heatmap.jpg",
                "width": detection_result["image_width"],
                "height": detection_result["image_height"],
            },
            "detection": {
                "total_vehicles": detection_result["total_vehicles"],
                "vehicles": detection_result["vehicles"],
                "vehicle_breakdown": detection_result["vehicle_breakdown"],
            },
            "parking": parking_result,
            "congestion": congestion_result,
            "hotspot": hotspot_result,
            "enforcement": enforcement_result,
        }

        # Save to history
        history_storage.add_record(response)

        # Broadcast alert if critical
        if hotspot_result.get("rank") == 1:
            asyncio.create_task(manager.broadcast({
                "type": "alert",
                "message": f"Critical Congestion Detected! Score: {hotspot_result['score']}",
                "analysis_id": analysis_id
            }))

        logger.info(
            f"[{analysis_id}] Analysis complete. "
            f"Vehicles: {detection_result['total_vehicles']}, "
            f"Congestion: {congestion_result['level']} ({congestion_result['score']})"
        )

        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"[{analysis_id}] Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )


@app.get("/api/samples")
async def list_samples():
    """List available sample images."""
    samples = []
    if SAMPLE_DIR.exists():
        for idx, img_file in enumerate(sorted(SAMPLE_DIR.iterdir())):
            if img_file.suffix.lower() in ALLOWED_EXTENSIONS:
                samples.append({
                    "id": f"sample_{idx}",
                    "name": img_file.stem.replace("_", " ").title(),
                    "description": f"Sample traffic image: {img_file.stem}",
                    "thumbnail_url": f"/static/samples/{img_file.name}",
                    "url": f"/static/samples/{img_file.name}",
                })

    return {"samples": samples}


@app.post("/api/analyze-sample/{sample_id}")
async def analyze_sample(sample_id: str):
    """Analyze a sample image by its ID."""
    # Find the sample file
    samples = sorted(SAMPLE_DIR.iterdir()) if SAMPLE_DIR.exists() else []
    sample_files = [
        f for f in samples if f.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    # Extract index from sample_id
    try:
        idx = int(sample_id.replace("sample_", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid sample ID.")

    if idx < 0 or idx >= len(sample_files):
        raise HTTPException(status_code=404, detail="Sample image not found.")

    sample_file = sample_files[idx]

    # Create an UploadFile-like object and reuse analyze logic
    analysis_id = str(uuid.uuid4())[:12]
    timestamp = datetime.now(timezone.utc).isoformat()
    ext = sample_file.suffix.lower()

    # Copy sample to uploads
    upload_path = UPLOADS_DIR / f"{analysis_id}{ext}"
    shutil.copy2(str(sample_file), str(upload_path))

    try:
        detection_result = await asyncio.to_thread(detector.detect, str(upload_path))
        # Parking analysis BEFORE annotation so violation types are set
        parking_result = parking_intel.analyze(detection_result)
        image_processor.save_original(str(upload_path), analysis_id)
        annotated_path = image_processor.draw_annotations(
            str(upload_path), detection_result["vehicles"], analysis_id
        )
        heatmap_path = image_processor.generate_heatmap(
            str(upload_path), detection_result["vehicles"], analysis_id
        )
        congestion_result = congestion_scorer.calculate(detection_result, parking_result)
        hotspot_result = _classify_hotspots(detection_result, parking_result, congestion_result)
        enforcement_result = enforcement_ranker.rank(congestion_result, parking_result, hotspot_result)

        response_data = {
            "id": analysis_id,
            "timestamp": timestamp,
            "image": {
                "original_url": f"/static/outputs/{analysis_id}_original.jpg",
                "annotated_url": f"/static/outputs/{analysis_id}_annotated.jpg",
                "heatmap_url": f"/static/outputs/{analysis_id}_heatmap.jpg",
                "width": detection_result["image_width"],
                "height": detection_result["image_height"],
            },
            "detection": {
                "total_vehicles": detection_result["total_vehicles"],
                "vehicles": detection_result["vehicles"],
                "vehicle_breakdown": detection_result["vehicle_breakdown"],
            },
            "parking": parking_result,
            "congestion": congestion_result,
            "hotspot": hotspot_result,
            "enforcement": enforcement_result,
        }

        history_storage.add_record(response_data)

        return JSONResponse(content=response_data)
    except Exception as e:
        logger.error(f"Sample analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/dataset/summary")
async def get_dataset_summary():
    """Get summary analytics from the violations dataset."""
    if dataset_analytics is None or not dataset_analytics.is_loaded:
        raise HTTPException(
            status_code=404,
            detail="Dataset not loaded. Place the CSV file in the project root.",
        )

    return dataset_analytics.get_summary()


@app.get("/api/history")
async def get_history(limit: int = 20):
    """Get recent analysis history."""
    history = history_storage.get_history(limit=limit)
    return {"history": history}


@app.get("/api/export/{analysis_id}")
async def export_report(analysis_id: str):
    """Export the analysis report as a JSON file download."""
    record = history_storage.get_record(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    # Convert to JSON and return as a downloadable file
    # We can use a temporary file or just return a response with appropriate headers
    headers = {
        "Content-Disposition": f"attachment; filename=parksense_report_{analysis_id}.json"
    }
    return JSONResponse(content=record, headers=headers)


# ─── WebSockets ──────────────────────────────────────────────────────

@app.websocket("/api/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts."""
    await manager.connect(websocket)
    try:
        while True:
            # Just keep connection alive, waiting for broadcasts
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/api/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for video stream analysis."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "frame":
                    b64_data = payload.get("image", "").split(",")[-1]
                    image_data = base64.b64decode(b64_data)
                    
                    analysis_id = str(uuid.uuid4())[:12]
                    temp_path = UPLOADS_DIR / f"stream_{analysis_id}.jpg"
                    
                    with open(temp_path, "wb") as f:
                        f.write(image_data)
                        
                    # Run fast detection (only detector to save time)
                    detection_result = detector.detect(str(temp_path))
                    
                    # Optional: We could run the full pipeline, but it's too slow for video.
                    # We will return the bounding boxes and let the frontend draw them.
                    await websocket.send_json({
                        "type": "result",
                        "detection": {
                            "total_vehicles": detection_result["total_vehicles"],
                            "vehicles": detection_result["vehicles"]
                        }
                    })
                    
                    # Clean up
                    if temp_path.exists():
                        temp_path.unlink()
            except Exception as e:
                logger.error(f"Stream error: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        pass


# ─── Helper Functions ────────────────────────────────────────────────

def _classify_hotspots(
    detection_result: dict,
    parking_result: dict,
    congestion_result: dict,
) -> dict:
    """
    Classify image zones as hotspots based on vehicle clustering using DBSCAN.
    Identifies natural clusters of parked vehicles and calculates their specific
    congestion impact on traffic flow.
    """
    import numpy as np
    from sklearn.cluster import DBSCAN

    vehicles = detection_result.get("vehicles", [])
    img_w = detection_result.get("image_width", 1)
    img_h = detection_result.get("image_height", 1)

    parked_vehicles = [v for v in vehicles if v.get("is_parked", False)]
    total_parked = len(parked_vehicles)

    zones = []

    if total_parked > 0:
        # Extract centroids
        centroids = []
        for v in parked_vehicles:
            bbox = v["bbox"]
            cx = (bbox["x1"] + bbox["x2"]) / 2
            cy = (bbox["y1"] + bbox["y2"]) / 2
            centroids.append([cx, cy])
        
        X = np.array(centroids)
        
        # Calculate eps relative to image size (e.g., 10% of image diagonal)
        diag = np.sqrt(img_w**2 + img_h**2)
        eps = diag * 0.10
        min_samples = 3  # Minimum 3 vehicles to form a hotspot
        
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
        labels = db.labels_
        
        unique_labels = set(labels)
        
        zone_id = 1
        for k in unique_labels:
            if k == -1:
                # Noise points
                continue
            
            class_member_mask = (labels == k)
            cluster_points = X[class_member_mask]
            
            # Get the actual parked vehicles in this cluster
            cluster_indices = np.where(class_member_mask)[0]
            cluster_vehicles = [parked_vehicles[i] for i in cluster_indices]
            
            zone_parked = len(cluster_points)
            density = zone_parked / total_parked
            
            # Count illegal vs legal in this zone
            illegal_count = sum(
                1 for v in cluster_vehicles
                if v.get("parking_violation_type", "legal") != "legal"
            )
            legal_count = zone_parked - illegal_count
            
            # Get violation type breakdown for this zone
            zone_violations = {}
            total_impact_score = 0.0
            for v in cluster_vehicles:
                vtype = v.get("parking_violation_type", "legal")
                if vtype != "legal":
                    zone_violations[vtype] = zone_violations.get(vtype, 0) + 1
                total_impact_score += v.get("traffic_flow_impact_score", 0)
            
            # Determine top violation type
            top_violation = max(zone_violations, key=zone_violations.get) if zone_violations else None
            
            # Zone congestion impact (normalize based on max possible score per vehicle = 100)
            # We average the impact score, but amplify if there are many highly impactful vehicles
            avg_impact = total_impact_score / max(zone_parked, 1)
            zone_congestion_impact = min(round((avg_impact * 0.7) + (total_impact_score * 0.05), 1), 100.0)

            # Severity now heavily weights the traffic flow impact instead of just density
            severity = "Low"
            if zone_congestion_impact >= 75:
                severity = "Critical"
            elif zone_congestion_impact >= 50:
                severity = "High"
            elif zone_congestion_impact >= 25:
                severity = "Medium"
                
            # Calculate cluster centroid
            cluster_cx = np.mean(cluster_points[:, 0])
            cluster_cy = np.mean(cluster_points[:, 1])
            
            zones.append({
                "zone_id": zone_id,
                "region": f"Cluster near ({int(cluster_cx)}, {int(cluster_cy)})",
                "density": round(density, 3),
                "severity": severity,
                "center_x": int(cluster_cx),
                "center_y": int(cluster_cy),
                "vehicle_count": zone_parked,
                "illegal_count": illegal_count,
                "legal_count": legal_count,
                "top_violation_type": top_violation,
                "violation_breakdown": zone_violations,
                "congestion_impact": zone_congestion_impact,
            })
            zone_id += 1

    # Sort by congestion impact descending (targeted enforcement)
    zones.sort(key=lambda z: z["congestion_impact"], reverse=True)

    # Overall hotspot score is now driven by the maximum zone congestion impact
    hotspot_score = zones[0]["congestion_impact"] if zones else 0
    # Add a slight bump for having multiple zones
    hotspot_score = min(round(hotspot_score + (len(zones) * 2), 1), 100.0)

    # Determine overall rank
    if hotspot_score >= 76:
        rank, priority, severity = 1, "Priority 1", "Critical Congestion"
    elif hotspot_score >= 51:
        rank, priority, severity = 2, "Priority 2", "High Congestion"
    elif hotspot_score >= 26:
        rank, priority, severity = 3, "Priority 3", "Moderate Congestion"
    else:
        rank, priority, severity = 4, "Priority 4", "Low Congestion"

    return {
        "score": hotspot_score,
        "rank": rank,
        "priority_label": priority,
        "severity": severity,
        "zones": zones,
    }


# ─── Startup Event ───────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("  AI-ParkSense Backend Started")
    logger.info(f"  Model loaded: {detector.is_loaded}")
    logger.info(f"  Dataset loaded: {dataset_analytics.is_loaded if dataset_analytics else False}")
    logger.info("=" * 60)
