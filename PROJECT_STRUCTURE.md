# Transit Oracle - Project Directory Structure

```
transit-oracle/
│
├── README.md                          # Project documentation (existing)
├── PROJECT_STRUCTURE.md               # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variable template (no secrets)
├── .gitignore                         # Git ignore file
│
├── backend/                           # Python backend services
│   │
│   ├── ingestion/                     # Data ingestion layer (Member A)
│   │   ├── __init__.py
│   │   ├── gtfs_ingest.py            # Main GTFS-RT feed parser
│   │   ├── spatial_join.py           # GeoPandas traffic signal intersection logic
│   │   └── config.py                 # Feed URLs, thresholds, constants
│   │
│   ├── seeder/                        # Synthetic data generation (Member B)
│   │   ├── __init__.py
│   │   └── seeder_script.py          # 30-day historical data generator
│   │
│   ├── middleware/                    # API middleware layer (Member B)
│   │   ├── __init__.py
│   │   ├── app.py                    # Flask/FastAPI main application
│   │   ├── amplitude_client.py       # Amplitude API interactions
│   │   ├── backboard_client.py       # Backboard.io LLM orchestration (Member D)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── buses.py              # GET /api/high-risk-buses, GET /api/buses
│   │       ├── analytics.py          # GET /api/signal-delays, GET /api/costs
│   │       └── ai.py                 # POST /api/generate-alert, POST /api/generate-motion
│   │
│   ├── models/                        # Data models and schemas
│   │   ├── __init__.py
│   │   ├── events.py                 # Amplitude event schemas
│   │   └── bus.py                    # Bus/Vehicle data models
│   │
│   └── utils/                         # Shared utilities
│       ├── __init__.py
│       ├── logging.py                # Logging configuration
│       └── secrets.py                # 1Password integration
│
├── frontend/                          # React frontend (Member C & D)
│   ├── package.json
│   ├── vite.config.js                # Or next.config.js if using Next.js
│   │
│   ├── public/
│   │   └── assets/
│   │       ├── bus-icon.svg
│   │       ├── bus-icon-red.svg      # High-risk bus
│   │       └── signal-icon.svg
│   │
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       │
│       ├── components/
│       │   ├── common/
│       │   │   ├── Header.jsx
│       │   │   ├── SecurityBadge.jsx  # 1Password "Secured" badge
│       │   │   └── LoadingSpinner.jsx
│       │   │
│       │   ├── rider/                 # Rider View (Member C)
│       │   │   ├── TransitMap.jsx    # MapLibre GL map
│       │   │   ├── BusMarker.jsx     # Individual bus on map
│       │   │   ├── BusPopup.jsx      # Click popup with details
│       │   │   ├── RiskAlert.jsx     # Short-turn warning banner
│       │   │   └── AudioAlert.jsx    # ElevenLabs integration
│       │   │
│       │   └── mayor/                 # Mayor View (Member D)
│       │       ├── Dashboard.jsx     # Main dashboard layout
│       │       ├── CostCounter.jsx   # Taxpayer cost display
│       │       ├── IntersectionTable.jsx  # Ranked signal delays
│       │       ├── PolicyGenerator.jsx    # Gemini/Backboard AI button
│       │       └── charts/
│       │           ├── AmplitudeEmbed.jsx # Embedded Amplitude charts
│       │           └── DelayChart.jsx
│       │
│       ├── hooks/
│       │   ├── useBuses.js           # Fetch bus positions
│       │   ├── useHighRiskBuses.js   # Fetch high-risk cohort
│       │   └── useAnalytics.js       # Fetch cost/delay data
│       │
│       ├── services/
│       │   ├── api.js                # Axios/fetch wrapper
│       │   └── elevenlabs.js         # Audio alert service
│       │
│       ├── pages/
│       │   ├── RiderView.jsx         # /rider route
│       │   └── MayorView.jsx         # /mayor route
│       │
│       └── styles/
│           ├── globals.css
│           └── map.css
│
├── data/                              # Static data files
│   ├── traffic_signals/              # Downloaded from Toronto Open Data
│   │   └── .gitkeep                  # Placeholder (download shapefile here)
│   │
│   ├── gtfs_static/                  # TTC static GTFS (routes, stops)
│   │   └── .gitkeep
│   │
│   └── tape_delay/                   # Fallback recorded data
│       └── .gitkeep                  # Store recorded JSON here for demo backup
│
├── scripts/                           # Utility scripts
│   ├── download_traffic_signals.sh   # Fetch Toronto Open Data shapefile
│   ├── download_gtfs_static.sh       # Fetch TTC static GTFS
│   └── record_tape_delay.py          # Record live feed for backup
│
├── tests/                             # Test files
│   ├── test_gtfs_ingest.py
│   ├── test_spatial_join.py
│   └── test_amplitude_events.py
│
└── docs/                              # Additional documentation
    ├── api_reference.md              # Backend API docs
    ├── amplitude_schema.md           # Event taxonomy reference
    └── demo_script.md                # Hackathon presentation script
```

## Directory Responsibilities by Team Member

| Directory | Primary Owner | Description |
|-----------|---------------|-------------|
| `backend/ingestion/` | Member A (Data) | GTFS parsing, spatial joins |
| `backend/seeder/` | Member B (Architect) | Synthetic data generation |
| `backend/middleware/` | Member B (Architect) | API server, Amplitude polling |
| `backend/middleware/routes/ai.py` | Member D (Policy) | Backboard.io integration |
| `frontend/src/components/rider/` | Member C (Frontend) | Real-time map UI |
| `frontend/src/components/mayor/` | Member D (Policy) | Dashboard and AI features |
| `data/` | Member A (Data) | Static datasets |
| `scripts/` | All | Setup utilities |

## Key Files to Create First (Friday Night)

1. `backend/ingestion/gtfs_ingest.py` - **CRITICAL PATH**
2. `backend/seeder/seeder_script.py` - Needs to run overnight
3. `backend/middleware/app.py` - Basic Flask server
4. `frontend/src/components/rider/TransitMap.jsx` - Map skeleton
5. `.env.example` - Document required environment variables

## Environment Variables Required

```bash
# Amplitude
AMPLITUDE_API_KEY=your_amplitude_api_key

# TTC Data
TTC_GTFS_RT_URL=http://opendata.toronto.ca/TTC/realtime/VehiclePositions.pb
TTC_TRIP_UPDATES_URL=http://opendata.toronto.ca/TTC/realtime/TripUpdates.pb

# Backboard.io (for Gemini/Claude)
BACKBOARD_API_KEY=your_backboard_api_key

# MongoDB Atlas (optional)
MONGODB_URI=mongodb+srv://...

# ElevenLabs (optional)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```
