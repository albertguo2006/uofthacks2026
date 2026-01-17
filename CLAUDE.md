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

### Amplitude Integration
- Semantic event tracking (12+ event types)
- Real-time user property updates
- Cohort analysis by archetype
- Self-improving loop: Data → AI Insights → Product Changes

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