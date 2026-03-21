# Adaptive Routines -- Backend Specification (Hackathon)

A self-contained Python FastAPI backend that powers the Adaptive Routines app. Handles AI plan generation (two-tier), session management, reshuffle logic, and resilience scoring. Uses SQLite for storage and Google Gemini 3 Pro for LLM calls. Runs on localhost for the demo.

---

## 1. Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY="your-key-here"

# Run the server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## 2. Project Structure

```
backend/
├── main.py               # FastAPI app, CORS, lifespan, router registration
├── database.py           # SQLite + SQLModel engine/session setup
├── models.py             # SQLModel table models + Pydantic response schemas
├── llm.py                # Gemini 3 Pro API integration
├── prompts.py            # LLM prompt templates (high-level + monthly detail)
├── routers/
│   ├── plans.py          # Plan generation, listing, detail, monthly extension
│   ├── sessions.py       # Today view, complete, reshuffle, cascade, salvage
│   └── score.py          # Resilience score endpoint
├── seed.py               # Demo seed data script (run directly: python seed.py)
└── requirements.txt
```

---

## 3. Dependencies (`requirements.txt`)

```
fastapi
uvicorn[standard]
sqlmodel
httpx
python-dotenv
```

---

## 4. Configuration (`main.py` top-level)

```python
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.0-pro")
```

CORS must allow the Lovable frontend origin. For the demo, allow all origins:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 5. Database (`database.py`)

SQLite file stored at `backend/routines.db`. Use SQLModel with a single engine:

```python
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///routines.db"
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

Call `init_db()` in FastAPI's lifespan event. Also seed a default `UserProfile` row if none exists (id=1, resilience_score=0).

---

## 6. Data Models (`models.py`)

### 6.1 Table Models

```python
from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class UserProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    resilience_score: int = Field(default=0)


class Plan(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    prompt_used: str
    high_level_plan: str          # JSON string -- full-period month-by-month outline
    total_months: int
    current_month: int = Field(default=1)   # last month that has been detailed
    start_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="plan.id")
    scheduled_date: date
    scheduled_time: str           # "HH:MM" 24-hour format
    duration_minutes: int = Field(default=30)
    contextual_topic: str
    mvr_description: str
    status: str = Field(default="pending")
    # valid statuses: pending | completed | completed_mvr | reshuffled | missed
    original_time: str | None = None   # stores pre-reshuffle time
    month_number: int             # which month of the plan (1-indexed)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 6.2 Request / Response Schemas

```python
class GeneratePlanRequest(SQLModel):
    prompt: str   # e.g. "LeetCode 30 mins daily at 5 PM except Sundays for 3 months"


class GeneratePlanResponse(SQLModel):
    plan_id: int
    title: str
    total_months: int
    high_level_plan: dict         # the parsed JSON outline
    first_month_sessions: list    # list of Session dicts for month 1


class PlanSummary(SQLModel):
    id: int
    title: str
    total_months: int
    current_month: int
    total_sessions: int
    completed_sessions: int
    created_at: datetime


class SessionUpdate(SQLModel):
    session: dict
    points_earned: int
    resilience_score: int


class SalvageResponse(SQLModel):
    salvaged_count: int
    points_earned: int
    resilience_score: int
    sessions: list
```

---

## 7. Gemini LLM Integration (`llm.py`)

### 7.1 API Call Helper

```python
import json
import httpx

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

async def call_gemini(prompt: str, api_key: str, model: str) -> dict:
    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(url, json={
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7
            }
        })
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
```

### 7.2 Retry Logic

If Gemini returns malformed JSON, retry once. On second failure, raise an `HTTPException(502, "AI returned invalid response")`.

---

## 8. LLM Prompts (`prompts.py`)

### 8.1 Tier 1 -- High-Level Plan

This prompt asks the LLM to produce a month-by-month outline for the **entire** requested period. The output is stored in `plans.high_level_plan` and reused every time we generate the next month's sessions.

```python
TIER1_HIGH_LEVEL = """You are an expert habit coach and schedule planner.

The user will describe a goal, preferred schedule, and duration.
Generate a HIGH-LEVEL month-by-month plan for the ENTIRE duration.
This is a strategic outline, NOT individual daily sessions.

Return a JSON object with this exact structure:
{{
  "plan_title": "A short, motivating name for this plan",
  "total_months": <integer>,
  "schedule": {{
    "days_per_week": <integer>,
    "excluded_days": ["Sunday"],
    "preferred_time": "HH:MM",
    "session_duration_minutes": <integer>
  }},
  "months": [
    {{
      "month_number": 1,
      "theme": "Foundation & Basics",
      "focus_areas": ["Area 1", "Area 2", "Area 3"],
      "difficulty_level": "beginner",
      "weekly_progression": [
        "Week 1: ...",
        "Week 2: ...",
        "Week 3: ...",
        "Week 4: ..."
      ],
      "key_milestones": ["Milestone 1", "Milestone 2"]
    }}
  ]
}}

Rules:
- Create entries for EVERY month the user requests.
- Make progression logical and gradual across months.
- Each month should build on the previous one.
- Include variety within each month to prevent monotony.
- Weekly progressions should be specific enough to guide daily session generation later.
- Key milestones should be motivating and achievable.
- Extract the schedule details (days, time, duration, exclusions) from the user's request.

USER GOAL: {user_prompt}"""
```

### 8.2 Tier 2 -- Monthly Detail

This prompt generates the concrete daily sessions for a single month, using the stored high-level plan as context.

```python
TIER2_MONTHLY_DETAIL = """You are an expert habit coach. Generate detailed daily sessions for ONE specific month of a plan.

HIGH-LEVEL PLAN:
{high_level_plan_json}

Generate sessions for MONTH {month_number}.
Theme: {month_theme}
Focus areas: {focus_areas}
Weekly progression: {weekly_progression}

Schedule details:
- Start date for this month: {month_start_date}
- Days per week: {days_per_week}
- Excluded days: {excluded_days}
- Preferred time: {preferred_time}
- Session duration: {duration_minutes} minutes

Return a JSON object:
{{
  "sessions": [
    {{
      "date": "YYYY-MM-DD",
      "time": "HH:MM",
      "duration_minutes": {duration_minutes},
      "topic": "Specific, progressive contextual topic. Be concrete and actionable. Don't say 'Run' -- say '3k easy pace run focusing on breathing'. Don't say 'LeetCode' -- say 'Sliding Window: solve 2 medium problems'.",
      "mvr": "A Minimum Viable Routine achievable in under 5 minutes that still maintains the habit. Example: 'Read one LeetCode solution and trace through the logic' or 'Put on running shoes and walk around the block'."
    }}
  ]
}}

Rules:
- Generate sessions ONLY for dates within this month.
- Follow the weekly progression from the high-level plan.
- Make topics progressive within the month (build difficulty).
- Each MVR must be genuinely achievable in under 5 minutes.
- Respect the excluded days.
- Vary topics to prevent monotony while staying on-theme.
- Use the exact date format YYYY-MM-DD and time format HH:MM (24-hour)."""
```

---

## 9. API Endpoints

### 9.1 Plans (`routers/plans.py`)

#### `POST /api/plans/generate`

The core endpoint. Runs **two** LLM calls in sequence.

**Request body:**
```json
{ "prompt": "I want to practice LeetCode for 30 mins every day at 5 PM except Sundays for 3 months" }
```

**Logic:**
1. Call Gemini with `TIER1_HIGH_LEVEL` prompt → receive high-level plan JSON.
2. Extract month 1 details from the high-level plan.
3. Call Gemini with `TIER2_MONTHLY_DETAIL` prompt for month 1 → receive sessions array.
4. Insert a `Plan` row (store high-level plan as JSON string, `current_month=1`, calculate `start_date` from first session date).
5. Insert all month-1 `Session` rows linked to the plan (`month_number=1`).
6. Return the plan + high-level outline + first month sessions.

**Response:**
```json
{
  "plan_id": 1,
  "title": "LeetCode Mastery",
  "total_months": 3,
  "high_level_plan": {
    "plan_title": "LeetCode Mastery",
    "total_months": 3,
    "schedule": { "days_per_week": 6, "excluded_days": ["Sunday"], "preferred_time": "17:00", "session_duration_minutes": 30 },
    "months": [ ... ]
  },
  "first_month_sessions": [ ... ]
}
```

#### `GET /api/plans`

List all plans with summary stats.

**Response:**
```json
[
  {
    "id": 1,
    "title": "LeetCode Mastery",
    "total_months": 3,
    "current_month": 1,
    "total_sessions": 26,
    "completed_sessions": 5,
    "created_at": "2026-03-20T12:00:00"
  }
]
```

Compute `total_sessions` and `completed_sessions` by counting/filtering sessions for each plan.

#### `GET /api/plans/{id}`

Full plan detail including high-level plan and all generated sessions.

**Response:**
```json
{
  "id": 1,
  "title": "LeetCode Mastery",
  "total_months": 3,
  "current_month": 1,
  "start_date": "2026-03-21",
  "high_level_plan": { ... },
  "sessions": [ ... ]
}
```

#### `POST /api/plans/{id}/extend`

Generate the next month of detailed sessions.

**Logic:**
1. Load the plan and its `high_level_plan` JSON.
2. Compute `next_month = current_month + 1`. If `next_month > total_months`, return 400.
3. Calculate the start date for the next month (day after last session of current month, or first day of next calendar month -- whichever makes sense).
4. Extract month details from `high_level_plan.months[next_month - 1]`.
5. Call Gemini with `TIER2_MONTHLY_DETAIL` for the next month.
6. Insert new `Session` rows with `month_number = next_month`.
7. Update `plan.current_month = next_month`.
8. Return the new sessions.

**Response:**
```json
{
  "month_number": 2,
  "theme": "Intermediate Patterns",
  "sessions_created": 26,
  "sessions": [ ... ]
}
```

#### `DELETE /api/plans/{id}`

Delete a plan and all its sessions (cascade).

---

### 9.2 Sessions (`routers/sessions.py`)

#### `GET /api/sessions/today`

Returns all sessions for today, ordered by `scheduled_time`.

**Response:**
```json
{
  "date": "2026-03-20",
  "sessions": [
    {
      "id": 1,
      "plan_id": 1,
      "plan_title": "LeetCode Mastery",
      "scheduled_date": "2026-03-20",
      "scheduled_time": "17:00",
      "duration_minutes": 30,
      "contextual_topic": "Two Pointers: Valid Palindrome & Container With Most Water",
      "mvr_description": "Read one solution for Valid Palindrome and trace the pointer movement",
      "status": "pending",
      "original_time": null,
      "month_number": 1
    }
  ],
  "resilience_score": 42
}
```

Include `plan_title` by joining with the `Plan` table (or just a separate query).

#### `PATCH /api/sessions/{id}/complete`

**Logic:**
1. Load the session. Verify `status == "pending"`. If not, return 400.
2. Set `status = "completed"`.
3. Add 10 to `UserProfile.resilience_score`.
4. Return updated session + new score.

**Response:**
```json
{
  "session": { ... },
  "points_earned": 10,
  "resilience_score": 52
}
```

#### `PATCH /api/sessions/{id}/complete-mvr`

Same as complete but sets `status = "completed_mvr"` and awards **5** points.

#### `PATCH /api/sessions/{id}/push-back`

**Logic:**
1. Load the session. Verify `status == "pending"`.
2. Save current `scheduled_time` into `original_time`.
3. Add 2 hours to `scheduled_time` (parse "HH:MM", add 2h, format back).
4. Add 2 to resilience score.
5. Return updated session.

**Response:**
```json
{
  "session": { ... },
  "points_earned": 2,
  "resilience_score": 44
}
```

#### `PATCH /api/sessions/{id}/cascade`

**Logic:**
1. Load the session. Verify `status == "pending"`.
2. Save `scheduled_time` into `original_time`, set `status = "reshuffled"`.
3. Find all **future** pending sessions for the **same plan**, ordered by `scheduled_date, scheduled_time`.
4. Shift each one forward by one slot (push each session's date to the next scheduled date in the sequence). In the simplest implementation: shift all subsequent sessions forward by 1 day, skipping excluded days.
5. Add 2 to resilience score.
6. Return the reshuffled session + count of shifted sessions.

**Response:**
```json
{
  "session": { ... },
  "shifted_count": 3,
  "points_earned": 2,
  "resilience_score": 44
}
```

> **Simplification for hackathon:** Cascade is the most complex operation. A pragmatic approach: mark the current session as reshuffled, and for each subsequent pending session of the same plan on the same day or later, add 1 day to `scheduled_date`. This keeps the logic straightforward.

#### `POST /api/sessions/salvage`

**Logic:**
1. Find all sessions for today with `status == "pending"`.
2. Mark each as `status = "completed_mvr"`.
3. Add 5 points per salvaged session to resilience score.
4. Return summary.

**Response:**
```json
{
  "salvaged_count": 3,
  "points_earned": 15,
  "resilience_score": 57,
  "sessions": [ ... ]
}
```

---

### 9.3 Score (`routers/score.py`)

#### `GET /api/score`

```json
{ "resilience_score": 42 }
```

---

## 10. Two-Tier Generation Flow (Visual)

```
User: "LeetCode 30 min/day for 3 months"
            │
            ▼
   ┌─────────────────────┐
   │  POST /plans/generate│
   └─────────┬───────────┘
             │
    ┌────────▼─────────┐
    │  Gemini Call #1   │  ← TIER1_HIGH_LEVEL prompt
    │  (High-Level Plan)│
    └────────┬─────────┘
             │
             ▼
    Stored in plans.high_level_plan (JSON)
    Contains: 3 months of themes, focus areas, weekly progressions
             │
    ┌────────▼─────────┐
    │  Gemini Call #2   │  ← TIER2_MONTHLY_DETAIL prompt (month 1 only)
    │  (Month 1 Detail) │
    └────────┬─────────┘
             │
             ▼
    26 session rows inserted (month 1 only)
    User sees month 1 on their calendar



... 4 weeks later ...

   ┌──────────────────────────┐
   │ POST /plans/{id}/extend  │
   └──────────┬───────────────┘
              │
     ┌────────▼─────────┐
     │  Gemini Call      │  ← TIER2_MONTHLY_DETAIL prompt (month 2)
     │  (Month 2 Detail) │    Uses stored high_level_plan as context
     └────────┬─────────┘
              │
              ▼
     ~26 new session rows inserted (month 2)
     plan.current_month updated to 2
```

---

## 11. Resilience Score Rules

| Action | Points | Status set to |
|---|---|---|
| Complete full routine | +10 | `completed` |
| Complete MVR (including salvage) | +5 | `completed_mvr` |
| Push back 2 hours | +2 | remains `pending` (new time) |
| Skip & cascade | +2 | `reshuffled` |
| Missed (no action taken) | 0 | `missed` |

**The score never decreases.** No negative points, ever.

---

## 12. Seed Data (`seed.py`)

A standalone script that populates the database with demo data for a compelling hackathon presentation. Run it with `python seed.py`.

Should create:

1. **UserProfile** with `resilience_score = 47`.

2. **Plan: "LeetCode Mastery"**
   - prompt: "I want to practice LeetCode for 30 minutes every day at 5 PM except Sundays for 3 months"
   - total_months: 3, current_month: 1
   - A realistic `high_level_plan` JSON with 3 months of themes (Foundations → Intermediate Patterns → Advanced & Contest Prep)

3. **Sessions for the current week** (use dynamic dates relative to today):
   - 2 days ago: "Arrays: Two Sum & Contains Duplicate" — `completed` — 17:00
   - Yesterday: "Two Pointers: Valid Palindrome" — `completed_mvr` — 17:00
   - Today 09:00: "Morning Review: Hash Map Patterns" — `completed` — 09:00
   - Today 17:00: "Sliding Window: Maximum Subarray" — `pending` — 17:00
   - Tomorrow: "Stack: Valid Parentheses & Min Stack" — `pending` — 17:00
   - Day after: "Binary Search: Search Insert Position" — `pending` — 17:00

4. **Plan: "Morning Mindfulness"**
   - A second plan to show multi-plan support
   - 2-3 sessions this week (morning times, meditation/breathing topics)

This ensures the demo dashboard has a mix of completed, MVR, and pending sessions across multiple plans.

---

## 13. Error Handling

All endpoints should return structured error responses:

```json
{
  "detail": "Human-readable error message"
}
```

Key error cases:
- **Invalid session status transition** (e.g. completing an already-completed session) → 400
- **Plan not found** → 404
- **Session not found** → 404
- **Cannot extend past total_months** → 400
- **Gemini API failure** → 502 with message "AI service temporarily unavailable"
- **Gemini returns malformed JSON** → retry once, then 502

---

## 14. Voice Daily Briefing -- SLNG.ai Integration (Optional)

An optional "AI coach voice" feature. The backend generates a natural-language summary of today's sessions and converts it to speech via the [SLNG.ai](https://docs.slng.ai/hackathon) TTS API. SLNG provides a unified API across multiple TTS providers (Deepgram, ElevenLabs, Rime) -- swap models by changing the URL, not the code.

### 14.1 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SLNG_API_KEY` | For voice feature | -- | SLNG.ai API key (get one at [app.slng.ai](https://app.slng.ai)) |
| `SLNG_TTS_MODEL` | No | `deepgram/aura:2` | TTS model. Low-latency default. Alternatives: `elevenlabs/eleven:3` (premium voices), `rime/arcana:3-en` (multilingual) |

### 14.2 Briefing Text Generation

Build the briefing text from today's sessions -- no LLM call needed, just string formatting. Place this in a helper function `build_briefing_text(sessions, resilience_score)` in a new file `voice.py` or inside `routers/voice.py`.

Template logic:

```python
def build_briefing_text(sessions: list, score: int) -> str:
    pending = [s for s in sessions if s.status == "pending"]
    completed = [s for s in sessions if s.status in ("completed", "completed_mvr")]

    if not pending and not completed:
        return (
            f"Good news! Your schedule is clear today. "
            f"Your resilience score is {score}. "
            f"Head to the Planner to start a new routine whenever you're ready."
        )

    greeting = "Good morning" if datetime.now().hour < 12 else "Good afternoon"
    parts = [f"{greeting}!"]

    if completed:
        parts.append(f"You've already knocked out {len(completed)} session{'s' if len(completed) != 1 else ''} today. Nice work!")

    if pending:
        parts.append(f"You have {len(pending)} session{'s' if len(pending) != 1 else ''} coming up.")
        for i, s in enumerate(pending[:3]):  # max 3 to keep it short
            time_fmt = format_time_12h(s.scheduled_time)
            parts.append(f"At {time_fmt}: {s.contextual_topic}.")
        if len(pending) > 3:
            parts.append(f"Plus {len(pending) - 3} more later.")

    parts.append(
        f"Your resilience score is {score}. "
        f"Remember, even five minutes counts. You've got this!"
    )

    return " ".join(parts)
```

### 14.3 SLNG.ai TTS API Call

SLNG uses a single bridge endpoint for all TTS providers. Swap models by changing the URL path.

```python
import httpx

SLNG_TTS_URL = "https://api.slng.ai/v1/bridges/unmute/tts/{model}"

async def text_to_speech(text: str, api_key: str, model: str) -> bytes:
    url = SLNG_TTS_URL.format(model=model)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json={
            "text": text
        }, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        response.raise_for_status()
        return response.content
```

The response is raw audio bytes (WAV format for Deepgram, may vary by provider).

**Model options (swap by changing `SLNG_TTS_MODEL` env var):**
- `deepgram/aura:2` -- fast, low latency, great for English (default)
- `elevenlabs/eleven:3` -- premium voice quality
- `rime/arcana:3-en` -- good multilingual support

To pick a specific voice within a model, add `"model": "aura-2-theia-en"` to the request body (see [SLNG voice docs](https://docs.slng.ai/voices/deepgram-aura)).

### 14.4 Endpoint

#### `GET /api/voice/daily-briefing`

**Logic:**
1. Fetch today's sessions (reuse the same query as `GET /api/sessions/today`).
2. Fetch resilience score.
3. Build briefing text with `build_briefing_text()`.
4. Call SLNG.ai TTS with the text.
5. Return audio as a response.

**Response:** `audio/wav` binary (or `audio/mpeg` depending on provider).

**Headers:**
```
Content-Type: audio/wav
Content-Disposition: inline
```

**Error handling:**
- If `SLNG_API_KEY` is not set, return 501 with `{"detail": "Voice feature not configured"}`.
- If SLNG API fails, return 502 with `{"detail": "Voice service temporarily unavailable"}`.

**Implementation:**
```python
@router.get("/api/voice/daily-briefing")
async def daily_briefing(db: Session = Depends(get_session)):
    if not SLNG_API_KEY:
        raise HTTPException(501, "Voice feature not configured")

    sessions = get_today_sessions(db)
    score = get_resilience_score(db)
    text = build_briefing_text(sessions, score)
    audio_bytes = await text_to_speech(text, SLNG_API_KEY, SLNG_TTS_MODEL)

    return Response(content=audio_bytes, media_type="audio/wav")
```

### 14.5 File Placement

Add to the backend structure:

```
backend/
├── routers/
│   ├── ...
│   └── voice.py       # Daily briefing endpoint + text builder
```

### 14.6 Quick Test

Verify your SLNG key works before integrating:

```bash
curl https://api.slng.ai/v1/bridges/unmute/tts/deepgram/aura:2 \
  -H "Authorization: Bearer YOUR_SLNG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from Adaptive Routines!"}' \
  --output test.wav
```

If you hear "Hello from Adaptive Routines!" -- you're set.

---

## 15. CORS and Frontend Connection

The backend runs on `http://localhost:8000`. The Lovable frontend will run on its own dev URL (typically `https://*.lovable.app` during development or `http://localhost:5173` if running locally).

CORS is configured to allow all origins (`*`) for the hackathon demo. Every response includes appropriate CORS headers so the frontend can call the API without issues.

---

## 16. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | -- | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-3.0-pro` | Gemini model identifier (adjust to match available model name) |
| `DATABASE_URL` | No | `sqlite:///routines.db` | SQLite database path |
| `SLNG_API_KEY` | For voice | -- | SLNG.ai API key (omit to disable voice feature) |
| `SLNG_TTS_MODEL` | No | `deepgram/aura:2` | SLNG TTS model (alternatives: `elevenlabs/eleven:3`, `rime/arcana:3-en`) |
