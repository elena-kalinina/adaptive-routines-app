# Adaptive Routines App

A mobile-first PWA that uses AI to convert user goals into actionable, adaptable calendar routines. Built around the concept of graceful recovery from disruptions using a "Resilience Score" instead of punitive streaks.

## Documentation

- **[Full Specification](ADAPTIVE_ROUTINES_SPEC.md)** -- Product spec covering design system, database schema, user flows, UI screens, LLM integration, and gamification.
- **[Lovable Implementation Plan](LOVABLE_IMPLEMENTATION_PLAN.md)** -- Step-by-step prompts to build the app iteratively in Lovable, from foundation to polish.

## Core Concepts

- **AI Plan Generation** -- Describe a goal in plain language, get a full syllabus of progressive daily sessions with contextual topics
- **Minimum Viable Routine (MVR)** -- Every session has a 5-minute fallback so the habit never fully breaks
- **"Life Happened" Reshuffle** -- Three zero-guilt options when plans go sideways: downgrade, push back, or cascade
- **Resilience Score** -- Points for completing, adapting, and showing up. No penalties. Ever.
- **Salvage the Day** -- End-of-day rescue that bundles missed MVRs into one quick session

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Tailwind CSS |
| Backend | Supabase (Postgres, Auth, Edge Functions) |
| AI | OpenAI API (GPT-4o) with structured JSON outputs |
| Deployment | Lovable / PWA |

## Getting Started

```bash
# Clone the repository
git clone https://github.com/elena-kalinina/adaptive-routines-app.git
cd adaptive-routines-app
```

Detailed setup instructions will be added as the project scaffolding is built out.
