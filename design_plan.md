# UofTHacks 2026 - SkillPulse Design Plan

**Concept:** A self-improving AI-powered technical interview & OA platform using Behavioral Analytics.

---

## 1. Executive Summary

**SkillPulse** is an AI-powered technical interview and online assessment (OA) platform that moves beyond binary "Pass/Fail" metrics. It treats the coding interview as a data stream, analyzing **how** a candidate engineers a solution (testing habits, debugging efficiency, optimization patterns), rather than just the final output.

### The "Amplitude Loop" (Data → Insight → Action)

1. **Data:** Track granular **semantic events** (e.g., `test_case_added`, `refactor_start`) instead of just keystrokes.
2. **Insight:** An asynchronous AI Worker analyzes these patterns to build a live **Engineering DNA Radar Chart**.
3. **Action:**
   * **Self-Improving Candidate Experience:** Detect frustration and dynamically intervene with hints to prevent churn.
   * **Smart Employer Matching:** Match candidates to jobs using vector similarity on behavioral profiles, not just keywords.

### Relationship to Existing Implementation

This plan builds on the existing **Proof of Skill** codebase which has already implemented:
- FastAPI backend with auth, tasks, events, passports, jobs routes
- Next.js frontend with Monaco editor and telemetry
- Sandbox runner for secure code execution
- MongoDB Atlas integration
- Amplitude event forwarding
- Skill vector/passport system (maps to "Engineering DNA Radar")

**New Focus:** Adding AI-powered real-time analysis, frustration detection, and dynamic hint generation.

---

## 2. System Architecture

### Tech Stack

* **Frontend:** Next.js 14 (React), Tailwind CSS, Monaco Editor, Recharts ✅ *Implemented*
* **Backend API:** FastAPI (Python 3.11+) ✅ *Implemented*
* **Database:** MongoDB Atlas ✅ *Implemented*
* **Async Queue:** Python asyncio + background tasks (or Redis/Celery for scale)
* **AI Engine:** OpenAI GPT-4o / Claude API (via httpx or official SDK)
* **Code Execution:** Custom Docker sandbox runner ✅ *Implemented*
* **Analytics:** Amplitude HTTP API ✅ *Implemented*

### Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│   Next.js 14 Web App                                                        │
│   ├── Monaco Editor (captures semantic events)                              │
│   ├── Engineering DNA Radar (Recharts visualization)                        │
│   └── AI Hint Panel (receives interventions)                                │
└─────────────────────────────────────────────────────────────────────────────┘
              │ POST /track (events)              │ GET /radar (polling)
              ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER (FastAPI)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐  │
│   │   /track    │  │   /radar    │  │   /tasks    │  │   /ai/intervene   │  │
│   │   Events    │  │   Profile   │  │  Execution  │  │   Hint Generator  │  │
│   └──────┬──────┘  └─────────────┘  └─────────────┘  └───────────────────┘  │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    Background AI Worker                              │   │
│   │   • Consumes event batches                                          │   │
│   │   • Calls LLM for pattern analysis                                  │   │
│   │   • Updates radar_profile scores                                    │   │
│   │   • Triggers interventions when stuck detected                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
              │                         │
              ▼                         ▼
┌───────────────────────┐    ┌─────────────────────────────────────────────────┐
│      Amplitude        │    │                  MongoDB Atlas                   │
│   (Analytics SaaS)    │    │   users, events, sessions, tasks, jobs          │
└───────────────────────┘    └─────────────────────────────────────────────────┘
```

**Data Flow:**
1. **Frontend (Next.js)** captures semantic events via Monaco hooks
2. **POST /track** ingests events → stored in MongoDB + forwarded to Amplitude
3. **AI Worker** (background task) processes recent events → calls LLM → updates radar_profile
4. **Frontend** polls `/radar/{userId}` for updated scores + intervention hints

---

## 3. Data Design (MongoDB Schema)

> **Note:** These schemas extend the existing collections from the Proof of Skill implementation.

### 3.1 `users` Collection (Extended)

Extends the existing user model with radar_profile for AI analysis.

```javascript
{
  _id: ObjectId,
  email: String,                    // ✅ Existing
  password_hash: String,            // ✅ Existing
  role: "candidate" | "recruiter",  // ✅ Existing (maps to employer)
  display_name: String,             // ✅ Existing

  // ✅ Existing skill identity (keep for backwards compatibility)
  skill_vector: [Number],
  archetype: String,
  integrity_score: Number,

  // 🆕 NEW: Engineering DNA Radar (richer profile with confidence)
  radar_profile: {
    verification:   { score: 0.8, confidence: 0.9 }, // Testing mindset
    velocity:       { score: 0.6, confidence: 0.7 }, // Speed of delivery
    optimization:   { score: 0.3, confidence: 0.4 }, // Algorithmic efficiency
    decomposition:  { score: 0.9, confidence: 0.8 }, // Code modularity
    debugging:      { score: 0.7, confidence: 0.6 }  // Error resolution
  },

  created_at: ISODate
}
```

### 3.2 `jobs` Collection (Extended)

Extends existing jobs with AI-parsed target radar.

```javascript
{
  _id: ObjectId,
  job_id: String,                   // ✅ Existing
  title: String,                    // ✅ Existing
  company: String,                  // ✅ Existing
  tier: 0 | 1 | 2,                  // ✅ Existing

  // ✅ Existing matching fields
  target_vector: [Number],
  min_fit: Number,
  must_have: { ... },

  // 🆕 NEW: AI-parsed radar target (from job description)
  target_radar: {
    verification: 0.9,   // High reliability needed
    velocity: 0.4,       // Speed less important
    optimization: 0.7,
    decomposition: 0.6,
    debugging: 0.5
  },

  description: String,              // Job description (used for AI parsing)
  created_at: ISODate
}
```

### 3.3 `sessions` Collection (Extended)

Extends existing sessions with AI intervention context.

```javascript
{
  _id: ObjectId,
  session_id: String,               // ✅ Existing (UUID)
  user_id: ObjectId,                // ✅ Existing
  task_id: String,                  // ✅ Existing
  started_at: ISODate,              // ✅ Existing
  ended_at: ISODate,                // ✅ Existing

  // ✅ Existing outcomes
  submitted: Boolean,
  passed: Boolean,
  score: Number,
  feature_vector: [Number],

  // 🆕 NEW: AI intervention context
  ai_context: {
    is_stuck: Boolean,              // Detected by AI worker
    stuck_since: ISODate,           // When frustration started
    intervention_count: Number,     // Hints given this session
    last_hint: String,              // Most recent hint text
    error_streak: Number            // Consecutive errors of same type
  },

  current_code_snapshot: String     // Latest code state for AI context
}
```

### 3.4 `interventions` Collection (NEW)

Tracks AI-generated hints and their effectiveness.

```javascript
{
  _id: ObjectId,
  session_id: String,
  user_id: ObjectId,
  task_id: String,

  triggered_at: ISODate,
  trigger_reason: "error_streak" | "time_stuck" | "repeated_pattern",

  hint_text: String,                // The hint shown to user
  hint_category: "syntax" | "logic" | "approach" | "encouragement",

  // Effectiveness tracking
  acknowledged: Boolean,            // User clicked/saw hint
  code_changed_after: Boolean,      // Did they modify code?
  resolved_issue: Boolean,          // Did next run succeed?
  time_to_resolution_ms: Number
}
```

---

## 4. Semantic Event Schema (Amplitude)

This schema is critical for the **Data** criteria. We track **intent**, not just clicks.

> **Note:** Extends existing event types from `apps/api/routes/track.py`

### 4.1 Existing Events (Already Implemented)

| Event Type | Trigger | Properties |
|------------|---------|------------|
| `session_started` | Sandbox opened | `task_id`, `difficulty` |
| `editor_command` | Any editor action | `command`, `source` |
| `code_changed` | Debounced edit | `lines_changed`, `chars_added` |
| `run_attempted` | Click run | `result`, `runtime_ms`, `tests_passed` |
| `error_emitted` | Runtime error | `error_type`, `stack_depth`, `is_repeat` |
| `task_submitted` | Final submission | `passed`, `score` |

### 4.2 New Semantic Events (To Implement)

| Category | Event Name               | Trigger Logic                                 | Insight Derived                     |
| -------- | ------------------------ | --------------------------------------------- | ----------------------------------- |
| Thinking | `solution_draft_started` | User starts typing > 5s after page load       | Planning: did they read the prompt? |
| Thinking | `docs_lookup`            | Focus lost to documentation tab               | Resourcefulness                     |
| Coding   | `semantic_block_added`   | User defines a new function/class             | Decomposition: modular thinking     |
| Coding   | `library_import`         | User imports standard lib (e.g., collections) | Fluency                             |
| Verify   | `test_case_authored`     | User creates a custom input                   | Verification: proactive QA          |
| Verify   | `execution_error_streak` | 3+ errors of same type in 1 min               | Resilience / needs intervention?    |
| Optimize | `refactor_initiated`     | Editing code after passing tests              | Craftsmanship                       |
| AI       | `hint_displayed`         | AI intervention shown to user                 | Intervention tracking               |
| AI       | `hint_acknowledged`      | User interacted with hint                     | Hint effectiveness                  |

---

## 5. End-to-End Implementation Logic

### 5.1 Frontend: The "Smart IDE" (Extend Existing)

**Location:** `apps/web/src/components/sandbox/CodeEditor.tsx` ✅ *Exists*

**Existing Features:**
- Monaco Editor wrapper with language support
- Telemetry hooks for `editor_command`, `code_changed`
- Keyboard shortcut tracking

**New: Semantic Observer Hook**

Create `apps/web/src/hooks/useSemanticObserver.ts`:

```typescript
import { useCallback, useRef } from 'react';
import { trackEvent } from '@/lib/telemetry';

export function useSemanticObserver(sessionId: string, taskId: string) {
  const lastCode = useRef('');
  const sessionStartTime = useRef(Date.now());

  const analyzeCodeChange = useCallback((newCode: string) => {
    // Detect function/class definitions
    const functionRegex = /(?:function\s+\w+|const\s+\w+\s*=.*=>|def\s+\w+)/g;
    const newFunctions = newCode.match(functionRegex) || [];
    const oldFunctions = lastCode.current.match(functionRegex) || [];

    if (newFunctions.length > oldFunctions.length) {
      trackEvent('semantic_block_added', { sessionId, taskId, type: 'function' });
    }

    // Detect imports
    const importRegex = /(?:import\s+|from\s+\w+\s+import|require\()/g;
    if (importRegex.test(newCode) && !importRegex.test(lastCode.current)) {
      trackEvent('library_import', { sessionId, taskId });
    }

    lastCode.current = newCode;
  }, [sessionId, taskId]);

  return { analyzeCodeChange };
}
```

**New: AI Hint Panel Component**

Create `apps/web/src/components/sandbox/HintPanel.tsx`:

```typescript
interface HintPanelProps {
  sessionId: string;
  hint: string | null;
  onAcknowledge: () => void;
}

export function HintPanel({ sessionId, hint, onAcknowledge }: HintPanelProps) {
  if (!hint) return null;

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
      <p className="text-sm text-yellow-700">{hint}</p>
      <button onClick={onAcknowledge} className="text-xs underline">
        Got it
      </button>
    </div>
  );
}
```

**Live Radar Polling:**

```typescript
// In apps/web/src/hooks/useRadar.ts
import useSWR from 'swr';

export function useRadar(userId: string) {
  return useSWR(`/api/radar/${userId}`, fetcher, {
    refreshInterval: 5000 // Poll every 5 seconds
  });
}
```

---

### 5.2 Backend: Event Ingestion (Extend Existing)

**Location:** `apps/api/routes/track.py` ✅ *Exists*

**Current Flow:**
1. Receive event via `POST /track`
2. Store in MongoDB `events` collection
3. Forward to Amplitude (background task)

**Enhancement: Trigger AI Analysis**

```python
# apps/api/routes/track.py - Add to existing endpoint

from services.ai_worker import trigger_analysis

@router.post("/track")
async def track_event(event: TrackEvent, user: User = Depends(get_current_user)):
    # ... existing code ...

    # 🆕 Trigger AI analysis for intervention detection
    if event.event_type in ["run_attempted", "error_emitted", "code_changed"]:
        background_tasks.add_task(
            trigger_analysis,
            session_id=event.session_id,
            user_id=str(user.id)
        )

    return {"event_id": str(result.inserted_id), "forwarded_to_amplitude": True}
```

---

### 5.3 Backend: AI Worker Service (NEW)

**Location:** `apps/api/services/ai_worker.py`

```python
import httpx
from datetime import datetime, timedelta
from db.collections import events_collection, sessions_collection, users_collection
from config import settings

async def trigger_analysis(session_id: str, user_id: str):
    """
    Analyze recent events and potentially trigger an intervention.
    Called as a background task after relevant events.
    """
    # Step 1: Fetch recent events for this session
    recent_events = await events_collection.find(
        {"session_id": session_id}
    ).sort("timestamp", -1).limit(10).to_list(10)

    if not recent_events:
        return

    # Step 2: Check for frustration signals
    frustration = detect_frustration(recent_events)

    # Step 3: If frustrated, call LLM for hint generation
    if frustration["is_stuck"]:
        hint = await generate_hint(recent_events, frustration)

        # Update session with AI context
        await sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {
                "ai_context.is_stuck": True,
                "ai_context.last_hint": hint,
                "ai_context.stuck_since": datetime.utcnow()
            }, "$inc": {"ai_context.intervention_count": 1}}
        )

    # Step 4: Update radar profile scores
    await update_radar_profile(user_id, recent_events)


def detect_frustration(events: list) -> dict:
    """
    Detect if user is stuck based on event patterns.
    """
    error_events = [e for e in events if e["event_type"] == "error_emitted"]
    run_events = [e for e in events if e["event_type"] == "run_attempted"]

    # Check for error streak (3+ same errors in last 5 events)
    if len(error_events) >= 3:
        error_types = [e.get("properties", {}).get("error_type") for e in error_events[:3]]
        if len(set(error_types)) == 1:  # All same error type
            return {"is_stuck": True, "reason": "error_streak", "error_type": error_types[0]}

    # Check for repeated failed runs without code changes
    failed_runs = [e for e in run_events if not e.get("properties", {}).get("passed")]
    if len(failed_runs) >= 3:
        return {"is_stuck": True, "reason": "repeated_failures"}

    return {"is_stuck": False}


async def generate_hint(events: list, frustration: dict) -> str:
    """
    Call LLM to generate a contextual hint.
    """
    # Get current code from session
    session = await sessions_collection.find_one(
        {"session_id": events[0]["session_id"]}
    )
    current_code = session.get("current_code_snapshot", "") if session else ""

    prompt = f"""You are a helpful coding mentor. A student is working on a coding challenge and appears stuck.

Recent activity:
{format_events_for_llm(events)}

Current code:
```
{current_code[:1000]}
```

Frustration signal: {frustration['reason']}

Generate a single, concise hint (1-2 sentences) that guides them without giving away the answer. Be encouraging."""

    # Call OpenAI/Claude API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100
            }
        )
        result = response.json()
        return result["choices"][0]["message"]["content"]


async def update_radar_profile(user_id: str, events: list):
    """
    Update user's Engineering DNA radar based on recent behavior.
    """
    # Count semantic signals
    test_events = len([e for e in events if "test" in e.get("event_type", "")])
    refactor_events = len([e for e in events if e.get("event_type") == "refactor_initiated"])
    error_fixes = len([e for e in events if e.get("event_type") == "fix_applied"])

    # Calculate incremental score updates
    verification_delta = test_events * 0.02
    optimization_delta = refactor_events * 0.03
    debugging_delta = error_fixes * 0.02

    # Apply updates with confidence weighting
    await users_collection.update_one(
        {"_id": user_id},
        {"$inc": {
            "radar_profile.verification.score": verification_delta,
            "radar_profile.optimization.score": optimization_delta,
            "radar_profile.debugging.score": debugging_delta
        }}
    )
```

---

### 5.4 Backend: Radar Profile Endpoint (NEW)

**Location:** `apps/api/routes/radar.py`

```python
from fastapi import APIRouter, Depends
from middleware.auth import get_current_user
from db.collections import users_collection, sessions_collection
from models.user import User

router = APIRouter(prefix="/radar", tags=["radar"])

@router.get("/{user_id}")
async def get_radar_profile(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Get user's Engineering DNA radar profile with any pending interventions.
    """
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get active session intervention status
    active_session = await sessions_collection.find_one(
        {"user_id": user_id, "ended_at": None},
        sort=[("started_at", -1)]
    )

    intervention = None
    if active_session and active_session.get("ai_context", {}).get("is_stuck"):
        intervention = {
            "hint": active_session["ai_context"].get("last_hint"),
            "session_id": active_session["session_id"]
        }

    return {
        "user_id": user_id,
        "radar_profile": user.get("radar_profile", {}),
        "intervention": intervention
    }
```

---

### 5.5 Employer Portal: Match Engine (Extend Existing)

**Location:** `apps/api/routes/jobs.py` ✅ *Exists*

**Current:** Cosine similarity on `skill_vector` ✅

**Enhancement:** Add radar-based matching

```python
# apps/api/services/skillgraph.py - Add radar matching

def compute_radar_fit(candidate_radar: dict, job_target_radar: dict) -> float:
    """
    Compute fit score between candidate radar and job requirements.
    Returns 0.0 to 1.0.
    """
    dimensions = ["verification", "velocity", "optimization", "decomposition", "debugging"]

    candidate_vec = [candidate_radar.get(d, {}).get("score", 0.5) for d in dimensions]
    target_vec = [job_target_radar.get(d, 0.5) for d in dimensions]

    # Weighted cosine similarity (weight by confidence)
    confidence_weights = [candidate_radar.get(d, {}).get("confidence", 0.5) for d in dimensions]

    dot_product = sum(c * t * w for c, t, w in zip(candidate_vec, target_vec, confidence_weights))
    magnitude = (sum(c**2 * w for c, w in zip(candidate_vec, confidence_weights)) ** 0.5 *
                 sum(t**2 for t in target_vec) ** 0.5)

    return dot_product / magnitude if magnitude > 0 else 0.0
```

**Recruiter Dashboard UI:** `apps/web/src/app/recruiter/candidates/page.tsx` ✅ *Exists (needs API integration)*

---

## 6. Implementation Phases

### Phase 1: AI Worker Foundation (Priority)
- [ ] Create `services/ai_worker.py` with frustration detection
- [ ] Add OpenAI/Claude API integration
- [ ] Create `/radar/{user_id}` endpoint
- [ ] Add `ai_context` fields to sessions collection

### Phase 2: Frontend Hints
- [ ] Create `HintPanel` component
- [ ] Add `useRadar` hook with polling
- [ ] Integrate hint display into sandbox page
- [ ] Track hint acknowledgment events

### Phase 3: Semantic Events
- [ ] Create `useSemanticObserver` hook
- [ ] Add function/class detection regex
- [ ] Add import detection
- [ ] Emit new event types to backend

### Phase 4: Radar Visualization
- [ ] Create radar chart component (Recharts)
- [ ] Display on candidate passport page
- [ ] Add to recruiter candidate view

### Phase 5: Enhanced Job Matching
- [ ] Add `target_radar` to jobs schema
- [ ] Implement `compute_radar_fit()`
- [ ] Update job listing to show radar-based match scores
- [ ] Add "Why matched" tooltip

---

## 7. Environment Variables (Additional)

Add to `apps/api/.env`:

```env
# AI Service
OPENAI_API_KEY=op://hackathon/openai/api_key
# Or for Claude:
ANTHROPIC_API_KEY=op://hackathon/anthropic/api_key

# Intervention Settings
AI_HINT_ENABLED=true
FRUSTRATION_THRESHOLD_ERRORS=3
FRUSTRATION_THRESHOLD_TIME_MS=120000
```

---

# SPONSOR TRACK INTEGRATION

This section details how SkillPulse integrates with the three sponsor challenges to create a cohesive, multi-track submission.

## 8. Sponsor Track Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SKILLPULSE - SPONSOR INTEGRATION                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐    │
│   │   AMPLITUDE  │     │  TWELVELABS  │     │      BACKBOARD.IO        │    │
│   │   (Events)   │     │   (Video)    │     │  (Multi-Model + Memory)  │    │
│   └──────┬───────┘     └──────┬───────┘     └────────────┬─────────────┘    │
│          │                    │                          │                   │
│          ▼                    ▼                          ▼                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        FastAPI Backend                               │   │
│   │                                                                      │   │
│   │  POST /track ──────► Event Store ──────► AI Worker ──────┐           │   │
│   │       │                   │                    │         │           │   │
│   │       │                   │              ┌─────▼─────┐   │           │   │
│   │       ▼                   │              │ Backboard │   │           │   │
│   │   Amplitude               │              │  Router   │   │           │   │
│   │   Forward                 │              └─────┬─────┘   │           │   │
│   │                           │                    │         │           │   │
│   │                           │         ┌─────────┼─────────┐│           │   │
│   │                           │         ▼         ▼         ▼│           │   │
│   │                           │      Claude    GPT-4o    Gemini          │   │
│   │                           │      (hints)   (code)   (summary)        │   │
│   │                           │                                          │   │
│   │  POST /video/upload ──────┴──────► TwelveLabs Index                  │   │
│   │  GET /video/search ─────────────► Semantic Search                    │   │
│   │  GET /video/highlights ─────────► Auto-generated Highlights          │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Sponsor | Challenge | How SkillPulse Addresses It |
|---------|-----------|----------------------------|
| **Amplitude** | Self-improving products with behavioral data + AI | Core platform: event tracking → AI analysis → personalized hints + job matching |
| **TwelveLabs** | Video understanding with Pegasus/Marengo | Interview replay analysis, semantic search, auto-highlights for recruiters |
| **Backboard.io** | Adaptive memory + multi-model switching | Different LLMs for different tasks, remembers past hints to avoid repetition |

---

## 9. TwelveLabs Integration: Interview Replay Intelligence

### 9.1 Concept

Candidates can optionally record their screen + audio during coding sessions. TwelveLabs indexes these videos, enabling:
- **Semantic search**: Recruiters ask "when did they discuss testing?" and jump to exact timestamp
- **Auto-highlights**: AI extracts key moments (explaining approach, debugging, discussing tradeoffs)
- **Interview summaries**: Auto-generated text summary for recruiter review

### 9.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CANDIDATE INTERVIEW FLOW                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. Candidate records screen + audio while coding               │
│   2. Video uploaded to TwelveLabs for indexing                   │
│   3. AI extracts:                                                │
│      • Verbal explanations of approach                           │
│      • Moments of debugging thought process                      │
│      • Communication clarity score                               │
│   4. Recruiters can search: "when did they explain recursion?"   │
│   5. Auto-generate highlight reel of best moments                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 TwelveLabs Service Implementation

**Location:** `apps/api/services/twelvelabs.py`

```python
import httpx
import asyncio
from config import settings

TWELVELABS_BASE_URL = "https://api.twelvelabs.io/v1.2"

class TwelveLabsService:
    """
    TwelveLabs integration for interview video understanding.
    Uses Marengo for indexing and Pegasus for generation.
    """

    def __init__(self):
        self.api_key = settings.twelvelabs_api_key
        self.index_id = settings.twelvelabs_index_id

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make authenticated request to TwelveLabs API."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method,
                f"{TWELVELABS_BASE_URL}{endpoint}",
                headers={"x-api-key": self.api_key},
                **kwargs
            )
            response.raise_for_status()
            return response.json()

    async def create_index(self, index_name: str) -> str:
        """Create a new index for video storage."""
        result = await self._request(
            "POST", "/indexes",
            json={
                "name": index_name,
                "engines": [
                    {"name": "marengo2.6", "options": ["visual", "conversation", "text_in_video"]},
                    {"name": "pegasus1.1", "options": ["visual", "conversation"]}
                ]
            }
        )
        return result["_id"]

    async def index_interview_video(self, video_url: str, user_id: str, session_id: str) -> dict:
        """
        Upload and index an interview recording.
        Returns task_id for polling status.
        """
        result = await self._request(
            "POST", "/tasks",
            json={
                "index_id": self.index_id,
                "url": video_url,
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "type": "coding_interview"
                }
            }
        )
        return {
            "task_id": result["_id"],
            "status": result["status"]
        }

    async def get_task_status(self, task_id: str) -> dict:
        """Check video indexing status."""
        result = await self._request("GET", f"/tasks/{task_id}")
        return {
            "status": result["status"],
            "video_id": result.get("video_id"),
            "error": result.get("error")
        }

    async def search_interview_moments(self, video_id: str, query: str) -> list:
        """
        Semantic search within interview video.
        Example queries: "explaining their approach", "debugging", "discussing tradeoffs"
        """
        result = await self._request(
            "POST", "/search",
            json={
                "index_id": self.index_id,
                "query": query,
                "search_options": ["visual", "conversation", "text_in_video"],
                "filter": {"id": [video_id]},
                "threshold": "medium"
            }
        )
        return [{
            "start": clip["start"],
            "end": clip["end"],
            "confidence": clip["confidence"],
            "thumbnail_url": clip.get("thumbnail_url"),
            "transcript": clip.get("metadata", {}).get("transcript", "")
        } for clip in result.get("data", [])]

    async def generate_interview_summary(self, video_id: str) -> str:
        """
        Generate a comprehensive summary of the interview using Pegasus.
        """
        result = await self._request(
            "POST", "/summarize",
            json={
                "video_id": video_id,
                "type": "summary",
                "prompt": """Summarize this coding interview session. Include:
1. The candidate's problem-solving approach
2. How they handled debugging and errors
3. Their communication clarity when explaining decisions
4. Key technical decisions they made
5. Overall impression of their engineering style"""
            }
        )
        return result.get("summary", "")

    async def generate_highlights(self, video_id: str) -> str:
        """Generate bullet-point highlights for quick recruiter review."""
        result = await self._request(
            "POST", "/generate",
            json={
                "video_id": video_id,
                "type": "highlight",
                "prompt": "Extract the top 5 most impressive or notable moments from this coding interview."
            }
        )
        return result.get("data", "")

    async def extract_highlight_clips(self, video_id: str) -> list:
        """
        Extract key moments for recruiter review using semantic search.
        Returns timestamped clips for each category.
        """
        highlight_queries = [
            ("approach", "candidate explaining their problem-solving approach"),
            ("debugging", "candidate debugging and fixing an error"),
            ("tradeoffs", "candidate discussing tradeoffs or alternative solutions"),
            ("questions", "candidate asking clarifying questions"),
            ("testing", "candidate discussing or writing tests"),
            ("optimization", "candidate optimizing or refactoring code")
        ]

        highlights = []
        for category, query in highlight_queries:
            moments = await self.search_interview_moments(video_id, query)
            for moment in moments[:2]:  # Top 2 per category
                highlights.append({
                    "category": category,
                    "query": query,
                    "start": moment["start"],
                    "end": moment["end"],
                    "confidence": moment["confidence"],
                    "transcript": moment.get("transcript", "")
                })

        # Sort by confidence and return top highlights
        highlights.sort(key=lambda x: x["confidence"], reverse=True)
        return highlights[:10]

    async def analyze_communication_style(self, video_id: str) -> dict:
        """
        Analyze candidate's communication patterns using Pegasus.
        """
        result = await self._request(
            "POST", "/generate",
            json={
                "video_id": video_id,
                "type": "text",
                "prompt": """Analyze the candidate's communication style in this coding interview.
Rate each aspect from 1-5 and provide a brief justification:
- Clarity: How clearly do they explain technical concepts?
- Confidence: How confident do they sound when presenting solutions?
- Collaboration: Do they think out loud and invite feedback?
- Technical depth: Do they use appropriate technical terminology?
Return as JSON: {"clarity": {"score": X, "reason": "..."}, ...}"""
            }
        )
        import json
        try:
            return json.loads(result.get("data", "{}"))
        except:
            return {}
```

### 9.4 Video API Endpoints

**Location:** `apps/api/routes/video.py` (extend existing)

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from services.twelvelabs import TwelveLabsService
from db.collections import videos_collection, passports_collection
from middleware.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/video", tags=["video"])

@router.post("/upload")
async def upload_interview_video(
    video_url: str,
    session_id: str,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user)
):
    """
    Submit interview video for TwelveLabs indexing.
    Returns immediately; indexing happens asynchronously.
    """
    twelvelabs = TwelveLabsService()

    # Start indexing
    result = await twelvelabs.index_interview_video(
        video_url=video_url,
        user_id=str(user.id),
        session_id=session_id
    )

    # Store video record
    video_doc = {
        "user_id": user.id,
        "session_id": session_id,
        "video_url": video_url,
        "twelvelabs_task_id": result["task_id"],
        "status": "indexing",
        "uploaded_at": datetime.utcnow()
    }
    insert_result = await videos_collection.insert_one(video_doc)

    # Background task to poll for completion
    background_tasks.add_task(
        poll_indexing_completion,
        task_id=result["task_id"],
        video_doc_id=str(insert_result.inserted_id),
        user_id=str(user.id)
    )

    return {
        "video_id": str(insert_result.inserted_id),
        "status": "indexing",
        "message": "Video submitted for processing. Check status endpoint for updates."
    }


async def poll_indexing_completion(task_id: str, video_doc_id: str, user_id: str):
    """Background task to poll TwelveLabs and update status when ready."""
    import asyncio
    twelvelabs = TwelveLabsService()

    for _ in range(60):  # Poll for up to 10 minutes
        await asyncio.sleep(10)
        status = await twelvelabs.get_task_status(task_id)

        if status["status"] == "ready":
            # Video is indexed, run analysis
            video_id = status["video_id"]

            summary, highlights, communication = await asyncio.gather(
                twelvelabs.generate_interview_summary(video_id),
                twelvelabs.extract_highlight_clips(video_id),
                twelvelabs.analyze_communication_style(video_id)
            )

            # Update video document
            await videos_collection.update_one(
                {"_id": video_doc_id},
                {"$set": {
                    "status": "ready",
                    "twelvelabs_video_id": video_id,
                    "summary": summary,
                    "highlights": highlights,
                    "communication_analysis": communication,
                    "ready_at": datetime.utcnow()
                }}
            )

            # Update user's passport with video insights
            await passports_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "interview_video_id": video_id,
                    "interview_summary": summary,
                    "interview_highlights": highlights,
                    "communication_scores": communication
                }}
            )
            return

        elif status["status"] == "failed":
            await videos_collection.update_one(
                {"_id": video_doc_id},
                {"$set": {"status": "failed", "error": status.get("error")}}
            )
            return


@router.get("/{video_id}/status")
async def get_video_status(video_id: str, user = Depends(get_current_user)):
    """Check video processing status."""
    video = await videos_collection.find_one({"_id": video_id, "user_id": user.id})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "video_id": video_id,
        "status": video["status"],
        "ready_at": video.get("ready_at"),
        "has_summary": "summary" in video,
        "highlight_count": len(video.get("highlights", []))
    }


@router.get("/{video_id}/search")
async def search_video(
    video_id: str,
    q: str,
    user = Depends(get_current_user)
):
    """
    Semantic search within interview video.
    Example: ?q=when did they discuss testing strategy
    """
    video = await videos_collection.find_one({"_id": video_id})
    if not video or video.get("status") != "ready":
        raise HTTPException(status_code=400, detail="Video not ready for search")

    twelvelabs = TwelveLabsService()
    results = await twelvelabs.search_interview_moments(
        video_id=video["twelvelabs_video_id"],
        query=q
    )

    return {
        "query": q,
        "results": results
    }


@router.get("/{video_id}/summary")
async def get_video_summary(video_id: str, user = Depends(get_current_user)):
    """Get AI-generated interview summary and highlights."""
    video = await videos_collection.find_one({"_id": video_id})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "summary": video.get("summary"),
        "highlights": video.get("highlights", []),
        "communication_analysis": video.get("communication_analysis", {})
    }


@router.post("/{video_id}/analyze")
async def analyze_interview(video_id: str, user = Depends(get_current_user)):
    """
    Run full TwelveLabs analysis on interview video (re-analyze).
    """
    video = await videos_collection.find_one({"_id": video_id})
    if not video or not video.get("twelvelabs_video_id"):
        raise HTTPException(status_code=400, detail="Video not indexed")

    twelvelabs = TwelveLabsService()

    summary, highlights, communication = await asyncio.gather(
        twelvelabs.generate_interview_summary(video["twelvelabs_video_id"]),
        twelvelabs.extract_highlight_clips(video["twelvelabs_video_id"]),
        twelvelabs.analyze_communication_style(video["twelvelabs_video_id"])
    )

    # Update records
    await videos_collection.update_one(
        {"_id": video_id},
        {"$set": {
            "summary": summary,
            "highlights": highlights,
            "communication_analysis": communication,
            "analyzed_at": datetime.utcnow()
        }}
    )

    return {
        "summary": summary,
        "highlights": highlights,
        "communication_analysis": communication
    }
```

### 9.5 TwelveLabs Judging Criteria Alignment

| Criteria | How SkillPulse Addresses It |
|----------|----------------------------|
| **API Use** | Core interview analysis uses search, summarize, and generate endpoints |
| **Impact** | Real recruiter workflow: search interviews, get highlights, understand candidates |
| **Wow Factor** | Natural language search in videos + auto-generated highlight reels |
| **Technical Depth** | Multiple endpoint types, async processing, integration with passport system |
| **UX Quality** | Recruiter dashboard surfaces video insights alongside behavioral data |

---

## 10. Backboard.io Integration: Adaptive Multi-Model AI

### 10.1 Concept

Different AI models excel at different tasks. Backboard.io provides:
- **Single API** for multiple LLM providers (Claude, GPT, Gemini, Cohere)
- **Adaptive memory** that persists across sessions per user
- **Intelligent routing** to choose the best model for each task

### 10.2 Model Selection Strategy

| Task | Model | Rationale |
|------|-------|-----------|
| Hint generation (encouragement) | `anthropic/claude-3-haiku` | Empathetic, pedagogical tone |
| Code error analysis | `openai/gpt-4o-mini` | Strong at code understanding |
| Radar profile summarization | `google/gemini-1.5-flash` | Good at structured analysis |
| Job description parsing | `cohere/command-r` | Efficient for extraction tasks |

### 10.3 Backboard Service Implementation

**Location:** `apps/api/services/backboard.py`

```python
import httpx
import json
from typing import Optional
from config import settings

BACKBOARD_BASE_URL = "https://api.backboard.io/v1"

class BackboardService:
    """
    Multi-model AI service using Backboard.io for adaptive memory
    and intelligent model switching.

    Backboard.io provides:
    - Single API for 2200+ LLMs
    - Built-in memory that persists across sessions
    - $10 free credits with promo code UOFTHACKS26
    """

    def __init__(self, user_id: str):
        self.api_key = settings.backboard_api_key
        self.user_id = user_id  # Used for memory context

    async def _call_model(
        self,
        model: str,
        messages: list,
        memory_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generic model call with optional memory.
        Memory is keyed per-user to enable personalization.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # Enable Backboard memory for personalization
            if memory_key:
                payload["memory"] = {
                    "enabled": True,
                    "key": f"{self.user_id}:{memory_key}"
                }

            response = await client.post(
                f"{BACKBOARD_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    # =========================================================================
    # HINT GENERATION - Claude (empathetic, pedagogical)
    # =========================================================================

    async def generate_hint(self, code: str, error: str, attempt_count: int) -> str:
        """
        Use Claude for empathetic, pedagogical hints.
        Memory: Remembers past hints to avoid repetition.
        """
        return await self._call_model(
            model="anthropic/claude-3-haiku-20240307",
            messages=[
                {
                    "role": "system",
                    "content": """You are an encouraging coding mentor helping a student who is stuck.

Rules:
- Give a brief, helpful hint (1-2 sentences max)
- Don't give away the answer
- Be encouraging and supportive
- If you've given similar hints before (check your memory), try a different approach
- Acknowledge their effort if they've been trying for a while"""
                },
                {
                    "role": "user",
                    "content": f"""The student's current code:
```
{code[:1500]}
```

Error/Issue: {error}

This is attempt #{attempt_count}. Please provide a helpful hint."""
                }
            ],
            memory_key="hints",  # Backboard remembers past hints for this user
            temperature=0.8,
            max_tokens=150
        )

    async def generate_encouragement(self, context: str) -> str:
        """Generate pure encouragement when user seems frustrated."""
        return await self._call_model(
            model="anthropic/claude-3-haiku-20240307",
            messages=[
                {
                    "role": "system",
                    "content": "You are a supportive coding mentor. Give a brief (1 sentence) word of encouragement. Be genuine, not cheesy."
                },
                {
                    "role": "user",
                    "content": f"Context: {context}"
                }
            ],
            temperature=0.9,
            max_tokens=50
        )

    # =========================================================================
    # CODE ANALYSIS - GPT-4o (strong code understanding)
    # =========================================================================

    async def analyze_code_error(self, code: str, error: str) -> dict:
        """
        Use GPT-4o for detailed technical code analysis.
        Returns structured analysis of the error.
        """
        response = await self._call_model(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Analyze the code error. Return valid JSON only with this structure:
{
  "error_type": "syntax|runtime|logic|type",
  "root_cause": "brief explanation",
  "affected_lines": "line numbers or description",
  "severity": 1-5,
  "category": "null_reference|off_by_one|type_mismatch|syntax|other"
}"""
                },
                {
                    "role": "user",
                    "content": f"Code:\n```\n{code[:2000]}\n```\n\nError: {error}"
                }
            ],
            temperature=0.3,  # Lower temperature for structured output
            max_tokens=200
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error_type": "unknown", "root_cause": response, "severity": 3}

    async def suggest_fix(self, code: str, error: str) -> str:
        """
        Use GPT-4o to suggest a specific fix without giving full solution.
        """
        return await self._call_model(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Suggest a specific fix for this code issue. Be concise (2-3 sentences). Point to the exact location and what needs to change, but don't write the full corrected code."
                },
                {
                    "role": "user",
                    "content": f"```\n{code[:2000]}\n```\n\nError: {error}"
                }
            ],
            temperature=0.5,
            max_tokens=150
        )

    # =========================================================================
    # PROFILE SUMMARIZATION - Gemini (structured analysis)
    # =========================================================================

    async def summarize_radar_profile(self, radar: dict, recent_events: list) -> str:
        """
        Use Gemini for structured profile summarization.
        Memory: Tracks how profile has evolved over time.
        """
        return await self._call_model(
            model="google/gemini-1.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": f"""Summarize this developer's coding style based on their radar profile and recent behavior.

Radar Profile (scores 0-1):
{json.dumps(radar, indent=2)}

Recent Events (last 10):
{json.dumps(recent_events[-10:], indent=2, default=str)}

Provide:
1. Their strongest trait (1 sentence)
2. Area for growth (1 sentence)
3. How their style compares to their previous sessions (if you remember them)

Keep it concise and actionable."""
                }
            ],
            memory_key="profile_history",  # Remember past summaries
            temperature=0.6,
            max_tokens=200
        )

    async def generate_archetype_description(self, archetype: str, radar: dict) -> str:
        """Generate personalized archetype description based on actual scores."""
        return await self._call_model(
            model="google/gemini-1.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": f"""The developer has been classified as: "{archetype}"

Their radar scores: {json.dumps(radar, indent=2)}

Write a 2-sentence personalized description of their engineering style that reflects their actual scores. Be specific, not generic."""
                }
            ],
            temperature=0.7,
            max_tokens=100
        )

    # =========================================================================
    # JOB PARSING - Cohere Command (efficient extraction)
    # =========================================================================

    async def parse_job_requirements(self, job_description: str) -> dict:
        """
        Use Cohere Command for efficient job description parsing.
        Extracts ideal candidate radar profile from text.
        """
        response = await self._call_model(
            model="cohere/command-r",
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract the ideal candidate profile from this job description.

Job Description:
{job_description[:2000]}

Return valid JSON with scores 0.0-1.0 for each dimension:
{{
  "verification": 0.X,    // Testing mindset importance
  "velocity": 0.X,        // Speed of delivery importance
  "optimization": 0.X,    // Algorithmic efficiency importance
  "decomposition": 0.X,   // Code modularity importance
  "debugging": 0.X        // Error resolution importance
}}

Base scores on explicit and implicit requirements in the description."""
                }
            ],
            temperature=0.3,
            max_tokens=150
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Default balanced profile
            return {
                "verification": 0.5,
                "velocity": 0.5,
                "optimization": 0.5,
                "decomposition": 0.5,
                "debugging": 0.5
            }

    async def explain_job_match(self, candidate_radar: dict, job_radar: dict, fit_score: float) -> str:
        """Explain why a candidate matches (or doesn't match) a job."""
        return await self._call_model(
            model="cohere/command-r",
            messages=[
                {
                    "role": "user",
                    "content": f"""Candidate radar: {json.dumps(candidate_radar)}
Job requirements: {json.dumps(job_radar)}
Match score: {fit_score:.0%}

Explain in 1-2 sentences why this candidate does/doesn't match this role. Be specific about which dimensions align or differ."""
                }
            ],
            temperature=0.5,
            max_tokens=100
        )

    # =========================================================================
    # ADAPTIVE INTERVENTION - Intelligent model routing
    # =========================================================================

    async def adaptive_intervention(self, session_context: dict) -> dict:
        """
        Intelligently choose intervention type and model based on context.
        This is the "adaptive" part that makes decisions based on user state.
        """
        code = session_context.get("code", "")
        last_error = session_context.get("last_error")
        error_streak = session_context.get("error_streak", 0)
        time_stuck_ms = session_context.get("time_stuck_ms", 0)
        attempt_count = session_context.get("attempt_count", 1)

        # Decision tree for intervention type
        if error_streak >= 3 and last_error:
            # Technical stuck - use GPT for analysis + Claude for delivery
            analysis = await self.analyze_code_error(code, last_error)
            hint = await self.generate_hint(code, last_error, attempt_count)

            return {
                "type": "technical_hint",
                "analysis": analysis,
                "hint": hint,
                "model_used": ["gpt-4o-mini", "claude-3-haiku"]
            }

        elif time_stuck_ms > 180000:  # 3+ minutes without progress
            # Might need encouragement or different approach
            hint = await self.generate_hint(
                code,
                "User seems stuck (no progress for 3 minutes)",
                attempt_count
            )
            encouragement = await self.generate_encouragement(
                f"User has been working for {time_stuck_ms // 60000} minutes"
            )

            return {
                "type": "encouragement",
                "hint": hint,
                "encouragement": encouragement,
                "model_used": ["claude-3-haiku"]
            }

        elif error_streak >= 2:
            # Early intervention - quick hint
            hint = await self.generate_hint(code, last_error or "struggling", attempt_count)

            return {
                "type": "gentle_nudge",
                "hint": hint,
                "model_used": ["claude-3-haiku"]
            }

        return {"type": "none"}

    # =========================================================================
    # MEMORY MANAGEMENT
    # =========================================================================

    async def get_user_memory(self, memory_key: str) -> dict:
        """Fetch user's adaptive memory from Backboard."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKBOARD_BASE_URL}/memory/{self.user_id}:{memory_key}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if response.status_code == 200:
                return response.json()
            return {}

    async def clear_user_memory(self, memory_key: str):
        """Clear a specific memory key for the user."""
        async with httpx.AsyncClient() as client:
            await client.delete(
                f"{BACKBOARD_BASE_URL}/memory/{self.user_id}:{memory_key}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
```

### 10.4 Integration with AI Worker

**Update:** `apps/api/services/ai_worker.py`

```python
from services.backboard import BackboardService

async def trigger_analysis(session_id: str, user_id: str):
    """
    Use Backboard for adaptive, multi-model analysis.
    This replaces direct OpenAI calls with intelligent model routing.
    """
    # Initialize Backboard with user context (enables memory)
    backboard = BackboardService(user_id)

    # Fetch session context
    session = await sessions_collection.find_one({"session_id": session_id})
    recent_events = await events_collection.find(
        {"session_id": session_id}
    ).sort("timestamp", -1).limit(10).to_list(10)

    if not session or not recent_events:
        return

    # Build context for adaptive intervention
    error_events = [e for e in recent_events if e.get("event_type") == "error_emitted"]

    session_context = {
        "code": session.get("current_code_snapshot", ""),
        "last_error": error_events[0].get("properties", {}).get("error_message") if error_events else None,
        "error_streak": len(error_events),
        "time_stuck_ms": calculate_time_stuck(recent_events),
        "attempt_count": session.get("ai_context", {}).get("intervention_count", 0) + 1
    }

    # Adaptive intervention - Backboard chooses the right model(s)
    intervention = await backboard.adaptive_intervention(session_context)

    if intervention["type"] != "none":
        # Update session with intervention
        await sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {
                "ai_context.is_stuck": True,
                "ai_context.last_hint": intervention.get("hint"),
                "ai_context.intervention_type": intervention["type"],
                "ai_context.models_used": intervention.get("model_used", []),
                "ai_context.analysis": intervention.get("analysis")
            }, "$inc": {"ai_context.intervention_count": 1}}
        )

        # Store intervention for effectiveness tracking
        await interventions_collection.insert_one({
            "session_id": session_id,
            "user_id": user_id,
            "triggered_at": datetime.utcnow(),
            "intervention_type": intervention["type"],
            "models_used": intervention.get("model_used", []),
            "hint_text": intervention.get("hint"),
            "analysis": intervention.get("analysis"),
            "acknowledged": False
        })

    # Update radar profile using Gemini for summarization
    if len(recent_events) >= 5:
        user = await users_collection.find_one({"_id": user_id})
        if user and user.get("radar_profile"):
            summary = await backboard.summarize_radar_profile(
                user["radar_profile"],
                recent_events
            )
            await users_collection.update_one(
                {"_id": user_id},
                {"$set": {"radar_summary": summary}}
            )


def calculate_time_stuck(events: list) -> int:
    """Calculate milliseconds since last successful action."""
    if not events:
        return 0

    # Find last success (passed run or meaningful code change)
    for event in events:
        if event.get("event_type") == "run_attempted":
            if event.get("properties", {}).get("passed"):
                return int((datetime.utcnow() - event["timestamp"]).total_seconds() * 1000)

    # No success found, calculate from first event
    return int((datetime.utcnow() - events[-1]["timestamp"]).total_seconds() * 1000)
```

### 10.5 Backboard.io Judging Criteria Alignment

| Criteria | How SkillPulse Addresses It |
|----------|----------------------------|
| **Adaptive Memory** | Remembers past hints per user, tracks profile evolution, avoids repetition |
| **Model Switching** | 4 models: Claude (hints), GPT-4o (code), Gemini (summary), Cohere (parsing) |
| **Framework** | Uses Backboard.io API for unified access |
| **User Experience** | Personalized hints that get smarter over time |
| **Technical Implementation** | Clean service abstraction, intelligent routing logic |

---

## 11. Amplitude Integration: Self-Improving Product Loop

### 11.1 How SkillPulse Fulfills Amplitude Criteria

The entire SkillPulse platform is built around Amplitude's "data → insights → action" loop:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AMPLITUDE SELF-IMPROVING LOOP                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   DATA (Behavioral Events)                                                   │
│   ├── session_started, code_changed, run_attempted                          │
│   ├── error_emitted, fix_applied, task_submitted                            │
│   ├── semantic_block_added, library_import                                  │
│   └── hint_displayed, hint_acknowledged                                     │
│                          │                                                   │
│                          ▼                                                   │
│   INSIGHTS (AI Analysis)                                                     │
│   ├── Frustration detection (error streaks, time stuck)                     │
│   ├── Engineering DNA radar (verification, velocity, etc.)                  │
│   ├── Archetype classification (fast_iterator, careful_tester)              │
│   └── Job fit scoring (cosine similarity on radar vectors)                  │
│                          │                                                   │
│                          ▼                                                   │
│   ACTION (Product Changes)                                                   │
│   ├── Dynamic hints when stuck (not hardcoded tooltips)                     │
│   ├── Radar profile updates in real-time                                    │
│   ├── Job unlocks as skills improve                                         │
│   └── Personalized archetype descriptions                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Event Schema (Amplitude-Style)

Our event schema mirrors real product analytics:

```javascript
// Example events sent to Amplitude
{
  "event_type": "run_attempted",
  "user_id": "user_123",
  "time": 1705420800000,
  "event_properties": {
    "session_id": "sess_abc",
    "task_id": "bugfix-null-check",
    "result": "fail",
    "tests_passed": 2,
    "tests_total": 4,
    "runtime_ms": 145,
    "error_type": "TypeError"
  },
  "user_properties": {
    "$set": {
      "archetype": "careful_tester",
      "radar_verification": 0.8,
      "radar_velocity": 0.6,
      "total_sessions": 15
    }
  }
}
```

### 11.3 AI Beyond Rules (Key Differentiator)

**What rules can do:**
```python
# Basic if/else
if error_count >= 3:
    show_tooltip("Check your syntax!")
```

**What our AI does:**
```python
# AI-powered (via Backboard multi-model)
recent_events = get_last_10_events(session_id)
frustration = detect_frustration_patterns(recent_events)  # Pattern analysis
hint = await backboard.generate_hint(code, error, attempt_count)  # LLM generation
# Hint is contextual, remembers past hints, adapts to user's style
```

### 11.4 Amplitude Dashboard Recommendations

For the demo, set up these Amplitude views:

1. **Event Stream**: Show live events flowing in during coding
2. **User Funnel**: `session_started` → `run_attempted` → `task_submitted`
3. **Cohort by Archetype**: Compare behavior of `fast_iterator` vs `careful_tester`
4. **Retention by Hint Effectiveness**: Users who acknowledged hints vs ignored

### 11.5 Amplitude Judging Criteria Alignment

| Criteria | How SkillPulse Addresses It |
|----------|----------------------------|
| **Behavioral Data (25%)** | 12+ event types with rich properties, user journey tracking |
| **AI Application (25%)** | Multi-model LLM analysis, frustration detection, personalized hints |
| **Product Impact (25%)** | Real recruiter workflow, candidate experience improvement |
| **Innovation (15%)** | Video analysis + behavioral data + multi-model AI combined |
| **Execution (10%)** | Working prototype with clear data flow demonstration |

---

## 12. Updated Implementation Phases

### Phase 1: Core AI Worker (Priority)
- [x] FastAPI backend structure
- [x] Event tracking endpoints
- [x] MongoDB integration
- [ ] Create `services/backboard.py` with multi-model support
- [ ] Create `services/ai_worker.py` with frustration detection
- [ ] Create `/radar/{user_id}` endpoint
- [ ] Add `ai_context` fields to sessions collection

### Phase 2: TwelveLabs Video
- [ ] Create `services/twelvelabs.py`
- [ ] Implement video upload → indexing flow
- [ ] Add semantic search endpoint
- [ ] Generate interview summaries and highlights
- [ ] Integrate video insights into passport

### Phase 3: Frontend Hints & Radar
- [ ] Create `HintPanel` component
- [ ] Add `useRadar` hook with polling
- [ ] Integrate hint display into sandbox page
- [ ] Create radar chart visualization (Recharts)
- [ ] Track hint acknowledgment events

### Phase 4: Recruiter Video Experience
- [ ] Video player with timestamp navigation
- [ ] Search box for semantic video search
- [ ] Highlight clips display
- [ ] Communication analysis display

### Phase 5: Polish & Demo
- [ ] Seed demo data
- [ ] Test full flow: code → events → hints → radar → video → recruiter
- [ ] Prepare demo script for each sponsor track

---

## 13. Complete Environment Variables

```env
# apps/api/.env

# ============ EXISTING ============
# MongoDB Atlas (MLH Track)
MONGODB_URI=op://hackathon/mongodb/connection_string

# JWT Auth
JWT_SECRET=op://hackathon/app/jwt_secret
JWT_ALGORITHM=HS256

# Sandbox Runner
SANDBOX_RUNNER_URL=http://sandbox-runner:8080

# ============ AMPLITUDE ============
AMPLITUDE_API_KEY=op://hackathon/amplitude/api_key

# ============ TWELVELABS ============
TWELVELABS_API_KEY=op://hackathon/twelvelabs/api_key
TWELVELABS_INDEX_ID=your-index-id-here

# ============ BACKBOARD.IO ============
# Register at backboard.io/hackathons with code UOFTHACKS26 for $10 credit
BACKBOARD_API_KEY=op://hackathon/backboard/api_key

# ============ AI SETTINGS ============
AI_HINT_ENABLED=true
FRUSTRATION_THRESHOLD_ERRORS=3
FRUSTRATION_THRESHOLD_TIME_MS=120000
```

---

## 14. Demo Script for Judges

### Opening (15 seconds)
> "SkillPulse is an AI-powered technical interview platform that analyzes HOW you code, not just whether your code works. We're competing in three sponsor tracks: Amplitude, TwelveLabs, and Backboard.io."

### Amplitude Demo (45 seconds)
> "Watch the Engineering DNA radar update in real-time as I code. [Start coding task, make intentional errors]
>
> After 3 similar errors, our AI detects frustration. But this isn't a hardcoded tooltip—it's Claude analyzing my specific code through Backboard's API and generating a contextual hint.
>
> [Show hint appearing] Notice it remembers I saw a similar hint earlier and tries a different approach. That's adaptive memory.
>
> [Show Amplitude dashboard] Events are streaming to Amplitude: run_attempted, error_emitted, hint_displayed. This is the self-improving loop."

### TwelveLabs Demo (30 seconds)
> "Candidates can record their interview. Here's one I uploaded earlier.
>
> [Type in search box] 'When did they discuss their testing approach?'
>
> [Show results] TwelveLabs found the exact moment at 2:34. Click to jump there.
>
> [Show summary] It also auto-generated a summary and highlight reel for recruiters."

### Backboard Demo (30 seconds)
> "We use 4 different AI models through Backboard's single API:
> - Claude for empathetic hints
> - GPT-4o for code analysis
> - Gemini for profile summaries
> - Cohere for job parsing
>
> [Show intervention with multiple models] This hint used GPT to analyze the error, then Claude to write the message. Backboard's memory ensures we don't repeat advice."

### Closing (15 seconds)
> "SkillPulse: behavioral analytics meet multi-model AI to build interviews that understand how you think, not just what you type."

---

*Document Version: 2.0*
*Last Updated: January 2026*
*UofTHacks 2026 - SkillPulse Team*
*Sponsor Tracks: Amplitude, TwelveLabs, Backboard.io*
