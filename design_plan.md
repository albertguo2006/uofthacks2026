# UofTHacks 2026 - Amplitude Technical Challenge

**Concept:** A self-improving recruitment platform using Behavioral Analytics & AI.

---

## 1. Executive Summary

**SkillPulse** is an AI-powered technical interview platform that moves beyond binary "Pass/Fail" metrics. It treats the coding interview as a data stream, analyzing **how** a candidate engineers a solution (testing habits, debugging efficiency, optimization patterns), rather than just the final output.

### The “Amplitude Loop” (Data → Insight → Action)

1. **Data:** Track granular **semantic events** (e.g., `test_case_added`, `refactor_start`) instead of just keystrokes.
2. **Insight:** An asynchronous AI Worker analyzes these patterns to build a live **Engineering DNA Radar Chart**.
3. **Action:**

   * **Self-Improving Candidate Experience:** Detect frustration and dynamically intervene with hints to prevent churn.
   * **Smart Employer Matching:** Match candidates to jobs using vector similarity on behavioral profiles, not just keywords.

---

## 2. System Architecture

### Tech Stack

* **Frontend:** Next.js (React), Tailwind CSS, Monaco Editor, Recharts
* **Backend API:** Node.js (Express)
* **Database:** MongoDB Atlas (document store for flexible event schemas)
* **Async Queue:** BullMQ (Redis)
* **AI Engine:** OpenAI GPT-4o (via LangChain or direct API)
* **Code Execution:** Piston API (public sandbox)
* **Analytics:** Amplitude Browser SDK (source of truth)

### Architecture Flow

1. **Frontend (Next.js)** captures events
2. **API Gateway** ingests events → **MongoDB** (log) + **Redis** (queue)
3. **AI Worker** processes queue → updates **User Profile** (radar)
4. **Frontend** polls for radar updates + AI interventions (hints)

---

## 3. Data Design (MongoDB Schema)

### 3.1 `Users` Collection (The Profile)

Stores the "living" radar chart that updates after every session.

```javascript
{
  _id: ObjectId,
  name: "Alex Dev",
  role: "candidate", // or "employer"

  // The "Engineering DNA" Vector (0.0 to 1.0)
  radar_profile: {
    verification:   { score: 0.8, confidence: 0.9 }, // Testing mindset
    velocity:       { score: 0.6, confidence: 0.7 }, // Speed of delivery
    optimization:   { score: 0.3, confidence: 0.4 }, // Algorithmic efficiency
    decomposition:  { score: 0.9, confidence: 0.8 }  // Code modularity
  }
}
```

### 3.2 `Jobs` Collection (The Target)

Stores the "ideal candidate" shape derived from the job description.

```javascript
{
  _id: ObjectId,
  employer_id: ObjectId,
  title: "Senior Backend Engineer",
  description: "Must be reliable and write clean, tested code...",

  // Parsed by AI from the description above
  target_radar: {
    verification: 0.9, // High reliability needed
    velocity: 0.4,     // Speed less important
    optimization: 0.7
  }
}
```

### 3.3 `Sessions` Collection (The Event Stream)

Stores raw behavioral data for the current interview.

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  problem_id: "two_sum",
  status: "active",
  current_code_snapshot: "...",

  // AI Context for the "Self-Improving" Loop
  ai_context: {
    is_stuck: Boolean,
    intervention_count: 0
  }
}
```

---

## 4. Semantic Event Schema (Amplitude)

This schema is critical for the **Data** criteria. We track **intent**, not just clicks.

| Category | Event Name               | Trigger Logic                                 | Insight Derived                     |
| -------- | ------------------------ | --------------------------------------------- | ----------------------------------- |
| Thinking | `solution_draft_started` | User starts typing > 5s after page load       | Planning: did they read the prompt? |
| Thinking | `docs_lookup`            | Focus lost to documentation tab               | Resourcefulness                     |
| Coding   | `semantic_block_added`   | User defines a new function/class             | Decomposition: modular thinking     |
| Coding   | `library_import`         | User imports standard lib (e.g., collections) | Fluency                             |
| Verify   | `test_case_authored`     | User creates a custom input                   | Verification: proactive QA          |
| Verify   | `execution_error_streak` | 3+ errors of same type in 1 min               | Resilience / needs intervention?    |
| Optimize | `refactor_initiated`     | Editing code after passing tests              | Craftsmanship                       |

---

## 5. End-to-End Implementation Logic

### 5.1 Frontend: The "Smart IDE"

**Location:** `components/IdeEnvironment.tsx`

**Observer Hook:** Implement `useSemanticObserver`. It debounces keystrokes and runs regex checks to fire `semantic_block_added` only when valid code structures appear.

**Amplitude Sync:**

```javascript
const logEvent = (name, props) => {
  // 1) Send to backend for AI processing
  axios.post("/api/events/track", { name, props });

  // 2) Send to Amplitude for visualization
  amplitude.track(name, props);
};
```

**Live Radar:** Use SWR or polling to fetch `/api/radar/:userId` every 5s, then pass data to a Recharts Radar component.

---

### 5.2 Backend: The Ingestion API

**Location:** `pages/api/events/track.ts`

**Logic:**

1. Receive event
2. Save to MongoDB `event_logs`
3. Push job to Redis Queue: `behavior-analysis`
4. Return `200 OK` instantly (non-blocking)

---

### 5.3 Backend: The AI Worker (The "Brain")

**Location:** `workers/analyzer.ts`
**Trigger:** Consumes `behavior-analysis` jobs

**Step 1: Contextualize**
Fetch the last 10 events for this session.

**Step 2: Prompt LLM**

> User History: {last_10_events}
> Current Code: {code}
> Task:
>
> * Update the "Verification" and "Optimization" scores (0–1).
> * Is the user stuck? (True/False)
> * If stuck, generate a 1-sentence hint.

**Step 3: Update DB**
Update `Users.radar_profile` with the new scores.

**Step 4: Intervene**
If `stuck == true`, emit a WebSocket event `intervention` to the frontend.

---

### 5.4 Employer Portal: The Match Engine

**Location:** `pages/employer/dashboard.tsx`

**Vector Similarity Logic:**

```javascript
function cosineSimilarity(candidateA, targetB) {
  // Calculate dot product of the two radar vectors
  // Returns 0.0 to 1.0 (match percentage)
}
```

**UI:** Display candidates sorted by this score. Add a "Why?" tooltip, e.g., “Matches your requirement for high Optimization.”
