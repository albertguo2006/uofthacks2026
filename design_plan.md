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
