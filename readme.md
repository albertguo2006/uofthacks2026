```md
# Proof of Skill — Identity-First Freelance Marketplace (No Resumes)

**Theme: Identity**  
Your professional identity shouldn’t be self-reported (“I’m senior”), it should be **behavioral proof**: how you work, how you debug, how you communicate, and how you improve over time.

**Proof of Skill** is a freelance marketplace where:
- Candidates build a **Skill Identity** by completing real tasks inside an in-app sandbox.
- Recruiters see a **Skill Passport** backed by evidence (event traces + interview video moments).
- Premium jobs “unlock” **in real time** when your identity evolves.

---

## Sponsor tracks (limit 3): recommended stack

### ✅ Best fit for Idea 1: **Amplitude + TwelveLabs + 1Password**
- **Amplitude**: Track product-style behavioral events and use AI to produce insights/actions beyond if/else logic (explicit judging emphasis). :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}  
- **TwelveLabs**: Core functionality driven by video understanding (search/summarize/analyze interview recordings). :contentReference[oaicite:2]{index=2}  
- **1Password**: Security that’s simple + honest + people-first; optional passkeys/auth “extra mile.” :contentReference[oaicite:3]{index=3}  

### Why not Shopify for this idea
Shopify’s challenge is explicitly commerce/merchant value. :contentReference[oaicite:4]{index=4}  
You *could* contort Proof of Skill into “hire devs for merchants,” but it weakens the core identity story.

> Alternative (only if you drop TwelveLabs): **Amplitude + Backboard + 1Password**  
Backboard wants adaptive memory + model switching via its API. :contentReference[oaicite:5]{index=5}  
It’s a strong fit for “identity over time,” but you lose the video-wow factor that TwelveLabs gives you.

---

## Product overview

### Candidate experience (Identity you can’t fake)
1. Pick a task (bugfix, refactor, UI tweak, micro-design challenge).
2. Work inside an embedded sandbox (code editor / design canvas).
3. The app streams behavioral events to Amplitude (and stores locally for ML).
4. AI builds a **Skill Identity Vector** + **Skill Passport** with evidence.
5. Job feed updates in real time: higher-tier gigs unlock when fit probability crosses thresholds.

### Recruiter experience (Trustable signal, fast)
- Browse candidates by **Skill Identity** (not resumes).
- Review:
  - “How they worked” (behavioral signature)
  - “How they communicate” (TwelveLabs video moments + summary)
  - Evidence links (event highlights + video timestamps)
- Invite to a short video interview; results update the passport automatically.

---

## What makes this “Identity”-native (not bolted on)
We define “identity” as:
- **Behavioral Identity**: how you solve problems (events inside sandbox)
- **Communication Identity**: how you explain and collaborate (video understanding)
- **Integrity Identity**: how trustworthy the signal is (anti-cheat + transparent security posture)

---

## Architecture

```

┌───────────────────────────────┐
│  Next.js Web App              │
│  - Sandbox (Monaco/Canvas)    │
│  - Job Feed + Passport UI     │
│  - Video Upload UI            │
└───────────────┬───────────────┘
│ POST /track, /video
▼
┌───────────────────────────────┐
│  FastAPI Backend              │
│  - Event ingestion            │
│  - Feature extraction         │
│  - SkillGraph ML service      │
│  - Job matching API           │
│  - TwelveLabs pipeline        │
│  - Amplitude forwarding       │
└───────┬───────────────┬───────┘
│               │
│               │
▼               ▼
┌──────────────┐   ┌───────────────────┐
│ SQLite/PG    │   │ TwelveLabs         │
│ events store │   │ video index/search │
└──────────────┘   └───────────────────┘
│
▼
┌───────────────────────────────┐
│ Amplitude                     │
│ - behavioral event schema      │
│ - cohorts/funnels for demo     │
│ - user properties: skill_*     │
└───────────────────────────────┘

```

---

## Core loop (Amplitude judging alignment)

Amplitude’s challenge is “events → AI → visible change,” with AI doing something beyond rules. :contentReference[oaicite:6]{index=6} :contentReference[oaicite:7]{index=7}

Our loop:
1. **Observe**: capture granular behavioral events (not keystrokes; *signals*).
2. **Learn**: ML clusters + predicts skill vectors from behavior sequences.
3. **Act**: job feed unlocks + coaching + recruiter-facing passport updates.

---

## Repo structure

```

proof-of-skill/
apps/
web/                 # Next.js UI
api/                 # FastAPI backend
packages/
telemetry/           # client-side tracking SDK
skillgraph/          # ML + feature extraction
data/
jobs.json            # job definitions + target vectors
scripts/
seed_demo_data.py    # generates demo events + sample passports
docker-compose.yml
README.md

````

---

## Event schema (behavioral proof)

### Identity primitives
- `user_id`: candidate id (UUID)
- `session_id`: sandbox attempt id (UUID)
- `task_id`: canonical task identifier
- `artifact_id`: code snapshot hash / design file hash

### High-signal events
| Event | Purpose | Example properties |
|------|---------|--------------------|
| `task_started` | session boundary | `task_id`, `difficulty` |
| `editor_command` | “how you work” | `command` (format/refactor/find), `source` (shortcut/menu) |
| `run_attempted` | iteration behavior | `result` (pass/fail), `runtime_ms` |
| `error_emitted` | debugging signal | `error_type`, `stack_depth`, `is_repeat` |
| `fix_applied` | time-to-fix | `from_error_type`, `time_since_error_ms` |
| `refactor_applied` | craftsmanship | `kind` (extract fn/rename), `loc_changed` |
| `test_added` | reliability | `count`, `scope` |
| `paste_burst_detected` | integrity | `chars_pasted`, `burst_ms` |
| `task_submitted` | outcome | `score_raw`, `passed` |
| `interview_uploaded` | video pipeline start | `video_id` |
| `interview_insight_ready` | video pipeline done | `clarity_score`, `highlights_count` |

---

## SkillGraph (AI that is not a rules engine)

### 1) Feature extraction (per session)
We derive a compact feature vector from the event stream, e.g.:
- **Iteration velocity**: runs/hour, average time between run attempts
- **Debug efficiency**: mean time-to-fix by error class; repeat-error rate
- **Craftsmanship**: refactor frequency normalized by LOC; test additions
- **Tool fluency**: shortcut ratio vs menu usage
- **Integrity signals**: paste burst density; suspicious timing anomalies

### 2) Unsupervised identity archetypes (KMeans)
We cluster users into behavioral archetypes (e.g., “Fast Iterators”, “Careful Testers”, “Refactor-First”) based on multi-session vectors.
- Output becomes `user_property: identity_archetype`

### 3) Predictive job-fit model (lightweight)
We map:
- `candidate_vector` (learned)
- `job_target_vector` (defined in `jobs.json`)
to a **fit probability** via logistic regression / gradient boosting.

### 4) Explainability layer (LLM optional)
We generate a concise “Skill Passport” explanation referencing evidence:
- top contributing features
- notable sessions
- (and video highlights if present)

This can be done with a small prompt + deterministic feature attribution, but it’s optional for sponsor alignment.

---

## Real-time “job reveal” mechanic

Each job has:
- `tier`: 0/1/2 (hidden tiers)
- `min_fit_prob`: threshold
- `must_have`: constraints (e.g., integrity score, communication score)

API behavior:
- `/jobs` returns only jobs where `fit_prob >= min_fit_prob`
- When the model updates after a run/fix/refactor burst, the UI re-queries and new jobs appear.

---

## TwelveLabs integration: interview understanding

TwelveLabs encourages apps where core functionality uses their video understanding endpoints. :contentReference[oaicite:8]{index=8}  
We use it to build **Communication Identity** from interview video.

### What we extract
1. **Auto summary** (what they said + how they framed tradeoffs)
2. **Highlights** (exact moments where they explain tradeoffs, ownership, teamwork)
3. **Semantic search** (recruiter can ask: “when did they mention testing?” and jump to the moment)

TwelveLabs concepts:
- Indexes organize videos. :contentReference[oaicite:9]{index=9}  
- Videos must be uploaded/indexed before search; search returns matching segments. :contentReference[oaicite:10]{index=10}  
- Official SDK initialization + index creation is straightforward. :contentReference[oaicite:11]{index=11}  

---

## Security (1Password): secrets + recruiter auth

1Password asks for simple, honest, people-first security; passkeys/auth as “extra mile.” :contentReference[oaicite:12]{index=12}  

### Minimum (required)
- Store `AMPLITUDE_API_KEY`, `TWELVELABS_API_KEY`, `JWT_SECRET` in 1Password.
- Use `op run` with an env file of secret references (no plaintext secrets in repo). 1Password documents this pattern. :contentReference[oaicite:13]{index=13}  

### Extra mile
- Recruiter dashboard gated behind passkey login (WebAuthn).
- “Security transparency” panel:
  - what is collected (aggregates, not keystrokes)
  - how long it’s stored
  - how to delete data

---

# Implementation

## Tech stack
- Web: Next.js + Monaco Editor (code), optional Fabric.js (design)
- API: FastAPI (Python)
- ML: scikit-learn (KMeans + logistic regression), optional SHAP-like attribution
- Storage: SQLite (hackathon), upgradeable to Postgres
- Video: TwelveLabs Python SDK
- Analytics: Amplitude HTTP v2 events + Identify updates

---

## Setup

### 0) Prereqs
- Node 18+
- Python 3.10+
- 1Password CLI (optional but recommended)

### 1) Install
```bash
# web
cd apps/web
npm i

# api
cd ../api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
````

### 2) Secrets via 1Password (recommended)

Create `prod.env` with **secret references**:

```env
AMPLITUDE_API_KEY=op://hackathon/amplitude/api_key
TWELVELABS_API_KEY=op://hackathon/twelvelabs/api_key
JWT_SECRET=op://hackathon/app/jwt_secret
```

Run both services with `op run`:

```bash
op run --env-file=prod.env -- bash -lc "cd apps/api && uvicorn main:app --reload"
# in another terminal
op run --env-file=prod.env -- bash -lc "cd apps/web && npm run dev"
```

(1Password’s docs describe `op run` + env files as the standard way to provision secrets. ([1Password Developer][1]))

### 3) Amplitude project

We forward events using **HTTP v2** (`POST https://api2.amplitude.com/2/httpapi`). ([Amplitude][2])

* Create an Amplitude project
* Copy the project API key into 1Password

### 4) TwelveLabs

* Create a TwelveLabs account + API key
* The SDK basic flow is “create index → upload video → analyze/search.” ([GitHub][3])

---

## Key code: telemetry (client)

`packages/telemetry/track.ts`

```ts
export async function track(eventType: string, payload: Record<string, any>) {
  await fetch("/api/track", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_type: eventType,
      time: Date.now(),
      ...payload,
    }),
  });
}
```

Example usage in Monaco editor handlers:

```ts
track("editor_command", {
  user_id,
  session_id,
  task_id,
  command: "format_document",
  source: "shortcut",
});
```

---

## Key code: backend event ingestion + Amplitude forward

`apps/api/routes/track.py`

```py
from fastapi import APIRouter
from pydantic import BaseModel
import os, requests

AMPLITUDE_API_KEY = os.environ["AMPLITUDE_API_KEY"]
AMPLITUDE_HTTP_V2 = "https://api2.amplitude.com/2/httpapi"  # per docs :contentReference[oaicite:17]{index=17}

router = APIRouter()

class TrackEvent(BaseModel):
    event_type: str
    time: int
    user_id: str
    session_id: str | None = None
    task_id: str | None = None
    event_properties: dict = {}

@router.post("/track")
def track_event(evt: TrackEvent):
    # 1) store locally (SQLite/PG) for ML
    # db.insert(evt.dict())

    # 2) forward to Amplitude for sponsor-track visibility
    requests.post(AMPLITUDE_HTTP_V2, json={
        "api_key": AMPLITUDE_API_KEY,
        "events": [{
            "user_id": evt.user_id,
            "event_type": evt.event_type,
            "time": evt.time,
            "event_properties": {
                **evt.event_properties,
                "session_id": evt.session_id,
                "task_id": evt.task_id
            }
        }]
    }, timeout=5)

    return {"ok": True}
```

---

## Key code: SkillGraph (features → identity → job fit)

`packages/skillgraph/compute.py`

```py
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression

# In hackathon mode, train on seeded demo data at startup.
kmeans = KMeans(n_clusters=4, random_state=7)
clf = LogisticRegression(max_iter=1000)

def session_features(events: list[dict]) -> np.ndarray:
    # Minimal example; expand with your real signals
    shortcut = sum(1 for e in events if e["event_type"] == "editor_command" and e["event_properties"].get("source") == "shortcut")
    menu = sum(1 for e in events if e["event_type"] == "editor_command" and e["event_properties"].get("source") == "menu")
    errors = sum(1 for e in events if e["event_type"] == "error_emitted")
    fixes = sum(1 for e in events if e["event_type"] == "fix_applied")
    paste = sum(1 for e in events if e["event_type"] == "paste_burst_detected")
    return np.array([
        shortcut / max(1, shortcut + menu),
        fixes / max(1, errors),
        paste,
    ], dtype=float)

def compute_identity(user_sessions: list[list[dict]]) -> dict:
    X = np.vstack([session_features(s) for s in user_sessions])
    avg = X.mean(axis=0)

    archetype = int(kmeans.predict([avg])[0])
    # fit probability against a job can be done by clf or cosine similarity
    return {
        "identity_archetype": archetype,
        "skill_vector": avg.tolist()
    }
```

---

## Key code: job matching + reveal

`apps/api/routes/jobs.py`

```py
import json, numpy as np
from fastapi import APIRouter

router = APIRouter()
JOBS = json.load(open("data/jobs.json"))

def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(a.dot(b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

@router.get("/jobs")
def jobs(user_skill_vector: list[float]):
    visible = []
    for job in JOBS:
        fit = cosine(user_skill_vector, job["target_vector"])
        if fit >= job["min_fit"]:
            visible.append({**job, "fit": fit})
    return {"jobs": sorted(visible, key=lambda j: -j["fit"])}
```

---

## TwelveLabs: index + upload + search highlights

Using the official Python SDK initialization + index creation pattern (per SDK docs). ([GitHub][3])

`apps/api/video/twelvelabs_pipeline.py`

```py
import os
from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem

client = TwelveLabs(api_key=os.environ["TWELVELABS_API_KEY"])

def ensure_index(index_name: str) -> str:
    # Create once; cache ID in DB
    idx = client.indexes.create(
        index_name=index_name,
        models=[
            IndexesCreateRequestModelsItem(model_name="marengo3.0", model_options=["visual", "audio"]),
            IndexesCreateRequestModelsItem(model_name="pegasus1.2", model_options=["visual", "audio"]),
        ],
    )
    return idx.id

def upload_and_index(index_id: str, video_path: str) -> str:
    task = client.tasks.create(index_id=index_id, file=video_path)
    # Poll until ready; store task/video IDs
    return task.id

def recruiter_highlights(index_id: str, query: str):
    # Search returns matching segments after indexing completes. :contentReference[oaicite:19]{index=19}
    return client.search.query(index_id=index_id, query=query, options=["visual", "audio"])
```

Example recruiter queries:

* “moment they explain a tradeoff”
* “where they mention testing”
* “where they talk about collaborating or disagreement”

The returned segments are rendered as clickable timestamps in the recruiter UI.

---

## Updating Amplitude user properties (Skill Passport fields)

We push derived identity values back so Amplitude charts/cohorts can use them.

Option A: send `$identify` event (common pattern) ([Postman][4])
Option B: use Identify API directly ([Amplitude][5])

Hackathon-simple: `$identify` event alongside normal events.

---

## Demo flow (what judges see in 2 minutes)

1. Candidate starts a task → events stream
2. Candidate hits errors → fixes → refactors → reruns tests
3. Skill Passport updates live:

   * archetype
   * integrity score
   * “debug efficiency” improvements
4. A Tier-2 job suddenly appears (“unlocked”)
5. Recruiter opens candidate → sees:

   * evidence-backed passport
   * interview highlight clips (TwelveLabs search)
6. Security panel shows:

   * “secrets from 1Password”
   * recruiter access gate (optional passkey)

---

# Deliverables checklist (sponsor-track focused)

## Amplitude

* Clear event taxonomy + properties 
* Demonstrate AI doing substantive work (clustering/prediction) 
* Show visible product change (job unlock / coaching) 

## TwelveLabs

* Core workflow uses video understanding endpoints for search/summary/highlights 

## 1Password

* Simple + honest security UX + secrets management; passkeys/auth stretch 

---

## Notes on privacy & fairness (helps judging)

* Collect aggregates/signals, not raw keystrokes.
* Provide “why you got this identity” evidence links.
* Allow opt-out of video analysis; show what’s stored.
* Integrity signals are used to protect users from fraud, not to punish honest mistakes.

---

## Appendix: example `jobs.json`

```json
[
  {
    "job_id": "tier1-landing-page",
    "tier": 1,
    "title": "Build a marketing landing page (Next.js)",
    "min_fit": 0.55,
    "target_vector": [0.6, 0.5, 0.0]
  },
  {
    "job_id": "tier2-refactor-billing",
    "tier": 2,
    "title": "Refactor a billing service + add tests",
    "min_fit": 0.72,
    "target_vector": [0.7, 0.8, 0.0]
  }
]
```

---

## Appendix: seeded demo data

Use `scripts/seed_demo_data.py` to generate:

* 20 synthetic candidates with distinct archetypes
* 1–2 interview videos per candidate (or placeholders)
* enough events to populate Amplitude charts for judging

```

## If you want this README to map exactly to your team’s preferred stack
You can keep the README structure and swap:
- FastAPI → Node/Express
- Next.js → Remix
- SQLite → Supabase/Postgres

The sponsor-track mechanics (event schema + TwelveLabs + 1Password) remain unchanged.

::contentReference[oaicite:27]{index=27}
```

[1]: https://developer.1password.com/docs/cli/secrets-environment-variables/ "Load secrets into the environment | 1Password Developer"
[2]: https://amplitude.com/docs/apis/analytics/http-v2 "HTTP V2 API | Amplitude"
[3]: https://github.com/twelvelabs-io/twelvelabs-python "GitHub - twelvelabs-io/twelvelabs-python: Official TwelveLabs SDK for Python"
[4]: https://www.postman.com/amplitude-dev-docs/amplitude-developers/request/85hrvvv/http-api-identify?utm_source=chatgpt.com "HTTP API $identify | Amplitude Analytics APIs"
[5]: https://amplitude.com/docs/apis/analytics/identify?utm_source=chatgpt.com "Identify API"
