<p align="center">
  <img src="frontend/public/favicon.svg" width="80" alt="ParkVision AI Logo" />
</p>

<h1 align="center">ParkVision AI</h1>

<p align="center">
  <strong>AI-Driven Parking Intelligence for Smart Traffic Enforcement</strong><br/>
  <em>Detect. Quantify. Enforce.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-FF6F00?logo=yolo&logoColor=white" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-5.8-3178C6?logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-6.x-646CFF?logo=vite&logoColor=white" />
</p>

---

## 🧠 What is ParkVision AI?

ParkVision AI is a full-stack AI-powered traffic intelligence system that goes beyond simple vehicle detection. It:

1. **Detects** vehicles in traffic imagery using YOLOv8
2. **Classifies** parking violations into a **5-class taxonomy** (no-parking zone, double-parked, carriageway blocking, intersection blocking, legal)
3. **Quantifies** each violation's **traffic flow impact** using computational geometry and congestion decomposition
4. **Clusters** violations into **spatial hotspots** using DBSCAN
5. **Ranks** enforcement priorities with a multi-criteria index, telling officers **where to go first** for maximum traffic improvement

> **Key Innovation:** We don't just find violations — we measure how much congestion each one causes, and attribute what percentage of total congestion is parking-driven.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Vehicle Detection** | YOLOv8m (25.9M params) — detects cars, trucks, buses, motorcycles, and autorickshaws |
| 🎨 **Autorickshaw Detection** | Custom HSV color heuristics to identify Indian autorickshaws (not in COCO dataset) |
| 🅿️ **5-Class Violation Taxonomy** | no_parking_zone · double_parked · carriageway_blocking · intersection_blocking · legal |
| 📐 **Carriageway Blockage** | Shapely polygon intersection computes exact road area blocked by parked vehicles |
| 🚦 **3-Factor Congestion Scoring** | Carriageway blockage (0-40) + Lane reduction (0-30) + PCU-weighted volume pressure (0-30) |
| 📊 **Parking Impact Ratio** | Quantifies what % of congestion is caused by parking violations |
| 🔥 **DBSCAN Hotspot Clustering** | Finds natural clusters of parked vehicles — no fixed grid |
| ⚡ **Enforcement Ranking** | Priority 1-4 with per-zone targeted actions |
| 🗺️ **Violation-Weighted Heatmap** | Heatmap intensity weighted by each vehicle's traffic flow impact score |
| 📡 **Real-Time WebSocket Alerts** | Priority 1 hotspot alerts broadcast to all connected clients |
| 🎥 **Video Stream Analysis** | WebSocket endpoint for frame-by-frame live detection |
| 📁 **Dataset Analytics** | Processes 50,000+ Bengaluru police violation records for citywide insights |
| 📈 **Interactive Dashboard** | React 18 + Recharts with glassmorphism UI, live metrics, and export |
| 🤖 **AI Executive Summary** | Natural language enforcement intelligence report with typewriter animation |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                               │
│   Image Upload (REST)  ·  Sample Gallery  ·  WebSocket Stream   │
│   Bengaluru Police CSV Dataset (50K records)                     │
├─────────────────────────────────────────────────────────────────┤
│                      AI / ML LAYER                               │
│   YOLOv8m Detection → HSV Autorickshaw Reclassification         │
│   Shapely Polygon Intersection → DBSCAN Spatial Clustering      │
├─────────────────────────────────────────────────────────────────┤
│                    ANALYTICS LAYER                               │
│   Congestion Decomposition · Parking Impact Attribution          │
│   Per-Vehicle Impact Score · Zone Congestion Impact              │
├─────────────────────────────────────────────────────────────────┤
│                     OUTPUT LAYER                                 │
│   Annotated Image · Heatmap · Priority Enforcement Ranking      │
│   WebSocket Alerts · JSON Export · Dashboard                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | 0.115.0 |
| **AI/ML** | YOLOv8 (Ultralytics) | ≥8.2.0 |
| **Computer Vision** | OpenCV (headless) | 4.10.0 |
| **Geometry** | Shapely | ≥2.0.0 |
| **Clustering** | scikit-learn (DBSCAN) | ≥1.3.0 |
| **Data Processing** | Pandas + NumPy | ≥2.2.0 / ≥1.26.4 |
| **Frontend** | React 18 + TypeScript | 18.3 / 5.8 |
| **Build Tool** | Vite | 6.x |
| **Styling** | Tailwind CSS | 3.4 |
| **Charts** | Recharts | 2.15 |
| **Maps** | Leaflet + React-Leaflet | 1.9 / 4.2 |
| **Icons** | Lucide React | Latest |
| **Real-time** | WebSockets | ≥11.0.3 |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> **Note:** On first run, the YOLOv8m model (~52MB) will be downloaded automatically. Internet connection required.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

### 3. Dataset (Optional)

Place the Bengaluru police violations CSV file in the project root directory. The system will auto-detect and load it on backend startup.

---

## 📁 Project Structure

```
ParkVision-AI/
├── .gitignore
├── README.md
├── backend/
│   ├── main.py                        # FastAPI app — routes, WebSocket, pipeline orchestration
│   ├── requirements.txt               # Python dependencies
│   ├── models/
│   │   └── schemas.py                 # Pydantic response schemas
│   ├── services/
│   │   ├── detector.py                # YOLOv8 vehicle detection + autorickshaw heuristics
│   │   ├── image_processor.py         # OpenCV annotation + violation-weighted heatmap
│   │   ├── parking_intelligence.py    # 5-class violation classification + carriageway blockage
│   │   ├── congestion_scorer.py       # 3-factor congestion decomposition with PCU weights
│   │   ├── enforcement_ranker.py      # Multi-criteria priority index + per-zone enforcement
│   │   └── dataset_analytics.py       # Bengaluru police dataset processing
│   ├── storage/
│   │   └── history.py                 # JSON-based analysis history persistence
│   └── sample_images/                 # Pre-bundled sample traffic images
├── frontend/
│   ├── index.html                     # Entry point with splash screen
│   ├── package.json
│   ├── vite.config.ts                 # Dev proxy to backend
│   ├── tailwind.config.js             # Custom design tokens
│   └── src/
│       ├── App.tsx                    # Root layout with tab navigation
│       ├── main.tsx                   # React entry point
│       ├── index.css                  # Global styles, glassmorphism, animations
│       ├── api/
│       │   └── client.ts             # Axios API client
│       ├── components/
│       │   ├── layout/               # Header, LeftPanel, MainSection, RightPanel, BottomSection
│       │   ├── metrics/              # ExecutiveSummary, ZoneMiniMap
│       │   ├── analytics/            # DatasetDashboard
│       │   └── common/               # ErrorMessage, LoadingSpinner, StatusBadge
│       ├── hooks/
│       │   └── useAnalysis.ts        # Core state management hook
│       ├── types/
│       │   └── index.ts              # TypeScript interfaces
│       └── utils/
│           ├── constants.ts          # Color palettes, display names, violation mappings
│           └── formatters.ts         # Number/date formatting utilities
└── *.csv                              # Dataset (not included — see instructions above)
```

---

## 🔌 API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload & analyze a traffic image (full pipeline) |
| `POST` | `/api/analyze-sample/{id}` | Analyze a pre-bundled sample image |
| `GET` | `/api/samples` | List available sample images |
| `GET` | `/api/health` | Health check (model status, dataset status) |
| `GET` | `/api/dataset/summary` | Dataset analytics summary |
| `GET` | `/api/history?limit=20` | Recent analysis history |
| `GET` | `/api/export/{analysis_id}` | Export analysis report as JSON download |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `ws://host/api/ws/alerts` | Real-time Priority 1 hotspot alert notifications |
| `ws://host/api/ws/stream` | Live video frame-by-frame analysis (send base64 frames) |

---

## 🧮 Technical Deep Dive

### Congestion Score Formula (0-100)

```
Total = Carriageway_Blockage(0-40) + Lane_Reduction(0-30) + Volume_Pressure(0-30)

Factor 1: blockage_score = carriageway_blocked_pct × 40
Factor 2: lane_reduction_score = min(lanes_lost × 15, 30)
Factor 3: volume_score = 30 × (1 - e^(-0.08 × flow_impedance))

Where:
  flow_impedance = Σ(PCU_weighted_vehicles) / available_capacity
  PCU weights: Car=1.0, Auto=0.8, Motorcycle=0.5, Truck=2.5, Bus=3.0
```

### Parking Impact Ratio

```
parking_driven = blockage_score + lane_reduction_score
parking_impact_ratio = parking_driven / total_score
```

### Enforcement Priority Index

```
P = √(Congestion_Score/100 × Hotspot_Intensity/100) × 100
```

A geometric mean requiring **both** high congestion AND dense violation clustering for Priority 1.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for the object detection backbone
- [Bengaluru Traffic Police](https://btp.gov.in/) for the real-world violation dataset
- Built for [Flipkart GridLock 2.0](https://unstop.com/) hackathon

---

<p align="center">
  <strong>Detect. Quantify. Enforce.</strong><br/>
  <em>Built with ❤️ for smarter cities</em>
</p>
