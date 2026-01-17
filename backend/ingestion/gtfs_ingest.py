#!/usr/bin/env python3
"""
Transit Oracle - GTFS-RT Ingestion Script

This script fetches real-time vehicle positions from the TTC GTFS-RT feed,
processes them into Amplitude events, and sends them to the analytics platform.

The "Bus-as-User" paradigm:
- user_id = Vehicle ID (e.g., "Bus_1024")
- session_id = Trip ID
- Events track operational states (stop_arrival, signal_delay, short_turn, etc.)

Usage:
    python gtfs_ingest.py                    # Run with live feed
    python gtfs_ingest.py --tape-delay       # Run with recorded fallback data
    python gtfs_ingest.py --dry-run          # Parse feed but don't send to Amplitude

Author: Transit Oracle Team
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Optional

import requests

# GTFS-RT Protobuf bindings
try:
    from google.transit import gtfs_realtime_pb2
    PROTOBUF_AVAILABLE = True
except ImportError:
    PROTOBUF_AVAILABLE = False
    print("WARNING: gtfs-realtime-bindings not installed. Install with:")
    print("  pip install gtfs-realtime-bindings")

from config import (
    TTC_VEHICLE_POSITIONS_URL,
    TTC_TRIP_UPDATES_URL,
    TRANSITLAND_VEHICLE_POSITIONS_URL,
    AMPLITUDE_API_KEY,
    AMPLITUDE_BATCH_API_URL,
    AMPLITUDE_BATCH_SIZE,
    GTFS_POLL_INTERVAL_SECONDS,
    STOPPED_SPEED_THRESHOLD_KMH,
    HIGH_RISK_GAP_TIME_SECONDS,
    CROWDED_OCCUPANCY_LEVELS,
    OCCUPANCY_MAPPING,
    TAPE_DELAY_FILE,
)

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gtfs_ingest")

# =============================================================================
# Data Models
# =============================================================================

class VehiclePosition:
    """Represents a single vehicle's position and state."""

    def __init__(
        self,
        vehicle_id: str,
        trip_id: str,
        route_id: str,
        latitude: float,
        longitude: float,
        speed_kmh: float,
        bearing: Optional[float],
        timestamp: datetime,
        occupancy_status: str,
        stop_id: Optional[str] = None,
        current_stop_sequence: Optional[int] = None,
    ):
        self.vehicle_id = vehicle_id
        self.trip_id = trip_id
        self.route_id = route_id
        self.latitude = latitude
        self.longitude = longitude
        self.speed_kmh = speed_kmh
        self.bearing = bearing
        self.timestamp = timestamp
        self.occupancy_status = occupancy_status
        self.stop_id = stop_id
        self.current_stop_sequence = current_stop_sequence

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "vehicle_id": self.vehicle_id,
            "trip_id": self.trip_id,
            "route_id": self.route_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "speed_kmh": self.speed_kmh,
            "bearing": self.bearing,
            "timestamp": self.timestamp.isoformat(),
            "occupancy_status": self.occupancy_status,
            "stop_id": self.stop_id,
            "current_stop_sequence": self.current_stop_sequence,
        }

    @property
    def is_stopped(self) -> bool:
        """Check if vehicle is considered stopped."""
        return self.speed_kmh < STOPPED_SPEED_THRESHOLD_KMH

    @property
    def is_crowded(self) -> bool:
        """Check if vehicle is crowded."""
        return self.occupancy_status in CROWDED_OCCUPANCY_LEVELS

    @property
    def amplitude_user_id(self) -> str:
        """User ID for Amplitude (Bus-as-User paradigm)."""
        return f"Bus_{self.vehicle_id}"


# =============================================================================
# GTFS-RT Feed Parsers
# =============================================================================

def fetch_protobuf_feed(url: str, timeout: int = 10) -> Optional[bytes]:
    """
    Fetch raw Protobuf data from a GTFS-RT endpoint.

    Args:
        url: The GTFS-RT Protobuf endpoint URL
        timeout: Request timeout in seconds

    Returns:
        Raw bytes of the Protobuf response, or None on failure
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch feed from {url}: {e}")
        return None


def parse_vehicle_positions_protobuf(content: bytes) -> list[VehiclePosition]:
    """
    Parse GTFS-RT VehiclePositions Protobuf feed.

    Args:
        content: Raw Protobuf bytes

    Returns:
        List of VehiclePosition objects
    """
    if not PROTOBUF_AVAILABLE:
        logger.error("Protobuf bindings not available")
        return []

    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        feed.ParseFromString(content)
    except Exception as e:
        logger.error(f"Failed to parse Protobuf: {e}")
        return []

    vehicles = []

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue

        v = entity.vehicle

        # Extract vehicle ID (required)
        vehicle_id = v.vehicle.id if v.vehicle.HasField("id") else None
        if not vehicle_id:
            continue

        # Extract trip info
        trip_id = v.trip.trip_id if v.HasField("trip") and v.trip.HasField("trip_id") else "unknown"
        route_id = v.trip.route_id if v.HasField("trip") and v.trip.HasField("route_id") else "unknown"

        # Extract position (required)
        if not v.HasField("position"):
            continue

        lat = v.position.latitude
        lng = v.position.longitude

        # Speed: GTFS-RT provides speed in meters/second, convert to km/h
        speed_mps = v.position.speed if v.position.HasField("speed") else 0.0
        speed_kmh = speed_mps * 3.6

        # Bearing (optional)
        bearing = v.position.bearing if v.position.HasField("bearing") else None

        # Timestamp
        ts = v.timestamp if v.HasField("timestamp") else int(time.time())
        timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)

        # Occupancy status (critical for Rider View)
        occupancy = "UNKNOWN"
        if v.HasField("occupancy_status"):
            occupancy_enum = v.occupancy_status
            occupancy = OCCUPANCY_MAPPING.get(occupancy_enum, "UNKNOWN")

        # Current stop info
        stop_id = v.stop_id if v.HasField("stop_id") else None
        stop_seq = v.current_stop_sequence if v.HasField("current_stop_sequence") else None

        vehicle = VehiclePosition(
            vehicle_id=vehicle_id,
            trip_id=trip_id,
            route_id=route_id,
            latitude=lat,
            longitude=lng,
            speed_kmh=speed_kmh,
            bearing=bearing,
            timestamp=timestamp,
            occupancy_status=occupancy,
            stop_id=stop_id,
            current_stop_sequence=stop_seq,
        )
        vehicles.append(vehicle)

    return vehicles


def fetch_transitland_fallback() -> list[VehiclePosition]:
    """
    Fallback: Fetch vehicle positions from Transitland JSON API.

    Transitland converts Protobuf to JSON, which is easier to debug
    but may have slight latency compared to direct feed.
    """
    try:
        response = requests.get(TRANSITLAND_VEHICLE_POSITIONS_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Transitland fallback failed: {e}")
        return []

    vehicles = []

    # Transitland returns the feed in a specific structure
    entities = data.get("entity", [])

    for entity in entities:
        v = entity.get("vehicle", {})
        if not v:
            continue

        vehicle_info = v.get("vehicle", {})
        trip_info = v.get("trip", {})
        position = v.get("position", {})

        vehicle_id = vehicle_info.get("id")
        if not vehicle_id:
            continue

        lat = position.get("latitude")
        lng = position.get("longitude")
        if lat is None or lng is None:
            continue

        speed_mps = position.get("speed", 0)
        speed_kmh = speed_mps * 3.6

        ts = v.get("timestamp", int(time.time()))
        timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)

        # Map occupancy status
        occupancy_raw = v.get("occupancyStatus", "UNKNOWN")
        occupancy = occupancy_raw if occupancy_raw else "UNKNOWN"

        vehicle = VehiclePosition(
            vehicle_id=vehicle_id,
            trip_id=trip_info.get("tripId", "unknown"),
            route_id=trip_info.get("routeId", "unknown"),
            latitude=lat,
            longitude=lng,
            speed_kmh=speed_kmh,
            bearing=position.get("bearing"),
            timestamp=timestamp,
            occupancy_status=occupancy,
            stop_id=v.get("stopId"),
            current_stop_sequence=v.get("currentStopSequence"),
        )
        vehicles.append(vehicle)

    return vehicles


def load_tape_delay_data() -> list[VehiclePosition]:
    """
    Load pre-recorded vehicle positions for demo fallback.

    "Tape Delay" mode replays recorded data with updated timestamps
    if the live feed is unavailable during the demo.
    """
    try:
        with open(TAPE_DELAY_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Tape delay file not found: {TAPE_DELAY_FILE}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in tape delay file: {e}")
        return []

    vehicles = []
    now = datetime.now(tz=timezone.utc)

    for item in data:
        vehicle = VehiclePosition(
            vehicle_id=item["vehicle_id"],
            trip_id=item["trip_id"],
            route_id=item["route_id"],
            latitude=item["latitude"],
            longitude=item["longitude"],
            speed_kmh=item["speed_kmh"],
            bearing=item.get("bearing"),
            timestamp=now,  # Use current time for tape delay
            occupancy_status=item.get("occupancy_status", "UNKNOWN"),
            stop_id=item.get("stop_id"),
            current_stop_sequence=item.get("current_stop_sequence"),
        )
        vehicles.append(vehicle)

    return vehicles


# =============================================================================
# Amplitude Event Generation
# =============================================================================

def create_amplitude_event(
    event_type: str,
    vehicle: VehiclePosition,
    event_properties: Optional[dict] = None,
) -> dict:
    """
    Create an Amplitude event following the Bus-as-User schema.

    Args:
        event_type: The event name (e.g., "stop_arrival", "signal_delay")
        vehicle: The VehiclePosition object
        event_properties: Additional event-specific properties

    Returns:
        Amplitude event dictionary ready for API submission
    """
    event = {
        "user_id": vehicle.amplitude_user_id,
        "event_type": event_type,
        "time": int(vehicle.timestamp.timestamp() * 1000),  # Amplitude wants milliseconds
        "event_properties": {
            "route_id": vehicle.route_id,
            "trip_id": vehicle.trip_id,
            "latitude": vehicle.latitude,
            "longitude": vehicle.longitude,
            "speed_kmh": round(vehicle.speed_kmh, 2),
            "occupancy_status": vehicle.occupancy_status,
            "is_stopped": vehicle.is_stopped,
            "is_crowded": vehicle.is_crowded,
        },
        "user_properties": {
            "vehicle_type": "bus",
            "agency": "TTC",
        },
        "location_lat": vehicle.latitude,
        "location_lng": vehicle.longitude,
    }

    # Add session ID (Trip ID) for session tracking
    if vehicle.trip_id and vehicle.trip_id != "unknown":
        event["session_id"] = hash(vehicle.trip_id) & 0x7FFFFFFFFFFFFFFF  # Positive int64

    # Merge additional event properties
    if event_properties:
        event["event_properties"].update(event_properties)

    return event


def generate_position_event(vehicle: VehiclePosition) -> dict:
    """Generate a position_update event for a vehicle."""
    return create_amplitude_event("position_update", vehicle)


def generate_stop_arrival_event(
    vehicle: VehiclePosition,
    stop_name: str = "Unknown Stop",
    gap_time_seconds: int = 0,
) -> dict:
    """
    Generate a stop_arrival event when bus arrives at a stop.

    Args:
        vehicle: Current vehicle position
        stop_name: Human-readable stop name
        gap_time_seconds: Schedule deviation (positive = late)
    """
    return create_amplitude_event(
        "stop_arrival",
        vehicle,
        event_properties={
            "stop_id": vehicle.stop_id,
            "stop_name": stop_name,
            "gap_time": gap_time_seconds,
            "stop_sequence": vehicle.current_stop_sequence,
        },
    )


def generate_crowding_event(vehicle: VehiclePosition) -> dict:
    """Generate a passenger_crowding event when occupancy is high."""
    return create_amplitude_event(
        "passenger_crowding",
        vehicle,
        event_properties={
            "crowding_level": vehicle.occupancy_status,
        },
    )


def generate_short_turn_event(
    vehicle: VehiclePosition,
    last_stop_id: str,
    gap_time_at_turn: int,
) -> dict:
    """
    Generate a short_turn event when trip ends early.

    This is the KEY predictive event for the Rider View.
    """
    return create_amplitude_event(
        "short_turn",
        vehicle,
        event_properties={
            "last_stop_id": last_stop_id,
            "gap_time_at_turn": gap_time_at_turn,
            "terminated_early": True,
        },
    )


# =============================================================================
# Amplitude API Client
# =============================================================================

class AmplitudeClient:
    """Client for sending events to Amplitude HTTP API."""

    def __init__(self, api_key: str, dry_run: bool = False):
        self.api_key = api_key
        self.dry_run = dry_run
        self.event_buffer: list[dict] = []
        self.events_sent = 0

    def queue_event(self, event: dict):
        """Add an event to the buffer."""
        self.event_buffer.append(event)

        # Auto-flush if buffer is full
        if len(self.event_buffer) >= AMPLITUDE_BATCH_SIZE:
            self.flush()

    def queue_events(self, events: list[dict]):
        """Add multiple events to the buffer."""
        for event in events:
            self.queue_event(event)

    def flush(self):
        """Send all buffered events to Amplitude."""
        if not self.event_buffer:
            return

        events_to_send = self.event_buffer[:AMPLITUDE_BATCH_SIZE]
        self.event_buffer = self.event_buffer[AMPLITUDE_BATCH_SIZE:]

        if self.dry_run:
            logger.info(f"[DRY RUN] Would send {len(events_to_send)} events to Amplitude")
            for event in events_to_send[:3]:  # Log first 3 for debugging
                logger.debug(f"  Event: {event['event_type']} for {event['user_id']}")
            self.events_sent += len(events_to_send)
            return

        if not self.api_key:
            logger.warning("No Amplitude API key configured, skipping send")
            return

        payload = {
            "api_key": self.api_key,
            "events": events_to_send,
        }

        try:
            response = requests.post(
                AMPLITUDE_BATCH_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"Sent {len(events_to_send)} events to Amplitude "
                    f"(events_ingested: {result.get('events_ingested', 'unknown')})"
                )
                self.events_sent += len(events_to_send)
            elif response.status_code == 429:
                # Rate limited - implement backoff
                retry_after = int(response.headers.get("Retry-After", 30))
                logger.warning(f"Rate limited by Amplitude. Retrying in {retry_after}s")
                time.sleep(retry_after)
                # Re-queue events
                self.event_buffer = events_to_send + self.event_buffer
            else:
                logger.error(
                    f"Amplitude API error: {response.status_code} - {response.text}"
                )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send events to Amplitude: {e}")
            # Re-queue events for retry
            self.event_buffer = events_to_send + self.event_buffer


# =============================================================================
# Main Ingestion Loop
# =============================================================================

class GTFSIngestionService:
    """Main service for continuous GTFS-RT ingestion."""

    def __init__(
        self,
        amplitude_client: AmplitudeClient,
        use_tape_delay: bool = False,
    ):
        self.amplitude = amplitude_client
        self.use_tape_delay = use_tape_delay
        self.previous_positions: dict[str, VehiclePosition] = {}
        self.running = False

    def fetch_vehicles(self) -> list[VehiclePosition]:
        """Fetch current vehicle positions from the best available source."""

        if self.use_tape_delay:
            logger.info("Using tape delay (recorded) data")
            return load_tape_delay_data()

        # Try primary Protobuf feed first
        logger.debug(f"Fetching from {TTC_VEHICLE_POSITIONS_URL}")
        content = fetch_protobuf_feed(TTC_VEHICLE_POSITIONS_URL)

        if content:
            vehicles = parse_vehicle_positions_protobuf(content)
            if vehicles:
                logger.info(f"Fetched {len(vehicles)} vehicles from TTC Protobuf feed")
                return vehicles

        # Fallback to Transitland
        logger.warning("Primary feed failed, trying Transitland fallback...")
        vehicles = fetch_transitland_fallback()

        if vehicles:
            logger.info(f"Fetched {len(vehicles)} vehicles from Transitland")
            return vehicles

        logger.error("All feed sources failed!")
        return []

    def process_vehicles(self, vehicles: list[VehiclePosition]) -> list[dict]:
        """
        Process vehicle positions and generate Amplitude events.

        This method implements the core logic for detecting:
        - Position updates
        - Stop arrivals
        - Crowding events
        - Potential short turns (high-risk detection)
        """
        events = []

        for vehicle in vehicles:
            # Always generate a position update event
            events.append(generate_position_event(vehicle))

            # Check for crowding transition
            prev = self.previous_positions.get(vehicle.vehicle_id)
            if vehicle.is_crowded:
                if prev is None or not prev.is_crowded:
                    # Crowding just started
                    events.append(generate_crowding_event(vehicle))

            # Check for stop arrival (vehicle stopped near a stop)
            if vehicle.is_stopped and vehicle.stop_id:
                # TODO: Integrate with trip updates to get actual gap_time
                # For now, we'll set gap_time=0 (to be enriched by trip updates)
                events.append(
                    generate_stop_arrival_event(
                        vehicle,
                        stop_name=f"Stop {vehicle.stop_id}",
                        gap_time_seconds=0,
                    )
                )

            # Update previous position cache
            self.previous_positions[vehicle.vehicle_id] = vehicle

        return events

    def run_once(self) -> int:
        """
        Run a single ingestion cycle.

        Returns:
            Number of events generated
        """
        vehicles = self.fetch_vehicles()

        if not vehicles:
            logger.warning("No vehicles received this cycle")
            return 0

        events = self.process_vehicles(vehicles)

        if events:
            self.amplitude.queue_events(events)
            self.amplitude.flush()

        return len(events)

    def run(self, poll_interval: int = GTFS_POLL_INTERVAL_SECONDS):
        """
        Run continuous ingestion loop.

        Args:
            poll_interval: Seconds between feed fetches
        """
        self.running = True
        logger.info(f"Starting GTFS ingestion loop (poll interval: {poll_interval}s)")

        while self.running:
            try:
                start_time = time.time()
                event_count = self.run_once()
                elapsed = time.time() - start_time

                logger.info(
                    f"Cycle complete: {event_count} events in {elapsed:.2f}s "
                    f"(total sent: {self.amplitude.events_sent})"
                )

                # Sleep for remaining time in interval
                sleep_time = max(0, poll_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except KeyboardInterrupt:
                logger.info("Shutting down ingestion service...")
                self.running = False
            except Exception as e:
                logger.exception(f"Error in ingestion cycle: {e}")
                time.sleep(5)  # Brief pause before retry

    def stop(self):
        """Stop the ingestion loop."""
        self.running = False


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Transit Oracle GTFS-RT Ingestion Service"
    )
    parser.add_argument(
        "--tape-delay",
        action="store_true",
        help="Use recorded data instead of live feed (demo fallback)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse feed but don't send events to Amplitude",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run single fetch cycle and exit (for testing)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=GTFS_POLL_INTERVAL_SECONDS,
        help=f"Seconds between feed fetches (default: {GTFS_POLL_INTERVAL_SECONDS})",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize Amplitude client
    amplitude = AmplitudeClient(
        api_key=AMPLITUDE_API_KEY,
        dry_run=args.dry_run,
    )

    # Initialize ingestion service
    service = GTFSIngestionService(
        amplitude_client=amplitude,
        use_tape_delay=args.tape_delay,
    )

    if args.once:
        # Single cycle mode
        event_count = service.run_once()
        logger.info(f"Single cycle complete: {event_count} events")
    else:
        # Continuous mode
        service.run(poll_interval=args.poll_interval)


if __name__ == "__main__":
    main()
