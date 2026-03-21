# Hackathon Demo Tips & Guidelines

## Demo Script -- Plan the Story First

Before writing any code, decide on the **exact 3-minute demo script**:

1. Open app, show the onboarding screen (5 sec)
2. Go to Planner, type a goal live -- "I want to learn guitar for 20 minutes every evening for 3 months" (10 sec)
3. Watch AI generate the plan, show the month chips and session preview (15 sec -- this is the wow moment)
4. Add to calendar, land on Dashboard with today's sessions (5 sec)
5. Complete one session -- show the score animation (5 sec)
6. "Life Happened" on another -- show the calm bottom sheet, pick MVR (10 sec)
7. Quick look at Plans page showing progress bar (5 sec)

**Build backward from this script.** Everything the audience sees must be polished. Everything they don't see can be rough.

---

## Practical Tricks

### 1. Pre-warm the LLM call

The plan generation takes 10-20 seconds (two Gemini calls). During the demo, that's an eternity. Two options:

- **Best:** Have a pre-generated plan in the seed data. Demo the Planner chat with a real call but also have the Dashboard already populated so you can switch to it while "waiting."
- **Backup:** Add a `/api/plans/generate-demo` endpoint that returns a hardcoded beautiful response instantly. Wire it up as a fallback if Gemini is slow during the live demo.

### 2. Seed data is your safety net

Make `seed.py` create a gorgeous demo state: a plan with mixed session statuses (some completed, some pending, one reshuffled) so the Dashboard timeline looks alive and colorful from the first second. Run it right before the demo.

### 3. Make the Lovable frontend feel native

When you get to Step 8 (polish), these specific things have outsized visual impact:

- The **resilience score counting up** animation -- audiences love visible number changes
- The **bottom sheet sliding up** for Life Happened -- feels very app-like
- **Skeleton loading** shimmer on cards -- makes it feel production-grade
- The phone-frame wrapper (`max-w-md mx-auto` with shadow) -- on a projector this makes it look like a real phone app

### 4. CORS will bite you

Test the Lovable-to-localhost connection in Step 2 (API service layer) before building anything else. If CORS doesn't work, nothing works. Have `allow_origins=["*"]` in FastAPI from minute one.

### 5. Build the backend first, frontend second

Spend the first 30-40% of time getting all endpoints working and tested (use FastAPI's `/docs` Swagger UI -- it's a free testing tool). Once the backend is solid, the Lovable prompts go much faster because every step gets real data immediately.

### 6. Lovable emergency fallback

If Lovable struggles with a complex prompt, split it. For example, if Step 6 (Planner) fails, first build just the chat UI with hardcoded data, then add the API call. Don't let one step block everything.

### 7. One visual detail that impresses judges

Add a subtle gradient or glassmorphism effect to the top bar. In your Step 8 Lovable prompt, add: "Give the top bar a subtle glass effect: backdrop-blur-md bg-white/80". Small touch, big impression.

---

## Time Boxing (4 hours build + 1 hour video)

Total: 5 hours. Last hour is reserved for recording the demo video.

### Build Phase (4 hours)

| Block | Time   | What | Checkpoint |
|-------|--------|------|------------|
| 1     | 40 min | Backend: models, database, ALL endpoints (sessions, score, complete, reshuffle, cascade, salvage) | `/docs` shows all endpoints, seed data works |
| 2     | 35 min | Backend: plan generation (both Gemini tiers) + seed.py | Can generate a plan via `/docs`, seed populates demo data |
| 3     | 15 min | Backend: voice briefing endpoint (ElevenLabs) | Audio plays from `/docs` |
| **--** | **5 min** | **Backend smoke test: run seed, verify `/docs`** | **All 12+ endpoints green** |
| 4     | 25 min | Lovable: Steps 1-3 (design system + API layer + dashboard with live data) | Dashboard renders real sessions from backend |
| 5     | 25 min | Lovable: Step 4 (complete + life happened bottom sheet) | Can complete and reshuffle sessions |
| 6     | 20 min | Lovable: Steps 5-6 (salvage + AI planner chat) | Can generate a plan end-to-end |
| 7     | 15 min | Lovable: Step 7 (plans library -- keep it simple) | Plans page lists plans with progress |
| 8     | 20 min | Lovable: Steps 8-9 (animations, score glow, polish, voice button) | App feels alive and polished |
| **--** | **5 min** | **Full run-through of the demo flow** | **Everything works end-to-end** |
| 9     | 15 min | Bug fixes, final seed data refresh, prep for recording | Clean state ready |

### Cut List (drop these if behind schedule)

If you're running over, drop in this order (least to most important):

1. **Plans library** (Step 7) -- skip entirely, nobody will miss it in a 3-min demo
2. **Cascade/reshuffle** -- hardcode the response or simplify to just "mark as skipped"
3. **Voice briefing** -- nice-to-have, demo still works without it
4. **Salvage the Day** -- cut if tight, show only complete + life happened
5. **NEVER cut:** Dashboard, Complete, Life Happened, AI Planner -- these ARE the demo

### Video Phase (1 hour)

| Block | Time   | What |
|-------|--------|------|
| 1     | 10 min | Write a shot list from the demo script (which screens, which actions, what to say) |
| 2     | 10 min | Reset seed data to perfect state, test audio/screen recording setup |
| 3     | 20 min | Record 2-3 takes (aim for 2-3 minutes each) |
| 4     | 20 min | Light edit: trim dead air, add title card, export |

**Video recording tips:**
- Use phone screen recording if demoing on mobile, or OBS/QuickTime on desktop
- Record in the phone-frame view (desktop browser, `max-w-md` layout) -- looks great on any screen
- Talk over it: explain the problem ("streaks punish you"), show the solution ("resilience score rewards adapting")
- End with the voice briefing playing -- strong audio finish

---

## Voice Briefing Demo Tip

The SLNG.ai voice briefing is a killer demo moment. When presenting:

1. Open the app on the Dashboard
2. Say to the audience: "Your AI coach can also talk to you"
3. Tap the speaker button -- let the room hear the briefing
4. This lands best right after showing the populated Dashboard, before doing any interactions

Keep it for the middle of the demo (not the opener) so it feels like a surprise feature.

---

## The #1 Hackathon Rule

**If something doesn't work after 15 minutes, hardcode it and move on.** You can always come back. A polished demo with one fake endpoint beats a half-working demo with everything "real."
