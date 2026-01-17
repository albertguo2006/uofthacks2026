# Transit Oracle — The Self-Optimizing Urban Mobility Platform

A comprehensive research report and implementation blueprint for the UofTHacks 2026 Amplitude Challenge.

## Executive summary

Transit Oracle is a prototype for a "self-improving" urban mobility product that follows the Data → Insights → Action feedback loop. It combines real-time GTFS-RT telemetry (TTC), static infrastructure data (City of Toronto Open Data), and granular user behavioral analytics (Amplitude) to sense problems, generate insights with AI agents, and act (nudge users, surface bottlenecks, or trigger interventions).

## Contents

1. The paradigm shift
2. Phase 1 — Analytics (sensory system)
3. Phase 2 — Analysis (cognitive system)
4. Phase 3 — Action (closing the loop)
5. Engineering roadmap
6. Strategic differentiation
7. Risks & mitigations
8. Conclusion
9. Appendix — event schema (JSON)

---

## 1. The paradigm shift

Traditional transit apps passively display vehicle locations and ETAs. Transit Oracle treats the network as an instrumented system where both vehicles and commuters are first-class entities. The product continuously:

- Observes (high-frequency telemetry + user events)
- Learns (AI agents find causal patterns)
- Adapts (reroutes, nudges, advocacy)

This lets the system proactively improve the commute experience rather than only informing users after the fact.

## 2. Phase 1 — Analytics (the sensory system)

High-fidelity event instrumentation is the foundation.

### Digital-twin model

- Treat vehicles as users (e.g., `vehicle_ttc_8421`) so we can use retention/funnel tools on assets.
- Ingest GTFS-RT (vehicle positions, occupancy), signal location data, and user events into a unified Amplitude schema.

Core vehicle events (examples):

- `vehicle_position_update` — heartbeat (route_id, lat/lon, speed_kmh, occupancy_status, nearest_signal_id, dwell_time)
- `service_anomaly_detected` — synthetic (anomaly_type, severity)

Core user events (examples):

- `trip_plan_initiated` (origin/destination, time_of_day)
- `route_selected` (predicted_duration, inferred crowding_tolerance)
- `rage_tap` (rapid repeated taps — proxy for frustration)
- `trip_abandoned` (location_at_dropoff, nearest_vehicle_id)

Integration architecture: a FastAPI ingestion service polls GTFS-RT, enriches events with nearest-signal context, batches to Amplitude HTTP API v2, and deduplicates via `insert_id`.

## 3. Phase 2 — Analysis (the cognitive system)

AI Agents (Orchestrator → Specialists) act as virtual data scientists:

- Metrics Agent queries Amplitude metrics.
- Context Agent synthesizes qualitative signals (rage taps, reports).
- Orchestrator coordinates insight generation and action triggers.

Example insight: the Misery Index. Define:

$$
	ext{Misery Index} = \left( \frac{\text{Signal Dwell Time}}{\text{Total Run Time}} \right) \times \text{Crowding Multiplier} + \text{Frustration Factor}
$$

Where crowding multiplier is a weight derived from `occupancy_status` and frustration factor comes from aggregated `rage_tap` frequency. Agents can detect "silent stalls" by correlating clusters of slow vehicles with user frustration spikes and emit `incident_detected` events.

## 4. Phase 3 — Action (closing the loop)

Actions driven by insights include:

- Dynamic rerouting nudges (in-app guides or push notifications)
- Virtual Transit Signal Priority (vTSP) as an advocacy tool (collect votes for problem intersections)
- Natural-language "Commute Doctor" chat to explain incidents and recommend alternatives

Example nudge message:

> Optimization Alert: The 504 is stalled at Bathurst. Walk 3 minutes north to take the 501 Queen — it's moving 40% faster.

## 5. Engineering roadmap (36–48 hour hackathon)

Stack (suggested):

- Frontend: React / React Native (Expo) + Mapbox GL
- Backend: Python (FastAPI)
- Real-time cache: Redis
- Analytics: Amplitude (HTTP API v2)
- AI/LLM: LangChain or similar with GPT/Claude
- Hosting: Vercel (frontend), Render/Railway (backend)

Milestones:

- Phase 1 (0–8h): GTFS-RT poller, signal overlay, amplitude relay (batching & dedupe).
- Phase 2 (8–20h): map UI, instrumentation, rage-tap detector.
- Phase 3 (20–32h): agentic analysis (LangChain tools), `/chat` endpoint.
- Phase 4 (32–36h): demo dashboard (heatmap, AI decisions log, impact chart), "Simulate Chaos" button.

## 6. Strategic differentiation

- Novel identity model: vehicles as users enables retention-shaped analytics on assets.
- Agent orchestration demonstrates autonomous analytics and technical depth.
- Equity focus: Misery Index by neighborhood highlights transit inequity.

## 7. Risks & mitigations

- Rate limits: batch events and only forward significant state changes (e.g., moved > 50m or occupancy change).
- Latency: use Redis for sub-second decisions and Amplitude for historic learning.

## 8. Conclusion

Transit Oracle is a blueprint for a commute that senses, reasons, and acts. By combining instrumentation, AI agents, and closed-loop interventions, the product demonstrably improves user outcomes and can be built as a hackathon prototype.

## 9. Appendix — Event schema (JSON examples)

### A. Infrastructure event: `vehicle_position_update`

```json
{
  "user_id": "bus_vehicle_8421",
  "device_id": "gps_tracker_8421",
  "event_type": "vehicle_position_update",
  "time": 1735732800000,
  "event_properties": {
    "route_number": "504",
    "direction": "Eastbound",
    "latitude": 43.6452,
    "longitude": -79.3806,
    "speed_kmh": 3.2,
    "congestion_level": "STOP_AND_GO",
    "occupancy_status": "STANDING_ROOM_ONLY",
    "nearest_signal_id": "PX_291",
    "delay_vs_schedule_seconds": 340
  },
  "insert_id": "veh_8421_1735732800000"
}
```

### B. User event: `trip_friction_detected`

```json
{
  "user_id": "user_hash_99a",
  "event_type": "trip_friction_detected",
  "event_properties": {
    "trigger": "rage_tap_cluster",
    "click_velocity": 8,
    "current_route_context": "504_King",
    "associated_vehicle_occupancy": "CRUSHED_STANDING_ROOM_ONLY",
    "misery_index_score": 9.2
  }
}
```

### C. Agent action: `intervention_generated`

```json
{
  "user_id": "user_hash_99a",
  "event_type": "intervention_generated",
  "event_properties": {
    "intervention_type": "reroute_suggestion",
    "suggested_route": "501_Queen",
    "reason": "silent_stall_detected",
    "estimated_time_saved_minutes": 14
  }
}
```

Transit Oracle: The Self-Optimizing Urban Mobility PlatformA Comprehensive Research Report & Strategic Implementation Blueprint for the UofTHacks 2026 Amplitude ChallengeExecutive SummaryThis document articulates the architectural vision, technical specification, and strategic execution plan for Transit Oracle, a submission designed to secure victory in the UofTHacks 2026 Amplitude Technical Challenge. The challenge explicitly calls for the creation of a "mini self-improving product" that leverages the "Data $\rightarrow$ Insights $\rightarrow$ Action" feedback loop—a core philosophy driving the modern digital analytics landscape. Transit Oracle answers this call by reimagining the urban commute not as a static consumption of schedule data, but as a dynamic, agentic negotiation between a user’s intent and the city’s infrastructure constraints.Unlike traditional transit applications that passively display vehicle locations, Transit Oracle functions as an autonomous optimization engine. It synthesizes real-time General Transit Feed Specification (GTFS-RT) telemetry from the Toronto Transit Commission (TTC), static infrastructure data from the City of Toronto’s Open Data portal, and granular user behavioral analytics via Amplitude’s platform. By treating transit vehicles as "users" within the analytics schema and deploying Amplitude AI Agents to monitor the friction between infrastructure supply and commuter demand, the system creates a self-correcting feedback loop. This report details how Transit Oracle moves beyond simple observation to proactive intervention, satisfying the "Sense $\rightarrow$ Decide $\rightarrow$ Act" framework required to demonstrate a truly self-improving digital product.1. The Paradigm Shift: From Passive Tracking to Agentic MobilityThe prevailing model for transit technology is passive observation. Users open an app, query a route, and receive a static prediction based on current vehicle positions. This model fails to account for the stochastic nature of urban systems—traffic signal failures, sudden crowding surges, and the "silent stalls" that occur before official service alerts are issued. To win the Amplitude Challenge, Transit Oracle must transcend this paradigm by introducing agency into the system.1.1 The Theoretical Framework of the Self-Improving ProductA "self-improving product," as defined in the context of Amplitude’s product philosophy, is one that continuously observes user behavior, learns patterns from that behavior using AI, and adapts the experience over time.1 This concept aligns with the broader industry shift towards "Autonomous Analytics," where the bottleneck of human analysis is removed from the critical path of decision-making.In the context of Transit Oracle, the "product" is the commute itself. The system views the transit network as a customizable funnel where the user's goal is "Trip Completion" and the friction points are "Delay," "Crowding," and "Uncertainty." By instrumenting both the user and the vehicle, the system can optimize the funnel in real-time.Observation (Analytics): The system ingests high-frequency state changes from the physical world (bus locations, traffic signals) and the digital world (user route selections, abandonment rates).Learning (Analysis): AI Agents, modeled after Amplitude’s internal architecture (Orchestrator $\rightarrow$ Specialist), analyze this data to identify causal relationships. For example, learning that "Users on the 504 King Streetcar abandon the app 40% more frequently when the vehicle dwells at Spadina Ave for >120 seconds."Adaptation (Action): The system autonomously alters its own logic. It might dynamically deprioritize the 504 King route in search results for users with a low "Misery Tolerance," or trigger a push notification suggesting a specific alternative before the user even realizes the delay has occurred.41.2 The "Data $\rightarrow$ Insights $\rightarrow$ Action" LoopSuccess in this challenge requires a rigid adherence to the loop methodology. Every feature in Transit Oracle must map to one of these three stages.5StageTransit Oracle ImplementationAmplitude Feature UtilizationDataIngestion of TTC GTFS-RT (Vehicles) + User Events (Interactions) + City Infrastructure (Signals).HTTP API v2, Event Segmentation, Identity ResolutionInsightsAI Agents detecting "Silent Incidents" via anomaly detection on vehicle velocity and dwell times.Dashboard REST API, Root Cause Analysis, Cohort AnalysisActionDynamic re-ranking of route suggestions; Proactive "Nudges" to users; Automated "Virtual" Signal Priority requests.In-App Guides (Simulated), Push Notifications, Adaptive UIThis structure ensures that we are not merely building a utility, but a system that evolves. The "Action" phase feeds back into the "Data" phase (did the user accept the reroute?), creating the closed loop essential for the "Self-Improving" classification.2. Phase 1: Analytics — The Sensory SystemThe foundation of any self-improving product is high-fidelity data. For Transit Oracle, this requires a dual-track ingestion strategy that normalizes disparate data sources—ephemeral transit telemetry and persistent user behavior—into a unified event schema within Amplitude.2.1 The "Digital Twin" Data ModelTo analyze the transit network effectively, we must treat physical assets as "users" within the Amplitude project. This novel approach allows us to utilize Amplitude’s powerful user retention and funnel analysis tools on buses and streetcars.12.1.1 The Vehicle-as-User SchemaBy assigning a unique user_id to every transit vehicle (e.g., vehicle_ttc_8421), we can track its "journey" through the city as a series of events. This enables us to ask questions like "What is the retention rate of buses on the 501 Queen line?" (i.e., how many complete the route without severe deviation).Core Infrastructure Events:vehicle_position_update: This is the heartbeat event, triggered every 10-20 seconds as the poller fetches data from the TTC GTFS-RT feed.7Properties:route_id: The specific line (e.g., "504").speed_kmh: Derived from the delta between consecutive GPS pings.occupancy_status: A critical enum provided by the TTC (e.g., MANY_SEATS_AVAILABLE, STANDING_ROOM_ONLY, CRUSHED_STANDING_ROOM_ONLY).9congestion_level: Inferred status (e.g., STOP_AND_GO, RUNNING_SMOOTHLY).current_status: (e.g., IN_TRANSIT_TO, STOPPED_AT).Context: This data creates a baseline of "supply." If supply quality degrades (speed drops, occupancy rises), the "product" is failing.signal_approach: Triggered when a vehicle's geolocation intersects with the geofence of a known City of Toronto traffic signal.11Properties:intersection_name: e.g., "Queen St W at Spadina Ave".signal_id: Unique identifier from the Open Data dataset.dwell_time: Duration the vehicle remains within the signal's influence radius.Context: This event is crucial for identifying "Silent Stalls"—delays caused by signal timing rather than passenger boarding.service_anomaly_detected: A synthetic event generated by our backend when a vehicle violates heuristic thresholds (e.g., stationary for >3 minutes between stops).13Properties:anomaly_type: "bunching", "gapping", "silent_stall".severity: Calculated score based on deviation from schedule.2.1.2 The Commuter Behavioral SchemaUser events track the "demand" side of the equation. We must capture not just what the user does, but how they feel about it (inferred through interaction patterns).Core User Events:trip_plan_initiated: The user searches for a route.Properties: origin_geo, destination_geo, time_of_day, weather_context.route_selected: The user commits to a specific option.Properties: predicted_duration, crowding_tolerance (inferred), transfer_count.rage_tap: Rapid, repeated tapping on the "Refresh" or "Map" elements.Properties: screen_context, latency_ms.Context: This is a high-fidelity proxy for user frustration. A rage tap during a silent_stall is a strong signal for intervention.1trip_abandoned: The user closes the app or cancels navigation mid-trip.Properties: location_at_dropoff, nearest_vehicle_id, cumulative_delay.2.2 Integration ArchitectureThe ingestion layer serves as the bridge between raw public data and Amplitude’s structured event log.Data Pipeline Components:FastAPI Ingestion Service: A Python-based microservice that polls the TTC gtfs-realtime Protobuf feed every 10 seconds. It parses the binary data using gtfs-realtime-bindings and enriches it with static signal data.7Traffic Signal Overlay: We utilize the City of Toronto's "Traffic Signal Vehicle and Pedestrian Volumes" and "Traffic Signal Locations" datasets 14 to map every GPS coordinate to its nearest signalized intersection. This allows us to attribute delay to specific physical infrastructure.Amplitude HTTP API v2: The service acts as a relay, formatting the enriched data into JSON payloads compatible with Amplitude’s ingestion endpoint.Rate Limiting Strategy: To respect the 1000 events/second limit of the Amplitude Starter Plan 15, the relay implements a buffering bucket. Events are batched in groups of 10-50. During the hackathon demo, we will filter the stream to ingest only high-density routes (e.g., 504 King, 501 Queen, 510 Spadina) to ensure real-time fidelity without throttling.Deduplication: We will utilize the insert_id field, constructing a composite key (e.g., veh_{id}_{timestamp}) to ensure that network retries do not corrupt the analytics.153. Phase 2: Analysis — The Cognitive SystemWith data flowing into Amplitude, the "Analysis" phase involves interpreting this telemetry to find meaning. This is where Transit Oracle differentiates itself from a standard dashboard. We employ AI Agents—autonomous scripts powered by LLMs (via LangChain or Composio)—to act as virtual data scientists.163.1 The Agentic Architecture: Orchestrator & SpecialistsDrawing inspiration from Amplitude's own "AI Agent" architecture 18, Transit Oracle utilizes a multi-agent system to process insights.The Orchestrator Agent: This is the primary interface. It receives the high-level goal ("Optimize Commute Efficiency") and delegates tasks to specialized sub-agents.The Metrics Agent: Responsible for querying the Amplitude Dashboard REST API.19 It runs continuous checks on key metrics like "Average Speed per Route Segment" and "User Drop-off Rate."The Context Agent: Responsible for qualitative synthesis. It ingests unstructured data (e.g., user feedback text, "rage tap" patterns) and correlates it with the quantitative metrics.3.2 Automated Insight GenerationThe goal of the Analysis phase is to generate "Insights" that a rules-based engine would miss.3.2.1 The "Misery Index" CorrelationThe Metrics Agent is tasked with calculating a dynamic Misery Index for every active route. This index is a composite metric defined within Amplitude 20:$$\text{Misery Index} = \left( \frac{\text{Signal Dwell Time}}{\text{Total Run Time}} \right) \times \text{Crowding Multiplier} + \text{Frustration Factor}$$Where:Signal Dwell Time is derived from vehicle_position_update events near intersections.Crowding Multiplier applies a weight based on the occupancy_status (1.0 for EMPTY, 2.5 for CRUSHED_STANDING_ROOM_ONLY).Frustration Factor is derived from the frequency of rage_tap events in that geofence.The Insight: The Agent might discover, for example, that "While Route 504 is only 5 minutes delayed, the Misery Index has spiked to 8.5 due to 'Crushed' conditions and signal failures at Bathurst. This correlates with a 30% increase in app churn." This is a nuanced insight that pure ETA tracking misses.3.2.2 Detecting "Silent Incidents"Traditional transit apps rely on the agency to publish service alerts. These are often delayed by 15-30 minutes. Transit Oracle’s AI Agent detects incidents before they are official by analyzing the "Digital Twin" fleet behavior.4Algorithm:Cluster Analysis: The Agent observes that 3+ vehicles on Route 501 have speed_kmh < 2 for a duration exceeding the 90th percentile of historical dwell times at that location.Confirmation: The Agent checks for a corresponding spike in rage_tap events from users located in that cluster.Classification: If both conditions are met, the Agent classifies this as a "Silent Stall" and generates an internal alert event: incident_detected { type: "silent_stall", confidence: 0.92 }.3.3 Cohort Analysis for PersonalizationThe Analysis layer also segments users to tailor the experience. Using Amplitude’s Behavioral Cohorts 21, the AI identifies distinct personas:"Speed Demons": Users who consistently choose the fastest route regardless of crowding."Comfort Seekers": Users who abandon trips when occupancy_status is STANDING_ROOM_ONLY."Risk Averse": Users who check the app 5+ times before leaving.The AI Agent tags users with these properties (user_properties: { persona: "comfort_seeker" }), which are then used to weight the routing algorithm in the Action phase.4. Phase 3: Action — Closing the LoopThe final and most critical phase of the challenge is "Action." Insights are useless without intervention. Transit Oracle demonstrates "self-improvement" by using the insights generated in Phase 2 to autonomously alter the product experience in Phase 3.4.1 Dynamic Rerouting (The "Nudge")When the AI Agent detects a "Silent Stall" or a high "Misery Index" on a user’s intended route, it triggers an intervention.Mechanism:Trigger: The incident_detected event is pushed to the backend.Decision: The AI evaluates alternative paths. For a user on the 504 King (stalled), it checks the 501 Queen (parallel route).Action: If the 501 Queen has a Misery Index < 4.0, the system pushes an In-App Guide (simulated via notification) to the user: "Optimization Alert: The 504 is stalled at Bathurst. Walk 3 minutes north to take the 501 Queen—it’s moving 40% faster."This is the "Self-Improving" aspect: The product proactively saves the user from a bad experience based on real-time learning, rather than waiting for the user to find out the hard way.4.2 Virtual Transit Signal Priority (vTSP)Real Transit Signal Priority (TSP) allows buses to extend green lights.22 While we cannot control physical traffic lights in a hackathon, Transit Oracle implements Virtual TSP as an advocacy and planning tool.Mechanism:Analysis: The Agent identifies the specific intersection (e.g., Spadina & Queen) causing the highest aggregate delay for the fleet.Action: The app highlights this intersection on the map with a "Bottleneck" icon.User Value: When a user is stuck at this light, the app notifies them: "You are currently delayed by the Spadina traffic signal. This intersection has caused 45 hours of cumulative passenger delay today. Tap to vote for Signal Priority here."Feedback Loop: These "votes" are logged as user_advocacy_events in Amplitude, creating a heatmap of commuter demand for infrastructure change.4.3 The "Commute Doctor" Chat InterfaceTo fully leverage the Generative AI aspect, Transit Oracle includes a natural language interface where users can query the system’s "brain" directly.24Interaction Example:User: "Why is my commute so bad today?"Agent (Backend): The LLM retrieves the user's recent trip_history and correlates it with the vehicle_position_update stream for their route.Agent (Response): "It looks like your usual route, the 504 King, is experiencing severe bunching due to a stalled vehicle at Portland St. There are currently 3 streetcars stuck in a row. I recommend taking the GO Train from Exhibition, which is running on schedule."This transforms the app from a dashboard into a consultant.5. Engineering the Solution: Implementation RoadmapThis section provides the specific technical steps to build Transit Oracle within the constraints of a hackathon (36-48 hours).5.1 Technology StackFrontend: React Native (Expo) or React Web (Mobile First). Mapping via Mapbox GL JS.Backend: Python (FastAPI). Chosen for its robust async support and libraries for GTFS and AI agents.Data Store: Redis (for real-time vehicle cache), Amplitude (for historical analysis and events).AI/LLM: LangChain (Python) or Composio, utilizing OpenAI GPT-4o or Anthropic Claude 3.5 Sonnet for the reasoning engine.25Infrastructure: Vercel (Frontend), Render/Railway (Backend).5.2 Step-by-Step Implementation GuidePhase 1: The Ingestion Engine (Hours 0-8)The priority is to establish the data pipeline. Without data, there is no AI.Amplitude Setup: Initialize a new Amplitude Project. Configure the API Key and Secret. Enable the "Starter" plan to get 100k events/month limit.21GTFS-RT Poller:Write a Python script using google.transit.gtfs_realtime_pb2.Fetch https://retro.umoiq.com/service/publicXMLFeed?command=vehicleLocations&a=ttc&t=0 (or the official Open Data endpoint).Parse the Protocol Buffer. Extract id, lat, lon, route_id, occupancy_status (if available).Action: Map the raw data to the vehicle_position_update schema defined in Section 2.1.Traffic Signal Integration:Download the "Traffic Signal Locations" CSV from Toronto Open Data.Load this into a KD-Tree or simplistic geospatial index in memory for fast "nearest neighbor" lookups (to determine if a bus is "at a signal").Amplitude Relay:Implement the send_to_amplitude function using requests.post to https://api2.amplitude.com/2/httpapi.Crucial: Implement a basic buffer. Collect events for 10 seconds, then flush in a single batch to avoid HTTP overhead and rate limits.26Phase 2: The Client Experience (Hours 8-20)Build the "face" of the Oracle.Map Interface: Render the user's location and the "Ghost" vehicle icons based on the backend data.Instrumentation: Integrate the Amplitude SDK.Wrap the "Plan Trip" button with an event tracker: amplitude.track('trip_plan_initiated').Create a "Rage Click" detector: If click_count > 5 within 2000ms, fire amplitude.track('rage_tap').Feedback UI: Add a button on the "Active Trip" screen: "Report Full Bus." This fires the user_report event used for ground-truthing.Phase 3: The AI "Brain" (Hours 20-32)Build the Agentic logic.Agent Setup: Initialize a LangChain agent with access to two tools:Tool 1: get_amplitude_chart: Fetches a specific segmentation chart (e.g., "Avg Speed over last hour").Tool 2: get_current_vehicle_state: Fetches the real-time Redis cache of vehicle positions.Reasoning Loop:Create a scheduled task (cron) that runs every 5 minutes.Prompt: "Analyze the speed of vehicles on Route 504. Compare it to the historical baseline from Amplitude. If the deviation is > -20%, identify the cluster of vehicles responsible and return a 'Silent Stall' alert."Chatbot Integration: Expose an endpoint /chat that accepts a user string, injects the current vehicle context into the prompt, and returns the LLM's advice.Phase 4: The Loop Visualization (Hours 32-36)For the demo, you must show the loop working.The "God Mode" Dashboard: Create a public-facing dashboard (or a view in your app) that visualizes the "Self-Improvement."Panel A: "Real-Time Friction" (Heatmap of slow buses).Panel B: "AI Decisions" (Log of "Reroute Nudges" sent).Panel C: "Impact" (Chart showing "Time Saved" by users who accepted the nudge).Simulation: Since real traffic is unpredictable, build a "Simulate Chaos" button in your admin panel that artificially drops the speed of all buses on King St to 0. This allows you to demonstrate the AI reacting to a stall during the 3-minute judge presentation.6. Strategic Differentiation: How to WinTo secure high marks across all judging criteria, Transit Oracle explicitly targets the "Bonus" and "Innovation" requirements.6.1 Addressing the "Innovation & Amplitude Fit" Criteria (15%)Novel Use of Identity: By assigning User IDs to buses, we invert the typical analytics model. We analyze "Bus Retention" (does the bus stay on schedule?) and "Bus Churn" (does it go out of service?). This creative schema application demonstrates a deep understanding of Amplitude's flexibility beyond just tracking humans.The "Self-Improving" Narrative: We explicitly frame the product not as a tool for viewing data, but as a system that heals itself. When congestion rises, the app "improves" by routing around it. This perfectly mirrors the "Sense $\rightarrow$ Decide $\rightarrow$ Act" prompt.16.2 Addressing "Technical Depth" (25%)Complex Correlation: We don't just show location; we correlate occupancy with abandonment. This requires joining two distinct datasets (infrastructure and behavior), showing significant technical sophistication.AI Agent Orchestration: Using a multi-agent architecture (Metrics Agent + Context Agent) is far superior to a simple "chatbot wrapper." It shows we understand how to build autonomous systems that reason over data.6.3 Addressing "Product Impact" (25%)The Equity Angle: By analyzing the "Misery Index" across different neighborhoods (derived from origin_geo), Transit Oracle can highlight transit inequity. Users in underserved areas often face higher misery indices. Highlighting this "Social Good" aspect resonates strongly with judges looking for impactful solutions.Quantifiable Value: The application calculates "Time Saved" for every user interaction. "You saved 12 minutes by taking the 501." This metric proves value instantly.7. Overcoming Constraints & Risks7.1 The Rate Limit ChallengeThe Amplitude Starter Plan limits ingestion to ~1000 events/second. The TTC network generates massive telemetry.Solution: We implement Smart Filtering. The Ingestion Engine will only forward events to Amplitude if the vehicle state has changed significantly (e.g., moved > 50 meters or changed occupancy status). Stationary vehicles do not generate repetitive heartbeat events in Amplitude, conserving the quota while maintaining data fidelity.157.2 The Latency GapAmplitude charts typically have a small indexing delay (minutes). Real-time routing needs sub-second accuracy.Solution: We use a Hybrid Data Store. The "Real-Time Action" (Rerouting) relies on the Redis cache of the raw GTFS feed for immediate decisions. The "Self-Improving Insight" (Learning patterns) relies on Amplitude’s historical data. The AI synthesizes both: "Redis says the bus is here; Amplitude says this location usually has a 5-minute signal delay."8. ConclusionTransit Oracle represents the future of urban mobility—a system that does not merely digitize a paper schedule, but actively manages the flow of people through a constrained network. By combining the rigorous event instrumentation of Amplitude with the reasoning capabilities of Generative AI, we create a product that gets smarter with every trip taken.It satisfies the challenge by:Tracking Behavioral Data: Capturing the friction and intent of the commuter.Applying AI: Using Agents to diagnose system health and user sentiment.Closing the Loop: Actively intervening to optimize the journey.This is not just a transit tracker; it is an automated logistics engine for the human experience.Appendix: Event Schema Reference (JSON)A. Infrastructure Event: vehicle_position_updateJSON{
  "user_id": "bus_vehicle_8421",
  "device_id": "gps_tracker_8421",
  "event_type": "vehicle_position_update",
  "time": 1735732800000,
  "event_properties": {
    "route_number": "504",
    "direction": "Eastbound",
    "latitude": 43.6452,
    "longitude": -79.3806,
    "speed_kmh": 3.2,
    "congestion_level": "STOP_AND_GO",
    "occupancy_status": "STANDING_ROOM_ONLY",
    "nearest_signal_id": "PX_291",
    "delay_vs_schedule_seconds": 340
  },
  "insert_id": "veh_8421_1735732800000"
}
B. User Event: trip_friction_detectedJSON{
  "user_id": "user_hash_99a",
  "event_type": "trip_friction_detected",
  "event_properties": {
    "trigger": "rage_tap_cluster",
    "click_velocity": 8,
    "current_route_context": "504_King",
    "associated_vehicle_occupancy": "CRUSHED_STANDING_ROOM_ONLY",
    "misery_index_score": 9.2
  }
}
C. Agent Action: intervention_generatedJSON{
  "user_id": "user_hash_99a",
  "event_type": "intervention_generated",
  "event_properties": {
    "intervention_type": "reroute_suggestion",
    "suggested_route": "501_Queen",
    "reason": "silent_stall_detected",
    "estimated_time_saved_minutes": 14
  }
}
