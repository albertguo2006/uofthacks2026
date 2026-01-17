# Proof of Skill — Implementation Plan

> **Identity-First Freelance Marketplace**
> UofTHacks 2026 | Team Implementation Guide

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [Directory Structure](#directory-structure)
5. [Database Schema](#database-schema)
6. [API Specification](#api-specification)
7. [Event Schema](#event-schema)
8. [Implementation Phases](#implementation-phases)
9. [Sponsor Track Integration](#sponsor-track-integration)
10. [Security Considerations](#security-considerations)
11. [Demo Script](#demo-script)

---

## Executive Summary

**Proof of Skill** is a freelance marketplace where professional identity is proven through behavior, not self-reported resumes. Candidates complete coding tasks in a sandboxed environment while the system captures behavioral signals. Machine learning builds a "Skill Identity Vector" that unlocks jobs in real-time as competency is demonstrated.

### Core Value Proposition

| Stakeholder | Problem | Solution |
|-------------|---------|----------|
| **Candidates** | Resumes don't reflect true ability | Build verifiable skill identity through work |
| **Recruiters** | Can't trust self-reported skills | Evidence-backed passports with behavioral proof |
| **Platform** | Skill fraud is rampant | Anti-cheat signals + transparent identity |

### Scope Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Build scope | Demo-focused | Core flow: sandbox → events → job reveal |
| Task types | Code only | Monaco editor, no design canvas |
| Real-time updates | Polling | Simple, reliable for demo |
| Authentication | JWT + Passkey | 1Password sponsor track bonus |
| Code execution | Docker sandbox | Real execution, impressive demo |
| Database | MongoDB Atlas | MLH sponsor track + cloud-native |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      Next.js 14 Web App                             │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │
│   │  │   Candidate  │  │   Recruiter  │  │     Auth Pages           │   │   │
│   │  │  Dashboard   │  │  Dashboard   │  │  (Login/Register/Passkey)│   │   │
│   │  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘   │   │
│   │         │                 │                       │                 │   │
│   │  ┌──────▼───────┐  ┌──────▼───────┐               │                 │   │
│   │  │   Sandbox    │  │   Passport   │               │                 │   │
│   │  │ Monaco Editor│  │    Viewer    │               │                 │   │
│   │  └──────┬───────┘  └──────────────┘               │                 │   │
│   │         │                                         │                 │   │
│   │         ▼ telemetry events                        │                 │   │
│   └─────────┼─────────────────────────────────────────┼─────────────────┘   │
│             │                                         │                     │
└─────────────┼─────────────────────────────────────────┼─────────────────────┘
              │ POST /track                             │ POST /auth/*
              ▼                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        FastAPI Backend                              │   │
│   │                                                                     │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐   │   │
│   │  │   /track    │  │   /jobs     │  │  /passport  │  │   /auth   │   │   │
│   │  │   Events    │  │  Matching   │  │   Identity  │  │  JWT/Pass │   │   │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───────────┘   │   │
│   │         │                │                │                         │   │
│   │         ▼                ▼                ▼                         │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │                    Services Layer                           │    │   │
│   │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────┐  │    │   │
│   │  │  │ Amplitude │ │SkillGraph │ │TwelveLabs │ │  Sandbox    │  │    │   │
│   │  │  │ Forwarder │ │    ML     │ │   Video   │ │  Executor   │  │    │   │
│   │  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └──────┬──────┘  │    │   │
│   │  └────────┼─────────────┼─────────────┼──────────────┼─────────┘    │   │
│   └───────────┼─────────────┼─────────────┼──────────────┼──────────────┘   │
│               │             │             │              │                  │
└───────────────┼─────────────┼─────────────┼──────────────┼──────────────────┘
                │             │             │              │
                ▼             │             ▼              ▼
┌───────────────────────┐     │  ┌─────────────────┐  ┌─────────────────────┐
│      Amplitude        │     │  │   TwelveLabs    │  │   Sandbox Runner    │
│   (Analytics SaaS)    │     │  │   (Video SaaS)  │  │  (Docker Container) │
└───────────────────────┘     │  └─────────────────┘  └─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                       MongoDB Atlas                                 │   │
│   │                                                                     │   │
│   │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────┐     │   │
│   │  │   users   │  │  events   │  │   tasks   │  │     jobs      │     │   │
│   │  └───────────┘  └───────────┘  └───────────┘  └───────────────┘     │   │
│   │                                                                     │   │
│   │  ┌───────────┐  ┌───────────┐  ┌───────────┐                        │   │
│   │  │ sessions  │  │ passports │  │  videos   │                        │   │
│   │  └───────────┘  └───────────┘  └───────────┘                        │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Candidate works** → Monaco editor captures commands, runs, errors
2. **Events stream** → POST /track → stored in MongoDB + forwarded to Amplitude
3. **SkillGraph computes** → Feature extraction → clustering → job fit
4. **Passport updates** → Archetype assigned, skill vector computed
5. **Jobs unlock** → Polling fetches /jobs, new jobs appear when fit threshold crossed
6. **Recruiter reviews** → Views passport evidence + video highlights

---

## Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.x | React framework with App Router |
| TypeScript | 5.x | Type safety |
| Monaco Editor | Latest | Code editing (VS Code engine) |
| TailwindCSS | 3.x | Styling |
| SWR or React Query | Latest | Data fetching + polling |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Backend runtime |
| FastAPI | 0.100+ | API framework |
| Motor | Latest | Async MongoDB driver |
| Pydantic | 2.x | Data validation |
| PyJWT | Latest | JWT authentication |
| py_webauthn | Latest | Passkey/WebAuthn |
| scikit-learn | Latest | ML (KMeans, LogReg) |
| Docker | Latest | Sandbox isolation |

### External Services

| Service | Purpose | Sponsor Track |
|---------|---------|---------------|
| MongoDB Atlas | Primary database | MLH |
| Amplitude | Event analytics | Yes |
| TwelveLabs | Video understanding | Yes |
| 1Password | Secrets + passkey | Yes |

### DevOps

| Tool | Purpose |
|------|---------|
| Docker Compose | Local orchestration |
| 1Password CLI | Secret injection |

---

## Directory Structure

```
proof-of-skill/
│
├── apps/
│   │
│   ├── web/                              # Next.js 14 Frontend
│   │   ├── src/
│   │   │   ├── app/                      # App Router pages
│   │   │   │   ├── page.tsx              # Landing page
│   │   │   │   ├── layout.tsx            # Root layout + providers
│   │   │   │   ├── globals.css           # Global styles
│   │   │   │   │
│   │   │   │   ├── auth/
│   │   │   │   │   ├── login/
│   │   │   │   │   │   └── page.tsx      # Login page
│   │   │   │   │   └── register/
│   │   │   │   │       └── page.tsx      # Registration page
│   │   │   │   │
│   │   │   │   ├── candidate/
│   │   │   │   │   ├── page.tsx          # Candidate dashboard
│   │   │   │   │   ├── layout.tsx        # Candidate layout
│   │   │   │   │   ├── tasks/
│   │   │   │   │   │   ├── page.tsx      # Task listing
│   │   │   │   │   │   └── [taskId]/
│   │   │   │   │   │       └── page.tsx  # Sandbox environment
│   │   │   │   │   ├── passport/
│   │   │   │   │   │   └── page.tsx      # View own passport
│   │   │   │   │   └── jobs/
│   │   │   │   │       └── page.tsx      # Job feed
│   │   │   │   │
│   │   │   │   └── recruiter/
│   │   │   │       ├── page.tsx          # Recruiter dashboard
│   │   │   │       ├── layout.tsx        # Recruiter layout
│   │   │   │       ├── candidates/
│   │   │   │       │   ├── page.tsx      # Browse candidates
│   │   │   │       │   └── [id]/
│   │   │   │       │       └── page.tsx  # View candidate passport
│   │   │   │       └── security/
│   │   │   │           └── page.tsx      # Security transparency
│   │   │   │
│   │   │   ├── components/
│   │   │   │   ├── sandbox/
│   │   │   │   │   ├── CodeEditor.tsx    # Monaco wrapper
│   │   │   │   │   ├── OutputPanel.tsx   # Execution results
│   │   │   │   │   ├── TaskHeader.tsx    # Task info display
│   │   │   │   │   └── RunButton.tsx     # Execute code
│   │   │   │   │
│   │   │   │   ├── passport/
│   │   │   │   │   ├── SkillPassport.tsx # Full passport view
│   │   │   │   │   ├── ArchetypeBadge.tsx# Archetype display
│   │   │   │   │   ├── SkillVector.tsx   # Radar/bar chart
│   │   │   │   │   └── EvidenceList.tsx  # Event highlights
│   │   │   │   │
│   │   │   │   ├── jobs/
│   │   │   │   │   ├── JobFeed.tsx       # Job list + polling
│   │   │   │   │   ├── JobCard.tsx       # Individual job
│   │   │   │   │   └── UnlockAnimation.tsx# New job reveal
│   │   │   │   │
│   │   │   │   ├── video/
│   │   │   │   │   ├── InterviewUploader.tsx
│   │   │   │   │   ├── VideoPlayer.tsx
│   │   │   │   │   └── HighlightsList.tsx
│   │   │   │   │
│   │   │   │   ├── auth/
│   │   │   │   │   ├── LoginForm.tsx
│   │   │   │   │   ├── RegisterForm.tsx
│   │   │   │   │   ├── PasskeyButton.tsx # WebAuthn trigger
│   │   │   │   │   └── ProtectedRoute.tsx
│   │   │   │   │
│   │   │   │   └── ui/                   # Shared UI primitives
│   │   │   │       ├── Button.tsx
│   │   │   │       ├── Card.tsx
│   │   │   │       ├── Input.tsx
│   │   │   │       ├── Modal.tsx
│   │   │   │       ├── Spinner.tsx
│   │   │   │       └── Toast.tsx
│   │   │   │
│   │   │   ├── lib/
│   │   │   │   ├── api.ts                # API client (fetch wrapper)
│   │   │   │   ├── auth.ts               # Auth utilities
│   │   │   │   ├── telemetry.ts          # Event tracking client
│   │   │   │   └── constants.ts          # App constants
│   │   │   │
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.ts            # Auth state hook
│   │   │   │   ├── useJobFeed.ts         # Polling hook for jobs
│   │   │   │   ├── usePassport.ts        # Fetch passport data
│   │   │   │   ├── useTasks.ts           # Task listing
│   │   │   │   └── useCodeExecution.ts   # Run code hook
│   │   │   │
│   │   │   └── types/
│   │   │       ├── user.ts
│   │   │       ├── task.ts
│   │   │       ├── job.ts
│   │   │       ├── passport.ts
│   │   │       └── event.ts
│   │   │
│   │   ├── public/
│   │   │   └── favicon.ico
│   │   │
│   │   ├── package.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   └── .env.local.example
│   │
│   ├── api/                              # FastAPI Backend
│   │   ├── main.py                       # App entry, CORS, routers
│   │   ├── config.py                     # Settings from env
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                   # POST /auth/register, /auth/login
│   │   │   ├── passkey.py                # POST /auth/passkey/*
│   │   │   ├── track.py                  # POST /track
│   │   │   ├── tasks.py                  # GET /tasks, POST /tasks/{id}/run
│   │   │   ├── jobs.py                   # GET /jobs
│   │   │   ├── passport.py               # GET /passport/{user_id}
│   │   │   └── video.py                  # POST /video/upload, GET /video/search
│   │   │
│   │   ├── models/                       # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py                   # User, UserCreate, UserInDB
│   │   │   ├── auth.py                   # Token, LoginRequest
│   │   │   ├── event.py                  # TrackEvent, EventProperties
│   │   │   ├── task.py                   # Task, TaskSubmission, RunResult
│   │   │   ├── job.py                    # Job, JobMatch
│   │   │   ├── passport.py               # SkillPassport, Archetype
│   │   │   └── video.py                  # VideoUpload, Highlight
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── amplitude.py              # Forward events to Amplitude
│   │   │   ├── skillgraph.py             # ML pipeline
│   │   │   ├── twelvelabs.py             # Video analysis
│   │   │   ├── webauthn.py               # Passkey registration/auth
│   │   │   └── sandbox.py                # Docker execution client
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── mongo.py                  # MongoDB connection
│   │   │   └── collections.py            # Collection references
│   │   │
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── auth.py                   # JWT verification
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── security.py               # Password hashing
│   │   │   └── jwt.py                    # Token creation/verification
│   │   │
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   │
│   └── sandbox-runner/                   # Isolated Code Execution
│       ├── Dockerfile                    # Minimal, locked-down image
│       ├── runner.py                     # Main execution script
│       ├── server.py                     # HTTP API for execution
│       │
│       ├── languages/
│       │   ├── __init__.py
│       │   ├── base.py                   # Abstract runner
│       │   ├── python_runner.py          # Python execution
│       │   ├── javascript_runner.py      # Node.js execution
│       │   └── typescript_runner.py      # TS execution (via tsx)
│       │
│       ├── requirements.txt
│       └── package.json                  # For JS/TS execution
│
├── packages/                             # Shared code (optional)
│   └── skillgraph/                       # ML models (can be in api/services)
│       ├── __init__.py
│       ├── features.py                   # Feature extraction
│       ├── clustering.py                 # KMeans archetypes
│       ├── matching.py                   # Job fit scoring
│       └── models/                       # Serialized models
│           └── kmeans.pkl
│
├── data/                                 # Seed data
│   ├── jobs.json                         # Job definitions
│   ├── archetypes.json                   # Archetype descriptions
│   └── tasks/
│       ├── bugfix-null-check.json
│       ├── refactor-extract-function.json
│       ├── implement-debounce.json
│       ├── fix-async-race.json
│       └── add-input-validation.json
│
├── scripts/
│   ├── seed_demo_data.py                 # Seed MongoDB with demo data
│   ├── seed_tasks.py                     # Load tasks into DB
│   ├── train_models.py                   # Train/export ML models
│   └── generate_events.py                # Generate synthetic events
│
├── docker-compose.yml                    # Full stack orchestration
├── docker-compose.dev.yml                # Development overrides
├── prod.env.example                      # 1Password secret references
├── .gitignore
├── IMPLEMENTATION_PLAN.md                # This document
└── README.md                             # Project overview
```

---

## Database Schema

### MongoDB Collections

#### `users`

```javascript
{
  _id: ObjectId,
  email: String,                    // unique
  password_hash: String,            // bcrypt
  role: "candidate" | "recruiter",
  created_at: ISODate,

  // WebAuthn (optional)
  passkey_credentials: [{
    credential_id: Binary,
    public_key: Binary,
    sign_count: Number,
    created_at: ISODate
  }],

  // Candidate-specific
  skill_vector: [Number],           // computed by SkillGraph
  archetype: String,                // "fast_iterator", "careful_tester", etc.
  integrity_score: Number,          // 0-1

  // Metadata
  display_name: String,
  avatar_url: String
}
```

#### `events`

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  session_id: String,               // UUID per sandbox session
  task_id: String,
  event_type: String,               // "editor_command", "run_attempted", etc.
  timestamp: ISODate,

  properties: {
    // Varies by event_type
    command: String,
    source: "shortcut" | "menu",
    result: "pass" | "fail",
    error_type: String,
    // ... etc
  },

  // Tracking
  forwarded_to_amplitude: Boolean,
  processed_for_ml: Boolean
}
```

#### `sessions`

```javascript
{
  _id: ObjectId,
  session_id: String,               // UUID
  user_id: ObjectId,
  task_id: String,
  started_at: ISODate,
  ended_at: ISODate,

  // Computed per-session
  feature_vector: [Number],

  // Outcomes
  submitted: Boolean,
  passed: Boolean,
  score: Number
}
```

#### `tasks`

```javascript
{
  _id: ObjectId,
  task_id: String,                  // "bugfix-null-check"
  title: String,
  description: String,              // Markdown
  difficulty: "easy" | "medium" | "hard",
  category: "bugfix" | "refactor" | "feature" | "optimization",
  language: "python" | "javascript" | "typescript",

  starter_code: String,
  solution_code: String,            // For validation

  test_cases: [{
    input: Any,
    expected_output: Any,
    hidden: Boolean                 // Hidden from candidate
  }],

  time_limit_seconds: Number,
  created_at: ISODate
}
```

#### `jobs`

```javascript
{
  _id: ObjectId,
  job_id: String,
  title: String,
  description: String,
  company: String,
  tier: 0 | 1 | 2,                  // Hidden tiers

  // Matching
  target_vector: [Number],          // Ideal skill vector
  min_fit: Number,                  // Threshold to unlock (0-1)
  must_have: {
    min_integrity: Number,
    min_sessions: Number,
    required_archetypes: [String]
  },

  // Display
  salary_range: String,
  location: String,
  tags: [String],

  created_at: ISODate
}
```

#### `passports`

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,                // unique

  // Identity
  archetype: String,
  archetype_confidence: Number,
  skill_vector: [Number],

  // Computed metrics
  metrics: {
    iteration_velocity: Number,
    debug_efficiency: Number,
    craftsmanship: Number,
    tool_fluency: Number,
    integrity: Number
  },

  // Evidence
  notable_sessions: [{
    session_id: String,
    task_id: String,
    highlight: String,              // "Fixed 5 errors in 2 minutes"
    timestamp: ISODate
  }],

  // Video (if uploaded)
  interview_video_id: String,
  interview_highlights: [{
    timestamp_start: Number,
    timestamp_end: Number,
    description: String,
    query_matched: String
  }],

  updated_at: ISODate
}
```

#### `videos`

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,

  // TwelveLabs
  twelvelabs_index_id: String,
  twelvelabs_video_id: String,
  twelvelabs_task_id: String,

  status: "uploading" | "indexing" | "ready" | "failed",

  // Metadata
  filename: String,
  duration_seconds: Number,
  uploaded_at: ISODate,
  ready_at: ISODate
}
```

### Indexes

```javascript
// users
db.users.createIndex({ email: 1 }, { unique: true })

// events
db.events.createIndex({ user_id: 1, timestamp: -1 })
db.events.createIndex({ session_id: 1 })
db.events.createIndex({ forwarded_to_amplitude: 1 })

// sessions
db.sessions.createIndex({ user_id: 1 })
db.sessions.createIndex({ session_id: 1 }, { unique: true })

// passports
db.passports.createIndex({ user_id: 1 }, { unique: true })
```

---

## API Specification

### Authentication

#### `POST /auth/register`

Create a new user account.

**Request:**
```json
{
  "email": "candidate@example.com",
  "password": "securepassword123",
  "role": "candidate",
  "display_name": "Jane Developer"
}
```

**Response:** `201 Created`
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "email": "candidate@example.com",
  "role": "candidate",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### `POST /auth/login`

Authenticate with email/password.

**Request:**
```json
{
  "email": "candidate@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "user_id": "507f1f77bcf86cd799439011",
    "email": "candidate@example.com",
    "role": "candidate"
  }
}
```

#### `POST /auth/passkey/register/begin`

Start passkey registration (WebAuthn).

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "options": {
    "challenge": "base64-encoded-challenge",
    "rp": { "name": "Proof of Skill", "id": "localhost" },
    "user": { "id": "...", "name": "...", "displayName": "..." },
    "pubKeyCredParams": [...],
    "timeout": 60000,
    "attestation": "none"
  }
}
```

#### `POST /auth/passkey/register/complete`

Complete passkey registration.

**Request:**
```json
{
  "credential": {
    "id": "credential-id",
    "rawId": "base64",
    "response": {
      "clientDataJSON": "base64",
      "attestationObject": "base64"
    },
    "type": "public-key"
  }
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "credential_id": "credential-id"
}
```

#### `POST /auth/passkey/authenticate/begin`

Start passkey authentication.

**Request:**
```json
{
  "email": "candidate@example.com"
}
```

**Response:** `200 OK`
```json
{
  "options": {
    "challenge": "base64-encoded-challenge",
    "timeout": 60000,
    "rpId": "localhost",
    "allowCredentials": [...]
  }
}
```

#### `POST /auth/passkey/authenticate/complete`

Complete passkey authentication.

**Request:**
```json
{
  "email": "candidate@example.com",
  "credential": {
    "id": "credential-id",
    "rawId": "base64",
    "response": {
      "clientDataJSON": "base64",
      "authenticatorData": "base64",
      "signature": "base64"
    },
    "type": "public-key"
  }
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

### Events (Telemetry)

#### `POST /track`

Ingest behavioral event.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "event_type": "editor_command",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "bugfix-null-check",
  "timestamp": 1705420800000,
  "properties": {
    "command": "format_document",
    "source": "shortcut"
  }
}
```

**Response:** `202 Accepted`
```json
{
  "event_id": "507f1f77bcf86cd799439012",
  "forwarded_to_amplitude": true
}
```

---

### Tasks

#### `GET /tasks`

List available tasks.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "tasks": [
    {
      "task_id": "bugfix-null-check",
      "title": "Fix Null Reference Bug",
      "description": "A function crashes when given null input...",
      "difficulty": "easy",
      "category": "bugfix",
      "language": "javascript",
      "estimated_minutes": 10
    }
  ]
}
```

#### `GET /tasks/{task_id}`

Get task details with starter code.

**Response:** `200 OK`
```json
{
  "task_id": "bugfix-null-check",
  "title": "Fix Null Reference Bug",
  "description": "# Problem\n\nThe `processUser` function crashes...",
  "difficulty": "easy",
  "category": "bugfix",
  "language": "javascript",
  "starter_code": "function processUser(user) {\n  return user.name.toUpperCase();\n}",
  "test_cases": [
    { "input": {"name": "Alice"}, "expected_output": "ALICE" },
    { "input": null, "expected_output": null }
  ],
  "time_limit_seconds": 5
}
```

#### `POST /tasks/{task_id}/run`

Execute code in sandbox.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "function processUser(user) {\n  if (!user) return null;\n  return user.name.toUpperCase();\n}",
  "language": "javascript"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "results": [
    { "test_case": 1, "passed": true, "output": "ALICE", "time_ms": 12 },
    { "test_case": 2, "passed": true, "output": null, "time_ms": 8 }
  ],
  "all_passed": true,
  "total_time_ms": 20,
  "stdout": "",
  "stderr": ""
}
```

#### `POST /tasks/{task_id}/submit`

Submit final solution.

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "..."
}
```

**Response:** `200 OK`
```json
{
  "submitted": true,
  "passed": true,
  "score": 95,
  "passport_updated": true,
  "new_archetype": "careful_tester",
  "jobs_unlocked": 2
}
```

---

### Jobs

#### `GET /jobs`

Get jobs matching user's skill vector.

**Headers:** `Authorization: Bearer <token>`

**Query params:**
- `include_locked=true` (optional, for UI to show locked jobs)

**Response:** `200 OK`
```json
{
  "jobs": [
    {
      "job_id": "tier1-landing-page",
      "title": "Build a Marketing Landing Page",
      "company": "TechStartup Inc",
      "tier": 1,
      "fit_score": 0.78,
      "unlocked": true,
      "salary_range": "$60-80k",
      "tags": ["react", "frontend", "remote"]
    },
    {
      "job_id": "tier2-refactor-billing",
      "title": "Refactor Billing Service",
      "company": "FinanceApp Co",
      "tier": 2,
      "fit_score": 0.65,
      "unlocked": false,
      "unlock_requirements": {
        "min_fit": 0.72,
        "missing": ["higher debug efficiency"]
      }
    }
  ],
  "user_skill_vector": [0.7, 0.6, 0.1],
  "last_updated": "2024-01-16T12:00:00Z"
}
```

---

### Passport

#### `GET /passport/{user_id}`

Get user's skill passport.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "display_name": "Jane Developer",

  "archetype": {
    "name": "careful_tester",
    "label": "Careful Tester",
    "description": "Prioritizes test coverage and validation before shipping",
    "confidence": 0.85
  },

  "skill_vector": [0.7, 0.8, 0.1],

  "metrics": {
    "iteration_velocity": 0.65,
    "debug_efficiency": 0.82,
    "craftsmanship": 0.71,
    "tool_fluency": 0.58,
    "integrity": 0.95
  },

  "sessions_completed": 12,
  "tasks_passed": 10,

  "notable_moments": [
    {
      "type": "achievement",
      "description": "Fixed 5 consecutive errors without re-running",
      "session_id": "...",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],

  "interview": {
    "has_video": true,
    "highlights": [
      {
        "timestamp": "02:34",
        "description": "Explained testing philosophy",
        "query": "testing approach"
      }
    ]
  },

  "updated_at": "2024-01-16T12:00:00Z"
}
```

---

### Video

#### `POST /video/upload`

Upload interview video for processing.

**Headers:** `Authorization: Bearer <token>`

**Request:** `multipart/form-data`
- `file`: Video file (mp4, webm)

**Response:** `202 Accepted`
```json
{
  "video_id": "507f1f77bcf86cd799439013",
  "status": "uploading",
  "twelvelabs_task_id": "task_abc123"
}
```

#### `GET /video/{video_id}/status`

Check video processing status.

**Response:** `200 OK`
```json
{
  "video_id": "507f1f77bcf86cd799439013",
  "status": "ready",
  "duration_seconds": 180,
  "ready_at": "2024-01-16T12:05:00Z"
}
```

#### `GET /video/{video_id}/search`

Search video for specific moments.

**Query params:**
- `q`: Search query (e.g., "testing strategy")

**Response:** `200 OK`
```json
{
  "results": [
    {
      "start_time": 154.2,
      "end_time": 168.5,
      "confidence": 0.89,
      "transcript_snippet": "...I always write tests first because..."
    }
  ]
}
```

---

## Event Schema

### Event Types

| Event | Trigger | Key Properties |
|-------|---------|----------------|
| `session_started` | Sandbox opened | `task_id`, `difficulty` |
| `editor_command` | Any editor action | `command`, `source` |
| `code_changed` | Debounced edit | `lines_changed`, `chars_added` |
| `run_attempted` | Click run | `result`, `runtime_ms`, `tests_passed` |
| `error_emitted` | Runtime error | `error_type`, `stack_depth`, `is_repeat` |
| `fix_applied` | Code change after error | `from_error_type`, `time_since_error_ms` |
| `refactor_applied` | Detected refactor | `kind`, `loc_changed` |
| `test_added` | New test detected | `count`, `scope` |
| `paste_burst_detected` | Large paste | `chars_pasted`, `burst_ms` |
| `task_submitted` | Final submission | `passed`, `score` |
| `session_ended` | Sandbox closed | `duration_ms`, `outcome` |

### Event Structure

```typescript
interface TrackEvent {
  event_type: string;
  user_id: string;           // From JWT
  session_id: string;        // UUID per sandbox session
  task_id: string;
  timestamp: number;         // Unix ms
  properties: Record<string, any>;
}
```

### Amplitude Mapping

Events are forwarded to Amplitude with this transformation:

```python
amplitude_event = {
    "user_id": event.user_id,
    "event_type": event.event_type,
    "time": event.timestamp,
    "event_properties": {
        **event.properties,
        "session_id": event.session_id,
        "task_id": event.task_id
    },
    "user_properties": {
        # Updated after passport computation
        "$set": {
            "skill_archetype": passport.archetype,
            "skill_vector": passport.skill_vector,
            "integrity_score": passport.metrics.integrity
        }
    }
}
```

---

## Implementation Phases

### Phase 1: Foundation & Infrastructure (Day 1 Morning)

**Goal:** Project scaffolding and basic connectivity.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 1.1 | Initialize Next.js 14 project with App Router | Frontend | 30m |
| 1.2 | Initialize FastAPI project structure | Backend | 30m |
| 1.3 | Create MongoDB Atlas cluster | Backend | 15m |
| 1.4 | Implement MongoDB connection (motor) | Backend | 30m |
| 1.5 | Create Docker Compose for local dev | DevOps | 30m |
| 1.6 | Set up 1Password secret references | DevOps | 20m |
| 1.7 | Create basic health endpoints | Backend | 15m |
| 1.8 | Verify full stack connectivity | All | 15m |

**Deliverable:** `docker-compose up` runs Next.js + FastAPI + connects to MongoDB Atlas.

---

### Phase 2: Authentication System (Day 1 Morning/Afternoon)

**Goal:** Users can register, login, and use passkeys.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 2.1 | Create User model (Pydantic + MongoDB) | Backend | 20m |
| 2.2 | Implement password hashing (bcrypt) | Backend | 15m |
| 2.3 | Implement JWT creation/verification | Backend | 30m |
| 2.4 | Create `/auth/register` endpoint | Backend | 30m |
| 2.5 | Create `/auth/login` endpoint | Backend | 20m |
| 2.6 | Create auth middleware | Backend | 20m |
| 2.7 | Implement WebAuthn registration (py_webauthn) | Backend | 45m |
| 2.8 | Implement WebAuthn authentication | Backend | 45m |
| 2.9 | Create Login/Register pages (Next.js) | Frontend | 45m |
| 2.10 | Create PasskeyButton component | Frontend | 30m |
| 2.11 | Create useAuth hook | Frontend | 20m |
| 2.12 | Add ProtectedRoute component | Frontend | 20m |

**Deliverable:** Full auth flow works including passkey registration/login.

---

### Phase 3: Sandbox Runner Service (Day 1 Afternoon)

**Goal:** Securely execute user code in Docker containers.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 3.1 | Create sandbox-runner Dockerfile | Backend | 30m |
| 3.2 | Implement base runner interface | Backend | 20m |
| 3.3 | Implement Python runner | Backend | 30m |
| 3.4 | Implement JavaScript runner | Backend | 30m |
| 3.5 | Add resource limits (CPU, memory, time) | Backend | 30m |
| 3.6 | Add network isolation | Backend | 20m |
| 3.7 | Create HTTP API for sandbox | Backend | 30m |
| 3.8 | Integrate sandbox with FastAPI | Backend | 30m |
| 3.9 | Add to docker-compose | DevOps | 15m |

**Deliverable:** API can execute arbitrary Python/JS code safely with timeout.

---

### Phase 4: Task System (Day 1 Evening)

**Goal:** Tasks are stored in MongoDB, retrievable, and executable.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 4.1 | Create Task model | Backend | 15m |
| 4.2 | Create seed task JSON files | Backend | 45m |
| 4.3 | Create seed_tasks.py script | Backend | 20m |
| 4.4 | Implement `GET /tasks` | Backend | 20m |
| 4.5 | Implement `GET /tasks/{id}` | Backend | 15m |
| 4.6 | Implement `POST /tasks/{id}/run` | Backend | 45m |
| 4.7 | Implement `POST /tasks/{id}/submit` | Backend | 30m |
| 4.8 | Add test case validation logic | Backend | 30m |

**Deliverable:** Full task CRUD + code execution with test validation.

---

### Phase 5: Code Editor UI (Day 1 Evening / Day 2 Morning)

**Goal:** Functional sandbox UI with Monaco editor.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 5.1 | Install Monaco Editor package | Frontend | 10m |
| 5.2 | Create CodeEditor component | Frontend | 45m |
| 5.3 | Create TaskHeader component | Frontend | 20m |
| 5.4 | Create OutputPanel component | Frontend | 30m |
| 5.5 | Create RunButton component | Frontend | 15m |
| 5.6 | Build sandbox page layout | Frontend | 30m |
| 5.7 | Implement useCodeExecution hook | Frontend | 30m |
| 5.8 | Wire up run/submit flow | Frontend | 30m |
| 5.9 | Add syntax highlighting per language | Frontend | 20m |
| 5.10 | Add keyboard shortcuts (Cmd+Enter to run) | Frontend | 15m |

**Deliverable:** Candidate can open task, edit code, run, see results.

---

### Phase 6: Telemetry & Event Pipeline (Day 2 Morning)

**Goal:** Behavioral events captured and forwarded to Amplitude.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 6.1 | Create telemetry client (lib/telemetry.ts) | Frontend | 30m |
| 6.2 | Add event tracking to CodeEditor | Frontend | 30m |
| 6.3 | Track editor commands | Frontend | 20m |
| 6.4 | Track run attempts | Frontend | 15m |
| 6.5 | Track errors (from output) | Frontend | 20m |
| 6.6 | Detect and track paste bursts | Frontend | 30m |
| 6.7 | Create Event model | Backend | 15m |
| 6.8 | Implement `POST /track` | Backend | 30m |
| 6.9 | Store events in MongoDB | Backend | 15m |
| 6.10 | Create Amplitude forwarding service | Backend | 30m |
| 6.11 | Forward events async (background task) | Backend | 20m |
| 6.12 | Verify events in Amplitude dashboard | All | 15m |

**Deliverable:** Events flow from editor → API → MongoDB → Amplitude.

---

### Phase 7: SkillGraph ML Pipeline (Day 2 Morning/Afternoon)

**Goal:** Compute skill identity from behavioral events.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 7.1 | Define feature extraction functions | ML | 45m |
| 7.2 | Implement session feature vector | ML | 30m |
| 7.3 | Implement user aggregate vector | ML | 20m |
| 7.4 | Create synthetic training data | ML | 30m |
| 7.5 | Train KMeans archetype model | ML | 30m |
| 7.6 | Implement archetype prediction | ML | 20m |
| 7.7 | Implement cosine similarity job matching | ML | 20m |
| 7.8 | Create passport generation logic | ML | 30m |
| 7.9 | Trigger recomputation on task submit | Backend | 20m |
| 7.10 | Update Amplitude user properties | Backend | 20m |

**Deliverable:** After task submission, passport updates with new archetype/vector.

---

### Phase 8: Job Matching & Feed (Day 2 Afternoon)

**Goal:** Jobs unlock based on skill vector.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 8.1 | Create Job model | Backend | 15m |
| 8.2 | Create jobs.json seed data | Backend | 20m |
| 8.3 | Seed jobs to MongoDB | Backend | 10m |
| 8.4 | Implement `GET /jobs` with filtering | Backend | 30m |
| 8.5 | Create JobFeed component | Frontend | 30m |
| 8.6 | Create JobCard component | Frontend | 20m |
| 8.7 | Implement useJobFeed polling hook | Frontend | 25m |
| 8.8 | Create UnlockAnimation component | Frontend | 30m |
| 8.9 | Show locked vs unlocked jobs | Frontend | 20m |
| 8.10 | Add unlock requirements display | Frontend | 20m |

**Deliverable:** Job feed updates after task completion; new jobs animate in.

---

### Phase 9: Passport UI (Day 2 Afternoon)

**Goal:** Candidates and recruiters can view skill passports.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 9.1 | Implement `GET /passport/{user_id}` | Backend | 30m |
| 9.2 | Create SkillPassport component | Frontend | 45m |
| 9.3 | Create ArchetypeBadge component | Frontend | 20m |
| 9.4 | Create SkillVector visualization | Frontend | 30m |
| 9.5 | Create EvidenceList component | Frontend | 25m |
| 9.6 | Build candidate passport page | Frontend | 20m |
| 9.7 | Build recruiter candidate view | Frontend | 30m |

**Deliverable:** Full passport view with archetype, metrics, evidence.

---

### Phase 10: TwelveLabs Integration (Day 2 Evening)

**Goal:** Video upload, indexing, and semantic search.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 10.1 | Set up TwelveLabs account + API key | Backend | 10m |
| 10.2 | Implement TwelveLabs service | Backend | 30m |
| 10.3 | Create video index on startup | Backend | 15m |
| 10.4 | Implement `POST /video/upload` | Backend | 30m |
| 10.5 | Handle async video indexing | Backend | 30m |
| 10.6 | Implement `GET /video/search` | Backend | 25m |
| 10.7 | Create InterviewUploader component | Frontend | 30m |
| 10.8 | Create VideoPlayer component | Frontend | 25m |
| 10.9 | Create HighlightsList component | Frontend | 25m |
| 10.10 | Integrate highlights into passport | Frontend | 20m |

**Deliverable:** Upload video → indexed → recruiter can search moments.

---

### Phase 11: Recruiter Dashboard (Day 2 Evening / Day 3)

**Goal:** Recruiters can browse and evaluate candidates.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 11.1 | Create recruiter dashboard layout | Frontend | 30m |
| 11.2 | Implement candidate listing | Frontend | 25m |
| 11.3 | Add filtering by archetype | Frontend | 20m |
| 11.4 | Build candidate detail page | Frontend | 30m |
| 11.5 | Integrate video highlights | Frontend | 20m |
| 11.6 | Create security transparency panel | Frontend | 30m |

**Deliverable:** Full recruiter flow from browsing to viewing candidate.

---

### Phase 12: Demo Polish (Day 3)

**Goal:** Smooth end-to-end demo flow.

| # | Task | Owner | Est. |
|---|------|-------|------|
| 12.1 | Create comprehensive seed script | Backend | 45m |
| 12.2 | Generate synthetic events for demo users | Backend | 30m |
| 12.3 | Add loading states throughout | Frontend | 30m |
| 12.4 | Add error handling/toasts | Frontend | 30m |
| 12.5 | Polish animations | Frontend | 30m |
| 12.6 | Test full demo flow | All | 30m |
| 12.7 | Create demo script/talking points | All | 20m |
| 12.8 | Record backup video | All | 30m |

**Deliverable:** Polished, demo-ready application.

---

## Sponsor Track Integration

### Amplitude

**Requirement:** Events → AI → Visible Product Change (not just if/else rules)

**Our Implementation:**
- **Events:** Rich behavioral telemetry (12+ event types)
- **AI:** KMeans clustering + predictive job matching (ML, not rules)
- **Visible Change:** Jobs unlock in real-time; passport updates; archetype assigned

**Demo Highlight:**
1. Show Amplitude dashboard with live events streaming
2. Complete a task with specific behavior pattern
3. Show passport archetype change
4. Show new job unlocking

**Amplitude Dashboard Setup:**
- Create cohorts by archetype
- Build funnel: session_started → run_attempted → task_submitted
- User properties: `skill_archetype`, `skill_vector[]`, `integrity_score`

---

### TwelveLabs

**Requirement:** Core functionality uses video understanding endpoints

**Our Implementation:**
- Upload interview videos
- Auto-index with Marengo + Pegasus models
- Semantic search for moments ("explain testing approach")
- Surface highlights in recruiter view

**Demo Highlight:**
1. Show uploaded interview video
2. Type search query: "when did they mention collaboration?"
3. Jump to exact timestamp
4. Show how this becomes passport evidence

---

### 1Password

**Requirement:** Simple, honest, people-first security; passkeys as stretch

**Our Implementation:**

**Minimum (Required):**
- All secrets in 1Password: `AMPLITUDE_API_KEY`, `TWELVELABS_API_KEY`, `JWT_SECRET`, `MONGODB_URI`
- Run services with `op run --env-file=prod.env`
- No plaintext secrets in repo

**Stretch (Passkeys):**
- WebAuthn passkey registration for recruiters
- Passkey authentication flow
- Security transparency panel showing what data is collected

**Demo Highlight:**
1. Show `prod.env` with secret references (not values)
2. Show `op run` command starting services
3. Demonstrate passkey login flow
4. Show security panel explaining data collection

---

### MongoDB Atlas (MLH)

**Requirement:** Use MongoDB Atlas as database

**Our Implementation:**
- Primary datastore for all collections
- Cloud-hosted cluster
- Proper indexing for query performance
- Atlas dashboard showing data flow

**Demo Highlight:**
1. Show Atlas dashboard with collections
2. Show real-time document updates during demo
3. Highlight scalability (cloud-native)

---

## Security Considerations

### Code Execution Sandbox

```yaml
# sandbox-runner security measures
security:
  - Docker container isolation
  - No network access (--network none)
  - Read-only filesystem (mostly)
  - Resource limits:
      cpu: 0.5 cores
      memory: 256MB
      timeout: 10 seconds
  - Non-root user
  - No privileged operations
  - Temp directory for code execution
  - Cleanup after each run
```

### Data Privacy

- **Collect aggregates, not keystrokes:** We track signals (command type, timing patterns) not raw input
- **Transparency panel:** Users see exactly what's collected
- **Evidence linking:** Users understand why they got their identity
- **Opt-out:** Video analysis is optional
- **Data deletion:** Users can request data removal

### Authentication

- **Passwords:** bcrypt with cost factor 12
- **JWTs:** Short expiry (1 hour), refresh tokens (7 days)
- **Passkeys:** WebAuthn with proper challenge validation
- **HTTPS:** Required in production

---

## Demo Script

### 2-Minute Flow

**Setup:** Two browser windows (Candidate + Recruiter)

**0:00 - 0:20 | Introduction**
> "Proof of Skill is a freelance marketplace where your identity is what you do, not what you claim. Let me show you."

**0:20 - 0:50 | Candidate Journey**
1. Show candidate dashboard with tasks
2. Open "Fix Null Check Bug" task
3. Show starter code with the bug
4. Write fix (add null check)
5. Click Run → Show tests passing
6. Point out: "Events are streaming to Amplitude right now"

**0:50 - 1:10 | Identity Update**
1. Submit task
2. Show passport updating
3. Highlight archetype assignment: "Careful Debugger"
4. Show skill vector visualization

**1:10 - 1:30 | Job Unlock**
1. Navigate to job feed
2. Show new Tier-2 job animating in
3. Explain: "This job unlocked because my debug efficiency crossed the threshold"
4. Show locked Tier-3 job with requirements

**1:30 - 1:50 | Recruiter View**
1. Switch to recruiter window
2. Show candidate list filtered by archetype
3. Click on candidate
4. Show passport with behavioral evidence
5. Demo video search: "when did they talk about testing?"
6. Click timestamp → jump to moment

**1:50 - 2:00 | Security**
> "And all of this runs on 1Password for secrets—no plaintext credentials—and recruiters can use passkeys. Our security panel shows exactly what we collect."

---

## Appendix: Sample Task Definition

```json
{
  "task_id": "bugfix-null-check",
  "title": "Fix Null Reference Bug",
  "description": "## Problem\n\nThe `processUser` function crashes when passed a null or undefined user.\n\n## Requirements\n\n1. Return `null` if user is null/undefined\n2. Return `null` if user.name is null/undefined\n3. Return uppercase name otherwise\n\n## Hints\n\n- Consider using optional chaining\n- Think about all edge cases",
  "difficulty": "easy",
  "category": "bugfix",
  "language": "javascript",
  "starter_code": "function processUser(user) {\n  return user.name.toUpperCase();\n}\n\nmodule.exports = { processUser };",
  "test_cases": [
    {
      "input": {"user": {"name": "Alice"}},
      "expected_output": "ALICE",
      "hidden": false
    },
    {
      "input": {"user": null},
      "expected_output": null,
      "hidden": false
    },
    {
      "input": {"user": {"name": null}},
      "expected_output": null,
      "hidden": true
    },
    {
      "input": {"user": undefined},
      "expected_output": null,
      "hidden": true
    }
  ],
  "time_limit_seconds": 5
}
```

---

## Appendix: Environment Variables

### `prod.env.example` (1Password References)

```env
# MongoDB Atlas
MONGODB_URI=op://hackathon/mongodb/connection_string

# JWT
JWT_SECRET=op://hackathon/app/jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=1

# Amplitude
AMPLITUDE_API_KEY=op://hackathon/amplitude/api_key

# TwelveLabs
TWELVELABS_API_KEY=op://hackathon/twelvelabs/api_key

# WebAuthn
WEBAUTHN_RP_ID=localhost
WEBAUTHN_RP_NAME=Proof of Skill
WEBAUTHN_ORIGIN=http://localhost:3000

# Sandbox
SANDBOX_RUNNER_URL=http://sandbox-runner:8080
```

---

## Appendix: Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: ./apps/web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - api

  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - JWT_SECRET=${JWT_SECRET}
      - AMPLITUDE_API_KEY=${AMPLITUDE_API_KEY}
      - TWELVELABS_API_KEY=${TWELVELABS_API_KEY}
      - SANDBOX_RUNNER_URL=http://sandbox-runner:8080
    depends_on:
      - sandbox-runner

  sandbox-runner:
    build: ./apps/sandbox-runner
    ports:
      - "8080:8080"
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:size=100M
```

---

*Document Version: 1.0*
*Last Updated: January 2026*
*UofTHacks 2026 - Proof of Skill Team*
