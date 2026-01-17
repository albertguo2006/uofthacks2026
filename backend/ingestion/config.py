"""
Transit Oracle - Ingestion Configuration

All configurable parameters for GTFS-RT feed ingestion.
"""

import os

# =============================================================================
# TTC GTFS-RT Feed URLs
# =============================================================================

# Primary: Direct TTC Protobuf endpoints
TTC_VEHICLE_POSITIONS_URL = os.getenv(
    "TTC_GTFS_RT_URL",
    "https://opendata.toronto.ca/TTC/realtime/VehiclePositions.pb"
)

TTC_TRIP_UPDATES_URL = os.getenv(
    "TTC_TRIP_UPDATES_URL",
    "https://opendata.toronto.ca/TTC/realtime/TripUpdates.pb"
)

# Fallback: Transitland JSON proxy (if Protobuf fails)
TRANSITLAND_FEED_KEY = "f-dpz8-ttc~rt"
TRANSITLAND_VEHICLE_POSITIONS_URL = (
    f"https://transit.land/api/v2/rest/feeds/{TRANSITLAND_FEED_KEY}"
    "/download_latest_rt/vehicle_positions.json"
)

# =============================================================================
# Amplitude Configuration
# =============================================================================

AMPLITUDE_API_KEY = os.getenv("AMPLITUDE_API_KEY", "")
AMPLITUDE_HTTP_API_URL = "https://api2.amplitude.com/2/httpapi"
AMPLITUDE_BATCH_API_URL = "https://api2.amplitude.com/batch"

# Event batch settings
AMPLITUDE_BATCH_SIZE = 1000  # Max events per batch request
AMPLITUDE_FLUSH_INTERVAL_SECONDS = 30  # How often to send events

# =============================================================================
# Spatial Analysis Thresholds
# =============================================================================

# Speed threshold for "stopped" detection (km/h)
STOPPED_SPEED_THRESHOLD_KMH = 5.0

# Buffer radius around traffic signals (meters)
SIGNAL_BUFFER_RADIUS_METERS = 15.0

# Buffer radius around bus stops (meters)
STOP_BUFFER_RADIUS_METERS = 20.0

# =============================================================================
# Occupancy Mapping
# =============================================================================

# TTC reports 3 buckets, map to GTFS-RT standard enums
OCCUPANCY_MAPPING = {
    0: "EMPTY",
    1: "MANY_SEATS_AVAILABLE",      # TTC: "Not Busy" (0-30%)
    2: "FEW_SEATS_AVAILABLE",       # TTC: "Busy" (30-80%)
    3: "STANDING_ROOM_ONLY",        # TTC: "Very Busy" (>80%)
    4: "CRUSHED_STANDING_ROOM_ONLY",
    5: "FULL",
    6: "NOT_ACCEPTING_PASSENGERS",
}

# =============================================================================
# Risk Detection Thresholds
# =============================================================================

# Gap time threshold for "high risk" short turn (seconds)
HIGH_RISK_GAP_TIME_SECONDS = 600  # 10 minutes late

# Occupancy levels considered "crowded"
CROWDED_OCCUPANCY_LEVELS = [
    "STANDING_ROOM_ONLY",
    "CRUSHED_STANDING_ROOM_ONLY",
    "FULL",
]

# =============================================================================
# Polling Intervals
# =============================================================================

# How often to fetch GTFS-RT feed (seconds)
GTFS_POLL_INTERVAL_SECONDS = 30

# =============================================================================
# File Paths
# =============================================================================

# Traffic signals shapefile (downloaded from Toronto Open Data)
TRAFFIC_SIGNALS_SHAPEFILE = os.getenv(
    "TRAFFIC_SIGNALS_PATH",
    "data/traffic_signals/traffic_signals.shp"
)

# GTFS Static data directory
GTFS_STATIC_DIR = os.getenv(
    "GTFS_STATIC_PATH",
    "data/gtfs_static"
)

# Tape delay fallback file
TAPE_DELAY_FILE = os.getenv(
    "TAPE_DELAY_PATH",
    "data/tape_delay/recorded_positions.json"
)

# =============================================================================
# Coordinate Reference Systems
# =============================================================================

# WGS84 (lat/long) - Standard GPS coordinates
CRS_WGS84 = "EPSG:4326"

# NAD83 / UTM zone 17N - Metric CRS for Toronto area
# Used for accurate distance calculations in meters
CRS_TORONTO_UTM = "EPSG:26917"
