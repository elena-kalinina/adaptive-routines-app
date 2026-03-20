# Adaptive Routines -- Lovable Frontend Prompts (Hackathon)

Step-by-step prompts for building the frontend in Lovable. The frontend is a **pure UI layer** -- all data and AI logic lives in a Python FastAPI backend running on `localhost:8000`. No Supabase, no Edge Functions, no auth.

Paste each prompt into Lovable one at a time. Wait for it to finish before moving to the next.

---

## Pre-Flight

1. The FastAPI backend must be running at `http://localhost:8000` (see `HACKATHON_BACKEND_SPEC.md`).
2. Create a new Lovable project named "Adaptive Routines".
3. **Do NOT connect Supabase.** This app uses a custom backend.

---

## Step 1: Design System Foundation

**Goal:** Establish the visual language before building features.

### Prompt 1.1 -- Global Design Tokens

```
Set up a mobile-first React + TypeScript + Tailwind web app with the following design system.
Do NOT build any features yet -- just set up the foundation:

Global Styles:
- Font: Inter (import from Google Fonts)
- Background: bg-slate-50
- Default text: text-slate-800
- All cards: bg-white rounded-2xl shadow-sm
- All buttons: rounded-2xl with generous padding
- No harsh reds or greens anywhere. Success color is teal-500. Adaptation/change color is indigo-400.
- Use lucide-react icons with strokeWidth={1.5} throughout

Create a single placeholder page at "/" that says "Adaptive Routines" centered on screen, styled with these tokens, so I can confirm the design system is working.
```

---

## Step 2: API Service Layer

**Goal:** Create a clean abstraction for all backend calls so every component can use it.

### Prompt 2.1 -- API Client

```
Create an API service module at src/lib/api.ts that handles all communication with the backend.

The backend runs at http://localhost:8000. Store this as a constant API_BASE_URL at the top of the file.

Create these async functions (all return parsed JSON):

Plan functions:
- generatePlan(prompt: string) -- POST /api/plans/generate with body { prompt }
  Returns: { plan_id, title, total_months, high_level_plan, first_month_sessions }
- getPlans() -- GET /api/plans
  Returns: array of { id, title, total_months, current_month, total_sessions, completed_sessions, created_at }
- getPlan(id: number) -- GET /api/plans/{id}
  Returns: { id, title, total_months, current_month, start_date, high_level_plan, sessions }
- extendPlan(id: number) -- POST /api/plans/{id}/extend
  Returns: { month_number, theme, sessions_created, sessions }
- deletePlan(id: number) -- DELETE /api/plans/{id}

Session functions:
- getTodaySessions() -- GET /api/sessions/today
  Returns: { date, sessions, resilience_score }
  Each session has: id, plan_id, plan_title, scheduled_date, scheduled_time, duration_minutes, contextual_topic, mvr_description, status, original_time, month_number
- completeSession(id: number) -- PATCH /api/sessions/{id}/complete
  Returns: { session, points_earned, resilience_score }
- completeMvr(id: number) -- PATCH /api/sessions/{id}/complete-mvr
  Returns: { session, points_earned, resilience_score }
- pushBackSession(id: number) -- PATCH /api/sessions/{id}/push-back
  Returns: { session, points_earned, resilience_score }
- cascadeSession(id: number) -- PATCH /api/sessions/{id}/cascade
  Returns: { session, shifted_count, points_earned, resilience_score }
- salvageDay() -- POST /api/sessions/salvage
  Returns: { salvaged_count, points_earned, resilience_score, sessions }

Score function:
- getScore() -- GET /api/score
  Returns: { resilience_score }

Each function should:
- Use fetch() with the correct method and headers (Content-Type: application/json where needed)
- Throw a descriptive error if the response is not ok (include the status code and error detail from the response body)
- All PATCH/POST calls should include { method, headers: { "Content-Type": "application/json" }, body } as appropriate

Do NOT build any UI yet. Just the API module.
```

---

## Step 3: Dashboard Layout and Routine Cards

**Goal:** Build the main screen -- the Today timeline -- connected to the backend from the start.

### Prompt 3.1 -- Dashboard Structure

```
Build the main Dashboard page at route "/". This is a mobile-first daily timeline view. It fetches data from the backend using the API module we created.

On mount, call getTodaySessions() from src/lib/api.ts. While loading, show a centered spinner. If the backend is unreachable, show a friendly error: "Can't reach the server. Make sure the backend is running on localhost:8000."

Layout from top to bottom:

1. TOP BAR (sticky):
   - Left side: Today's date formatted as "Friday, Mar 20" (use the actual current date)
   - Right side: Resilience Score from the API response, displayed with a small Shield icon from lucide-react. Style: text-teal-500 font-bold text-lg. Give the score number an id="resilience-score" so we can animate it later.

2. TIMELINE BODY (scrollable, takes remaining height above the bottom nav):
   - A thin vertical line on the left margin (border-l-2 border-slate-200) with small circular dots at each session time
   - A horizontal "current time" indicator line that spans the full width, positioned at the current time. Style: thin teal-400 line with a subtle glow (box-shadow: 0 0 8px rgba(20, 184, 166, 0.4)).

3. ROUTINE CARDS attached to the timeline:
   Render each session from the API as a card. Each Routine Card:
   - Container: bg-white rounded-2xl shadow-sm p-4 with a colored left border (4px) based on status
   - Text hierarchy:
     - Time: text-sm font-medium text-slate-400 -- format scheduled_time as "5:00 PM"
     - Topic: text-lg font-bold text-slate-800 -- this is contextual_topic, the PRIMARY visual element
     - Plan name: text-xs text-slate-400 -- show plan_title prefixed with "From: "
   - Two icon buttons on the right:
     - CheckCircle icon (teal-500) for "Complete" -- only shown if status is "pending"
     - RefreshCw icon (indigo-400) for "Life Happened" -- only shown if status is "pending"
   - Status-based left border colors and styling:
     - pending: no colored left border, full opacity
     - completed: border-teal-500, content slightly faded (opacity-60), teal checkmark overlay
     - completed_mvr: border-teal-400, slightly faded, small "MVR" badge
     - reshuffled: border-indigo-400, shuffle icon badge
     - missed: border-slate-300, most faded (opacity-40)

4. If no sessions for today, show a friendly empty state with an illustration and "No routines today. Visit the Planner to create one!" with a teal button linking to /planner.

5. BOTTOM NAVIGATION BAR (sticky at bottom):
   - Three tabs with lucide-react icons (strokeWidth 1.5):
     - "Today" (CalendarDays icon) -- active by default, teal-500 when active
     - "Plans" (List icon)
     - "Planner" (Sparkles icon)
   - Style: bg-white border-t border-slate-100, centered icons with small label text below each
   - Tabs link to: /, /plans, /planner respectively

Make the whole page scroll naturally on mobile. Use generous padding and spacing -- it should feel spacious, not cramped. Max width of content: max-w-md mx-auto for a nice mobile feel even on desktop.
```

---

## Step 4: Complete and Life Happened Logic

**Goal:** Make the core interaction loop functional.

### Prompt 4.1 -- Complete Button

```
Implement the "Complete" button on each Routine Card on the Dashboard:

When a user clicks the CheckCircle (Complete) button on a pending session:
1. Call completeSession(sessionId) from src/lib/api.ts
2. On success, update the local state:
   - Change the session's status to "completed"
   - Update the resilience score display to the new value from the response
3. Animate the card: transition to showing a teal-500 left border, fade the content to opacity-60, and show a small teal checkmark
4. The Resilience Score in the header should animate: count up from old value to new value over 500ms. Add a brief teal glow pulse (box-shadow animation) around the score.
5. If the API call fails, show a toast notification with the error message. Do NOT change the card state.
6. The CheckCircle button should only be visible on cards with status "pending".

Use React state to manage sessions locally after the initial fetch. Don't re-fetch the entire list on every action.
```

### Prompt 4.2 -- Life Happened Bottom Sheet

```
Build the "Life Happened" flow:

When a user clicks the RefreshCw (Life Happened) button on a pending session, open a Bottom Sheet (Drawer) that slides up from the bottom of the screen. Use the shadcn/ui Drawer component. Do NOT use a centered modal popup.

The Drawer content:
- A small drag handle at the top
- Header: "No stress. How do we adjust?" in text-lg font-bold text-slate-700
- Subheader showing the session info: "[contextual_topic] at [formatted time]" in text-sm text-slate-400
- Three option cards stacked vertically, each as a tappable card (bg-slate-50 rounded-2xl p-4 cursor-pointer, hover:bg-slate-100 transition):

  Option A -- "Do the Minimum":
  - Icon: Zap from lucide-react in amber-500
  - Title: "Downgrade to MVR (5 mins)" in font-semibold
  - Subtitle: Show the session's actual mvr_description from the data
  - Badge: "+5 resilience" in a small bg-teal-100 text-teal-700 rounded-full px-2 py-0.5 text-xs pill

  Option B -- "Push Back 2 Hours":
  - Icon: Clock from lucide-react in indigo-400
  - Title: "Push back 2 hours" in font-semibold
  - Subtitle: "Reschedule to [current time + 2 hours formatted]"
  - Badge: "+2 resilience" pill (same style)

  Option C -- "Skip & Cascade":
  - Icon: ArrowRight from lucide-react in indigo-400
  - Title: "Skip and shift everything" in font-semibold
  - Subtitle: "This session moves to the next free slot"
  - Badge: "+2 resilience" pill (same style)

When the user taps an option:

Option A (MVR):
- Call completeMvr(sessionId) from the API
- Update local state: status becomes "completed_mvr"
- Close drawer, show the score glow animation with +5

Option B (Push Back):
- Call pushBackSession(sessionId) from the API
- Update local state with the new scheduled_time from the response
- Close drawer, animate the card moving to its new position in the timeline (use transition-all duration-500)
- Show score glow with +2

Option C (Cascade):
- Call cascadeSession(sessionId) from the API
- Re-fetch today's sessions (since multiple sessions may have shifted) by calling getTodaySessions() again
- Close drawer, show score glow with +2

After ANY option, trigger the resilience score glow animation. For reshuffles (Options B and C), make the glow indigo instead of teal.

All cards in the drawer should use calming colors only -- no reds anywhere.
```

---

## Step 5: Salvage the Day

**Goal:** Build the end-of-day rescue feature.

### Prompt 5.1 -- Salvage Day FAB

```
Add a "Salvage the Day" floating action button to the Dashboard:

Visibility logic:
- After 6:00 PM local time, check if there are any sessions with status "pending" for today (from the local state, no extra API call needed)
- If yes, show a floating button positioned at the bottom center of the screen, ABOVE the bottom navigation bar (use bottom-20 or similar)
- If no pending sessions or before 6 PM, don't show it

Button style:
- bg-teal-500 text-white rounded-full shadow-lg px-6 py-3
- A subtle breathing/pulse animation (animate-pulse but toned down -- reduce opacity range)
- Content: Sparkles icon + "Salvage the Day" text
- font-medium text-sm

When tapped, open a Bottom Sheet (Drawer) with:
- Header: "Quick Catch-Up" in text-lg font-bold text-slate-700
- Subheader: "Bundle all remaining tasks into a 15-minute session" in text-sm text-slate-400
- A list of all pending sessions, showing just the mvr_description as a bulleted checklist:
  - Each item: a small circle bullet + the MVR text in text-sm text-slate-600
  - Example items: "• Read one LeetCode solution", "• Put on shoes, walk one block"
- At the bottom: a large teal CTA button:
  - bg-teal-500 text-white rounded-2xl py-4 w-full font-bold text-lg
  - Text: "I Did It! 💪" (this is one place where an emoji adds energy)

When "I Did It!" is tapped:
1. Call salvageDay() from the API
2. Update local state: set all pending sessions to "completed_mvr"
3. Update resilience score with the new value (animate the count-up + teal glow)
4. Close the drawer
5. Show a brief celebratory message (a toast or inline message): "Amazing! You salvaged the day. +[points] resilience"
```

---

## Step 6: AI Planner

**Goal:** Build the AI-powered plan generation page. This is the WOW moment for the demo.

### Prompt 6.1 -- Planner Chat UI

```
Create the AI Planner page at route "/planner" (accessible from the bottom nav "Planner" tab).

Layout -- a polished chat interface:

1. Top bar: "AI Planner" title with a Sparkles icon (teal-500), same sticky style as Dashboard

2. Chat area (scrollable, takes remaining space between top bar and input area):
   - Start with a single AI message bubble (left-aligned):
     Style: bg-white rounded-2xl p-4 shadow-sm, max-w-[85%]
     Text: "Hi! Tell me about a habit or skill you want to build. Include how often, what time, and for how long. For example: 'I want to practice guitar for 20 minutes every evening at 7 PM for 2 months, skipping weekends.'"

3. Input area (sticky at bottom, above bottom nav):
   - Container: bg-white border-t border-slate-100 p-3
   - Text input: bg-slate-100 rounded-2xl px-4 py-3 w-full, placeholder "Describe your goal and schedule..."
   - Send button: bg-teal-500 rounded-full p-2 ml-2, with ArrowUp icon in white
   - The input and button should be in a flex row

When the user types a message and hits send (or presses Enter):
1. Show their message as a right-aligned bubble (bg-teal-500 text-white rounded-2xl p-4, max-w-[85%])
2. Show a typing indicator: a left-aligned bubble with three animated dots (use CSS animation for a wave effect)
3. Call generatePlan(prompt) from src/lib/api.ts
4. Replace the typing indicator with a PLAN PREVIEW COMPONENT:

PLAN PREVIEW COMPONENT (rendered as an AI response bubble, left-aligned, bg-white rounded-2xl p-5 shadow-sm):
- Plan title: text-xl font-bold text-slate-800
- Below that, a "high-level overview" section:
  - Label: "Your journey" in text-sm font-medium text-slate-500 mb-2
  - Horizontal scrollable row of MONTH CHIPS:
    - Each month: a pill showing "Month [N]: [theme]" e.g. "Month 1: Foundations"
    - Style: bg-slate-100 rounded-xl px-3 py-2 text-sm text-slate-700 whitespace-nowrap
    - Active/first month: bg-teal-100 text-teal-700 border border-teal-200
  - Below chips: show key_milestones for month 1 as small text items with a Target icon
- Divider line (border-t border-slate-100 my-3)
- Below that, "Month 1 Preview" section:
  - Label: "Month 1: [theme]" in text-sm font-medium text-slate-500 mb-2
  - Show the first 5 sessions from first_month_sessions in compact cards:
    - Each: date + topic in a small card (bg-slate-50 rounded-xl p-3 mb-2)
    - Date: text-xs text-slate-400
    - Topic: text-sm font-semibold text-slate-700
  - If there are more than 5, show "and [N] more sessions this month..." in text-xs text-slate-400
- Session count badge: "[N] sessions in month 1 • [total_months] months total" in text-sm text-slate-500
- Large CTA button at the bottom:
  - bg-teal-500 text-white rounded-2xl py-4 w-full font-bold text-lg shadow-md
  - Text: "Looks Good, Add to Calendar"
  - hover: bg-teal-600 transition

When "Looks Good, Add to Calendar" is clicked:
1. Show a brief loading state on the button (spinner + "Adding...")
2. The plan is already created in the backend (generatePlan does that), so just show a success state
3. Add a new AI bubble: "Plan added! Your first month of sessions is on your timeline. Check the Today tab to see what's coming up."
4. After 2 seconds, auto-navigate to "/" (the Dashboard)

If the API call fails during generation:
- Replace the typing indicator with an error bubble (left-aligned, same style but with a subtle red-50 background):
  "Sorry, I had trouble creating that plan. Please try again with a bit more detail about your schedule."
- Re-enable the input so the user can try again

IMPORTANT: The input should be disabled and the send button should show a spinner while waiting for the AI response. This generation can take 10-20 seconds since it makes two LLM calls.
```

---

## Step 7: Plans Library

**Goal:** Let users view and manage their plans.

### Prompt 7.1 -- Plans Page

```
Create a Plans page at route "/plans" (accessible from the bottom nav "Plans" tab).

On mount, call getPlans() from src/lib/api.ts. Show a spinner while loading.

Layout:
1. Top bar: "Your Plans" in text-xl font-bold, same sticky style as other pages

2. Plan Cards (vertical list, max-w-md mx-auto):
   Render each plan from the API as a card:
   - Container: bg-white rounded-2xl shadow-sm p-5 mb-3
   - Plan title: text-lg font-bold text-slate-800
   - Created date: text-sm text-slate-400 (format as "Created Mar 20, 2026")
   - Progress section:
     - Progress bar: h-2 rounded-full bg-slate-100, with a teal-500 fill showing (completed_sessions / total_sessions) proportion
     - Progress text below bar: text-sm text-slate-500, e.g. "12 / 42 sessions completed"
   - Month indicator: text-xs text-slate-400, e.g. "Month 1 of 3 generated"
   - If current_month < total_months, show a small "Generate Next Month" button:
     - Style: text-sm text-teal-600 font-medium, with a ChevronRight icon
     - On click: call extendPlan(planId) from the API
     - Show a spinner on the button while loading
     - On success: refresh the plans list and show a toast "Month [N] generated! [X] new sessions added."

3. Empty state (if no plans):
   - Centered content with a large Sparkles icon (teal-300, size 48)
   - Text: "No plans yet" in text-lg font-medium text-slate-600
   - Subtext: "Create your first adaptive routine" in text-sm text-slate-400
   - Teal CTA button linking to /planner: "Create a Plan"

4. Tapping a plan card opens a plan detail view. This can be a new route /plans/:id or a slide-in panel. Show:
   - The plan title and high-level overview (month themes from high_level_plan)
   - All generated sessions grouped by month, then by week
   - Each session shown in a compact format: date, time, topic, status badge
   - Status badges: small colored pills (teal for completed, indigo for reshuffled, slate for pending)
```

---

## Step 8: Polish and Micro-Interactions

**Goal:** Add the finishing touches that make the demo impressive.

### Prompt 8.1 -- Animations and Transitions

```
Add these micro-interactions throughout the app to make it feel alive and polished:

1. RESILIENCE SCORE ANIMATION (Dashboard top bar):
   - When the score increases, animate the number counting up (old value to new value over 600ms, use requestAnimationFrame or a counter library)
   - Add a glow pulse around the score: a teal box-shadow that fades in and out over 1 second
   - When the increase came from a reshuffle action (Options B or C in Life Happened), make the glow indigo instead of teal
   - The Shield icon next to the score should do a brief scale-up-then-back animation (scale to 1.2, back to 1 over 400ms)

2. CARD COMPLETION EFFECT:
   - When a session is marked complete, the card should do a brief "pop" (scale to 1.02 then back to 1 over 300ms)
   - Then transition to the completed state (faded, teal border) over 500ms
   - Use transition-all duration-500 ease-in-out

3. CARD PUSH-BACK ANIMATION:
   - When a session is pushed back 2 hours, the card should slide down smoothly to its new position in the timeline
   - Use layout animation if available (Framer Motion's AnimatePresence would be ideal, but CSS transitions work too)

4. PAGE TRANSITIONS:
   - When switching between bottom nav tabs, use a subtle fade transition (opacity 0 to 1 over 200ms)
   - The active tab icon should have a brief scale animation when selected

5. LOADING STATES:
   - All loading spinners should be teal-500 and use a smooth spinning animation
   - Skeleton loading for cards: show 3 placeholder cards with a shimmer animation (bg-slate-100 with a moving gradient highlight) while data loads

6. PLAN GENERATION:
   - While waiting for AI response in the Planner, show an engaging typing indicator:
     Three dots that animate in a wave pattern (each dot bounces up with a staggered delay)
   - When the plan preview appears, animate it sliding in from the bottom with a slight fade

7. HAPTIC FEEDBACK:
   - On task completion, reshuffle confirmation, and plan creation: call navigator.vibrate(50) if available (wrap in a try-catch)

8. TOAST NOTIFICATIONS:
   - Use a toast system (shadcn/ui toast or sonner) for success/error messages
   - Toasts should appear at the top of the screen, styled with the calm design system (no harsh colors)
   - Success: bg-teal-50 border-teal-200 text-teal-800
   - Error: bg-amber-50 border-amber-200 text-amber-800 (amber, NOT red)
```

### Prompt 8.2 -- PWA Setup

```
Configure this app as a Progressive Web App so it feels native on mobile:

1. Add a manifest.json with:
   - name: "Adaptive Routines"
   - short_name: "Routines"
   - theme_color: "#0d9488" (teal-600)
   - background_color: "#f8fafc" (slate-50)
   - display: "standalone"
   - start_url: "/"
   - Generate simple placeholder icons (192x192 and 512x512)

2. Register a basic service worker for offline caching of the app shell

3. Add these meta tags in index.html:
   - viewport: width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no
   - apple-mobile-web-app-capable: yes
   - apple-mobile-web-app-status-bar-style: default
   - theme-color: #0d9488

4. The app should feel full-screen when added to the home screen on iOS and Android.
```

---

## Step 9: Demo Polish

**Goal:** Make sure the demo is smooth and impressive.

### Prompt 9.1 -- Demo-Ready Tweaks

```
Make these final adjustments for a hackathon demo:

1. BACKEND CONNECTIVITY:
   - If the backend is unreachable on any page, show a clean full-screen state:
     - Icon: WifiOff from lucide-react (slate-300, size 48)
     - Text: "Can't connect to the server" in text-lg text-slate-600
     - Subtext: "Make sure the backend is running on localhost:8000" in text-sm text-slate-400
     - A "Retry" button that re-attempts the API call
   - Don't show ugly error stack traces anywhere

2. SMOOTH NAVIGATION:
   - The bottom nav should highlight the current active tab with teal-500 color and a small dot indicator below the icon
   - Switching tabs should be instant (no page reload)
   - Use client-side routing (React Router)

3. RESPONSIVE BUT MOBILE-FIRST:
   - On desktop, center the content in a phone-sized container: max-w-md mx-auto with a min-h-screen and a subtle shadow to mimic a phone screen
   - This way the demo looks great whether shown on a phone or projected on a big screen

4. EMPTY STATES:
   - Dashboard with no sessions: friendly illustration area + "Your day is clear! Create a plan in the Planner tab." with arrow pointing to the nav
   - Plans with no plans: Sparkles icon + "No plans yet. Create your first adaptive routine!" with CTA button

5. QUICK WIN -- ADD A SPLASH/ONBOARDING:
   - When the app first loads (check localStorage for a "hasSeenOnboarding" flag), show a brief welcome screen:
     - Clean white background
     - App name "Adaptive Routines" in text-2xl font-bold text-slate-800
     - Tagline: "Turn goals into habits. Gracefully." in text-slate-500
     - Three small feature highlights (with icons):
       - Calendar icon: "AI-powered daily plans"
       - Shield icon: "Zero-guilt resilience scoring"
       - RefreshCw icon: "Graceful rescheduling"
     - "Get Started" button (teal) that sets the localStorage flag and navigates to /planner
   - This only shows once. After that, the app goes straight to the Dashboard.
```

---

## Implementation Order Summary

| Step | What You Build | Key Outcome |
|---|---|---|
| 1 | Design system | Consistent visual language |
| 2 | API service layer | Clean backend integration |
| 3 | Dashboard + Routine Cards | Main screen with live data |
| 4 | Complete + Life Happened | Core interaction loop works |
| 5 | Salvage the Day | End-of-day rescue feature |
| 6 | AI Planner chat | Two-tier plan generation with preview |
| 7 | Plans library | Browse and extend plans |
| 8 | Animations + PWA | Polish and native feel |
| 9 | Demo polish | Hackathon-ready presentation |

---

## Tips for Working with Lovable

1. **One prompt at a time.** Wait for Lovable to finish rendering before sending the next prompt. Review the output visually before continuing.

2. **Fix before moving forward.** If a step produces a bug or visual issue, describe the problem to Lovable and ask it to fix before moving on. Example: "The Routine Cards are too wide on mobile. Constrain them to max-w-md mx-auto."

3. **Test the API connection early.** After Step 2, you can test in the browser console: `import { getScore } from './lib/api'; getScore().then(console.log)`. If this works, all subsequent steps will work.

4. **The Planner step is the slowest.** Step 6 generates the most code. If Lovable struggles, split it: first build just the chat UI with a fake response, then add the real API call.

5. **Test on mobile.** After each step, open the Lovable preview on your phone to verify the mobile layout. The app is designed mobile-first.

6. **If CORS errors appear**, make sure the FastAPI backend has the CORS middleware configured with `allow_origins=["*"]`. This is in the backend spec.

7. **Keep the backend running** during all Lovable development. The Dashboard and Planner need live data to render correctly.
