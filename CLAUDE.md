# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SkillPulse** - An AI-powered technical interview and online assessment platform that analyzes behavioral coding patterns to build an "Engineering DNA" profile for candidates. The platform uses semantic event tracking, multi-model AI analysis, and video understanding to move beyond binary Pass/Fail metrics.

### Core Concept
- Tracks HOW candidates code (testing habits, debugging efficiency, optimization patterns)
- Generates real-time "Engineering DNA Radar Charts" showing skills across 5 dimensions
- Uses AI to detect frustration and provide contextual hints
- Analyzes interview videos for communication skills and key moments

## Common Development Commands

### Running the Development Environment

```bash
# Start all services with Docker Compose
docker-compose -f docker-compose.dev.yml up

# Or run individual services:
# API (FastAPI backend)
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Web (Next.js frontend)
cd apps/web
npm install
npm run dev

# Sandbox Runner (code execution service)
cd apps/sandbox-runner
docker build -t sandbox-runner .
docker run -p 8080:8080 sandbox-runner
```

### Testing and Linting

```bash
# Run API tests
cd apps/api
pytest tests/

# Run frontend tests
cd apps/web
npm run test
npm run lint

# Type checking
cd apps/web
npm run type-check
```

### Database Operations

```bash
# Seed demo data
cd scripts
python seed_demo_data.py

# Generate events for testing
python generate_events.py

# Train ML models
python train_models.py
```

## Architecture

### Tech Stack
- **Frontend**: Next.js 14, React, Tailwind CSS, Monaco Editor, Recharts
- **Backend**: FastAPI (Python 3.11+), Motor (async MongoDB driver)
- **Database**: MongoDB Atlas
- **AI Services**:
  - Backboard.io (multi-model AI routing: Claude, GPT-4o, Gemini, Cohere)
  - TwelveLabs (video analysis and search)
- **Analytics**: Amplitude (behavioral event tracking)
- **Code Execution**: Custom Docker sandbox runner

### Key Services Architecture

1. **Event Flow**: Monaco Editor → POST /track → MongoDB + Amplitude → AI Worker
2. **AI Analysis**: Background worker processes events → Calls appropriate LLM via Backboard → Updates radar profile
3. **Video Pipeline**: Upload → TwelveLabs indexing → Semantic search + highlights extraction
4. **Real-time Updates**: Frontend polls /radar/{userId} for profile updates and interventions

### Database Collections

- **users**: User accounts with radar_profile (Engineering DNA scores)
- **sessions**: Coding session data with AI intervention context
- **events**: Granular behavioral events (code changes, runs, errors)
- **tasks**: Coding challenges with difficulty and test cases
- **jobs**: Job listings with target radar profiles for matching
- **passports**: Skill passports with evidence and video insights
- **interventions**: AI-generated hints and their effectiveness metrics
- **videos**: Interview recordings with TwelveLabs analysis

## Sponsor Track Integrations

### Amplitude Integration (Detailed)

SkillPulse implements a comprehensive Amplitude integration demonstrating the **self-improving product loop**: behavioral data → AI insights → product adaptation.

#### Event Schema (12+ Event Types)

| Event Type | Description | Key Properties |
|------------|-------------|----------------|
| `code_changed` | User modifies code in editor | `lines_changed`, `chars_added`, `chars_pasted` |
| `test_cases_ran` | Code executed against tests | `tests_passed`, `tests_total`, `runtime_ms`, `result` |
| `task_submitted` | Final solution submitted | `passed`, `score`, `tests_passed`, `tests_total` |
| `error_emitted` | Runtime error occurred | `error_type`, `stack_depth`, `is_repeat` |
| `fix_applied` | Error fix applied | `time_since_error`, `fix_type` |
| `contextual_hint_shown` | AI hint displayed | `hint_type`, `trigger_reason` |
| `hint_acknowledged` | User clicked/dismissed hint | `hint_id`, `time_to_acknowledge` |
| `chat_help_requested` | User asked chat assistant | `message_length`, `has_code_context`, `has_error_context` |
| `chat_help_response_received` | Chat response sent | `response_length` |
| `proctoring_violation` | Integrity violation detected | `violation_type`, `severity` |
| `paste_burst_detected` | Large paste detected | `chars_pasted` |
| `tab_switch` | User switched browser tabs | `duration_away_ms` |
| `editor_command` | Editor shortcut/command used | `command`, `source` (shortcut vs menu) |

#### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVENT INGESTION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Monaco Editor  →  POST /track  →  MongoDB  →  Background Task              │
│                                      │              │                        │
│                                      ▼              ▼                        │
│                              Store event     forward_to_amplitude()          │
│                              with metadata   (async, non-blocking)           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI ANALYSIS TRIGGER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  For events: run_attempted, error_emitted, code_changed                     │
│                                      │                                       │
│                                      ▼                                       │
│                          trigger_analysis()                                  │
│                                      │                                       │
│              ┌───────────────────────┴───────────────────────┐              │
│              ▼                                               ▼              │
│     Frustration Detection                          Radar Profile Update      │
│     (error_streak >= 3 OR                         (incremental score        │
│      time_stuck >= 180s)                           adjustments)              │
│              │                                                               │
│              ▼                                                               │
│     Backboard AI Intervention                                                │
│     (multi-model hint generation)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PASSPORT & USER PROPERTIES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  On task_submitted:                                                          │
│                                      │                                       │
│              ┌───────────────────────┼───────────────────────┐              │
│              ▼                       ▼                       ▼              │
│     compute_skill_vector()    assign_archetype()    update_amplitude_       │
│     [5 dimensions]            (rule-based)          user_properties()        │
│                                                                              │
│  Synced to Amplitude:                                                        │
│    • skill_archetype (fast_iterator, careful_tester, debugger, etc.)        │
│    • skill_vector [iteration_velocity, debug_efficiency, craftsmanship,     │
│                    tool_fluency, integrity]                                  │
│    • integrity_score                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Amplitude Service Functions (`services/amplitude.py`)

| Function | Purpose | Amplitude API |
|----------|---------|---------------|
| `forward_to_amplitude()` | Forward events async | `POST /2/httpapi` |
| `update_amplitude_user_properties()` | Sync user profile | `POST /2/httpapi` ($identify) |
| `fetch_event_segmentation()` | Query event analytics | `GET /api/2/events/segmentation` |
| `fetch_user_activity()` | Get user activity summary | `GET /api/2/useractivity` |
| `fetch_user_event_counts()` | Local MongoDB counts (fast) | N/A (local) |
| `get_passport_analytics()` | Comprehensive user metrics | Hybrid (local + Amplitude) |

#### The Self-Improving Loop

```
DATA (Behavioral Events)
    │
    ├── code_changed, test_cases_ran, error_emitted, fix_applied
    ├── contextual_hint_shown, hint_acknowledged
    ├── chat_help_requested, proctoring_violation
    │
    ▼
INSIGHTS (AI Analysis)
    │
    ├── Frustration Detection: pattern analysis on error streaks, time stuck
    ├── Skill Vector Computation: 5-dimension profile from event aggregation
    ├── Archetype Assignment: fast_iterator, careful_tester, debugger, craftsman, explorer
    ├── Error Profile: user's common error patterns for personalized hints
    │
    ▼
ACTION (Product Adaptation)
    │
    ├── Contextual Hints: AI-generated, personalized to error history
    ├── Task Recommendations: based on weak areas in radar profile
    ├── Recruiter Matching: job fit scoring using skill vectors
    ├── Passport Updates: real-time Engineering DNA visualization
```

#### Key Files

| File | Role |
|------|------|
| `apps/api/services/amplitude.py` | Core Amplitude service (forwarding, user properties, queries) |
| `apps/api/routes/track.py` | Event ingestion endpoints (`POST /track`, `POST /track/batch`) |
| `apps/api/routes/analytics.py` | Analytics query endpoints (passport, metrics breakdown) |
| `apps/api/services/skillgraph.py` | Skill vector computation, archetype assignment, Amplitude sync |
| `apps/api/services/ai_worker.py` | AI analysis trigger, frustration detection, radar updates |
| `apps/api/routes/tasks.py` | Task execution with `test_cases_ran`, `task_submitted` events |
| `apps/api/routes/chat.py` | Chat help with `chat_help_requested` events |

#### Analytics Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /analytics/passport` | User's comprehensive analytics (event counts, session stats, AI metrics) |
| `GET /analytics/passport/{user_id}` | Recruiter view of candidate analytics |
| `GET /analytics/events/counts` | Event count summary for current user |
| `GET /analytics/metrics/breakdown` | Detailed explanation of how each metric was calculated |
| `GET /analytics/amplitude/segmentation` | Direct Amplitude Data API queries |

#### Why This Qualifies for the Amplitude Sponsor Track

1. **Behavioral Data & Analytics**: 12+ semantic event types with rich properties, clear event schema, user journey modeling (session → attempts → errors → fixes → success)

2. **AI Application**: Frustration detection via pattern analysis (not just if/else), multi-model AI routing via Backboard, personalized hints based on error history, skill vector computation from behavioral aggregation

3. **Product Impact**: Real-time Engineering DNA radar charts, adaptive AI hints when struggling, recruiter job matching via skill vectors, comprehensive skill passport

4. **Self-Improving Loop**: Events drive AI insights → insights drive personalization → personalization improves experience → more events captured

### TwelveLabs Integration
- Interview video indexing with Marengo 3.0
- Semantic search within videos
- Auto-generated highlights and summaries
- Communication style analysis

### Backboard.io Integration
- Multi-model AI routing (4 different LLMs for different tasks)
- Adaptive memory per user (remembers past hints)
- Intelligent model selection based on task type

## Key API Endpoints

### Core Endpoints
- `POST /track` - Ingest behavioral events
- `GET /radar/{user_id}` - Get Engineering DNA profile with interventions
- `POST /tasks/{task_id}/run` - Execute code in sandbox
- `GET /jobs` - Get matched jobs based on radar profile

### Video Endpoints
- `POST /video/upload` - Submit interview video for analysis
- `GET /video/{video_id}/search` - Semantic search within video
- `GET /video/{video_id}/summary` - Get AI-generated summary

### Recruiter Endpoints
- `GET /recruiter/candidates` - Browse candidates with filters
- `GET /recruiter/candidates/{user_id}/passport` - View full skill passport
- `POST /recruiter/jobs` - Create job with target radar profile

## AI Worker Logic

The AI Worker (`services/ai_worker.py`) implements:
1. **Frustration Detection**: Analyzes event patterns for error streaks and time stuck
2. **Adaptive Intervention**: Uses Backboard to route to appropriate AI model
3. **Radar Profile Updates**: Incrementally updates Engineering DNA scores
4. **Hint Generation**: Context-aware hints that remember past interventions

## Important Implementation Notes

- The project extends an existing "Proof of Skill" codebase with AI-powered features
- MongoDB is used with Motor for async operations
- All AI calls go through Backboard.io for unified access and memory
- TwelveLabs video processing is asynchronous with polling for completion
- Frontend uses SWR for data fetching with automatic revalidation
- Sandbox runner provides secure code execution with resource limits

## Environment Variables

Critical environment variables (store in 1Password):
- `MONGODB_URI` - MongoDB Atlas connection string
- `AMPLITUDE_API_KEY` - For event forwarding
- `TWELVELABS_API_KEY` - For video analysis
- `BACKBOARD_API_KEY` - For multi-model AI (use code UOFTHACKS26)
- `JWT_SECRET` - For authentication
- `SANDBOX_RUNNER_URL` - Internal sandbox service URL

## Development Workflow

1. Changes to behavioral events should update both the tracking code and AI analysis
2. New radar dimensions require updates to: user model, AI worker, frontend visualization
3. Video features require TwelveLabs index setup before use
4. All AI hints should go through Backboard for memory persistence
5. Test with seed data before real user testing