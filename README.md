# Adaptive Routines

AI-powered app that turns goals into adaptive daily routines with contextual reminders, graceful rescheduling, and a zero-guilt Resilience Score.

Built for the [{Tech: Europe} Amsterdam AI Hackathon](https://luma.com/amsterdam-hack).

## The Problem

People use AI to generate great study plans, fitness routines, and learning schedules. But those plans die in a notes app because they never become part of your calendar. And when life inevitably interrupts, streak-based apps punish you -- so you quit entirely.

## The Solution

Adaptive Routines bridges the gap between AI-generated plans and daily execution. The app schedules sessions on your timeline, and when things go sideways, it helps you adapt instead of abandon. Every adjustment earns points. The score never goes down. You never start over from zero.

## Core Concepts

- **Two-Tier AI Planning** -- Describe a goal in plain language. The AI builds a strategic month-by-month roadmap for the full period, then generates detailed daily sessions one month at a time.
- **Minimum Viable Routine (MVR)** -- Every session has a 5-minute fallback so the habit never fully breaks.
- **"Life Happened" Rescheduling** -- Three zero-guilt options: downgrade to MVR, push back 2 hours, or skip and cascade.
- **Resilience Score** -- Points for completing, adapting, and showing up. No penalties. Ever.
- **Salvage the Day** -- End-of-day rescue that bundles missed MVRs into one quick session.
- **Voice Briefing** -- AI coach reads your daily schedule aloud via SLNG.ai text-to-speech.

## Architecture

```
┌─────────────────────┐       ┌──────────────────────┐
│   React Frontend    │──────▶│   FastAPI Backend     │
│   (built w/ Lovable)│  API  │   (localhost:8000)    │
└─────────────────────┘       └──────┬───────┬────────┘
                                     │       │
                              ┌──────▼──┐ ┌──▼───────┐
                              │ Gemini  │ │ SLNG.ai  │
                              │ 3.1 Pro │ │   TTS    │
                              └─────────┘ └──────────┘
```

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Tailwind CSS (Lovable) |
| Backend | Python FastAPI + SQLite + SQLModel |
| AI | Google Gemini 3.1 Pro (structured JSON output) |
| Voice | SLNG.ai TTS (Deepgram Aura voice) |

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --port 8000
```

Requires a `.env` file in the repo root:

```
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-3.1-pro-preview
SLNG_API_KEY=your-slng-key          # optional, for voice feature
```

### Seed Demo Data

```bash
cd backend
python seed.py
```

Creates two plans (LeetCode Mastery + Morning Mindfulness) with sessions across the current week in mixed statuses -- ready for a demo.

### Frontend

The frontend is a separate Lovable project that connects to the backend API. Set the `API_BASE_URL` in `src/lib/api.ts` to your backend URL (localhost or ngrok).

### API Docs

Interactive Swagger docs at [http://localhost:8000/docs](http://localhost:8000/docs) once the backend is running.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/plans/generate` | Generate a new plan (two Gemini calls) |
| GET | `/api/plans` | List all plans with progress stats |
| GET | `/api/plans/{id}` | Plan detail with all sessions |
| POST | `/api/plans/{id}/extend` | Generate next month's sessions |
| DELETE | `/api/plans/{id}` | Delete a plan |
| GET | `/api/sessions/today` | Today's sessions + resilience score |
| PATCH | `/api/sessions/{id}/complete` | Mark done (+10 pts) |
| PATCH | `/api/sessions/{id}/complete-mvr` | MVR done (+5 pts) |
| PATCH | `/api/sessions/{id}/push-back` | Reschedule +2h (+2 pts) |
| PATCH | `/api/sessions/{id}/cascade` | Skip and shift (+2 pts) |
| POST | `/api/sessions/salvage` | Salvage the day |
| GET | `/api/score` | Current resilience score |
| GET | `/api/voice/daily-briefing` | AI voice briefing (audio/mpeg) |

## Documentation

- **[Backend Spec](HACKATHON_BACKEND_SPEC.md)** -- Complete backend specification: models, endpoints, LLM prompts, setup.
- **[Lovable Prompts](HACKATHON_LOVABLE_PROMPTS.md)** -- Step-by-step frontend prompts for Lovable.
- **[Original Product Spec](ADAPTIVE_ROUTINES_SPEC.md)** -- Full product spec: design system, user flows, UI screens, gamification.
