# Adaptive Routines App -- Lovable Implementation Plan

This document contains the exact prompts to paste into Lovable, in order, to iteratively build the Adaptive Routines App. Each step builds on the previous one. Wait for Lovable to finish each step before moving to the next.

---

## Pre-Flight Checklist

Before starting in Lovable:

1. **Create a Supabase project** at [supabase.com](https://supabase.com)
2. **Get a Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey) (free tier is generous)
3. **Create a new Lovable project** -- name it "Adaptive Routines"
4. **Connect Supabase** to Lovable using the Supabase integration (Project URL + anon key)

---

## Step 1: Design System Foundation

**Goal:** Establish the visual language before building any features.

### Prompt 1.1 -- Global Design Tokens

```
Set up a mobile-first React + Tailwind web app with the following design system.
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

## Step 2: Dashboard Layout and Routine Cards

**Goal:** Build the main screen -- the Today timeline.

### Prompt 2.1 -- Dashboard Structure

```
Build the main Dashboard page at route "/". This is a mobile-first daily timeline view. Layout from top to bottom:

1. TOP BAR (sticky):
   - Left side: Today's date formatted as "Sunday, Mar 8" (use the actual current date)
   - Right side: A "Resilience Score" showing a number (hardcode 42 for now) with a small shield icon from lucide-react. Style it with text-teal-500 font-bold.

2. TIMELINE BODY (scrollable, takes remaining height):
   - A thin vertical line on the left margin (border-l-2 border-slate-200) with small dots at each hour
   - A horizontal "current time" indicator line that spans the full width at the position matching the current time. Make it a thin teal-400 line with a subtle glow (use box-shadow).

3. ROUTINE CARDS attached to the timeline:
   Create 4 sample cards with hardcoded data for testing:
   - Card 1: 9:00 AM, "Morning Breathing Exercise", plan "Mindfulness Journey", status: completed
   - Card 2: 12:00 PM, "Sliding Window Problems", plan "LeetCode Mastery", status: pending
   - Card 3: 3:00 PM, "3k Easy Pace Run", plan "Marathon Prep", status: reshuffled
   - Card 4: 5:00 PM, "Two Pointers Practice", plan "LeetCode Mastery", status: pending

   Each Routine Card design:
   - Container: bg-white rounded-2xl shadow-sm p-4, slight left border color based on status
   - Text hierarchy inside:
     - Time: text-sm font-medium text-slate-400 (e.g., "5:00 PM")
     - Topic: text-lg font-bold text-slate-800 (e.g., "Two Pointers Practice") -- THIS is the primary visual element
     - Plan: text-xs text-slate-400 (e.g., "From: LeetCode Mastery")
   - Two icon buttons on the right side of each card:
     - CheckCircle icon (teal-500) for "Complete"
     - RefreshCw icon (indigo-400) for "Life Happened"
   - Status-based styling:
     - completed: teal-500 left border, content slightly faded, checkmark overlay
     - reshuffled: indigo-400 left border, shuffle icon badge
     - pending: no colored border, full opacity
     - missed: slate-300 everything, most faded

4. BOTTOM NAVIGATION BAR (sticky):
   - Three tabs with lucide-react icons:
     - "Today" (CalendarDays icon) -- active by default, teal-500
     - "Plans" (List icon)
     - "Planner" (Sparkles icon)
   - Style: bg-white border-t border-slate-100, icons centered with small label text below

Make sure the whole page scrolls naturally on mobile. Use padding and spacing that feels spacious, not cramped.
```

---

## Step 3: Supabase Backend

**Goal:** Set up the database and connect the dashboard to real data.

### Prompt 3.1 -- Database Tables

```
Connect this app to Supabase. Create the following database tables using Supabase migrations:

TABLE: profiles
- id: UUID, primary key, references auth.users(id)
- display_name: TEXT, nullable
- resilience_score: INTEGER, default 0
- created_at: TIMESTAMPTZ, default now()

TABLE: plans
- id: UUID, primary key, default gen_random_uuid()
- user_id: UUID, not null, references profiles(id)
- title: TEXT, not null
- prompt_used: TEXT, not null
- total_sessions: INTEGER, default 0
- created_at: TIMESTAMPTZ, default now()

TABLE: sessions
- id: UUID, primary key, default gen_random_uuid()
- plan_id: UUID, not null, references plans(id) on delete cascade
- user_id: UUID, not null, references profiles(id)
- scheduled_time: TIMESTAMPTZ, not null
- duration_minutes: INTEGER, default 30
- contextual_topic: TEXT, not null
- mvr_description: TEXT, not null
- status: TEXT, default 'pending', check constraint for values: 'pending', 'completed', 'completed_mvr', 'reshuffled', 'missed'
- original_time: TIMESTAMPTZ, nullable
- created_at: TIMESTAMPTZ, default now()

Enable Row Level Security on ALL tables. Policies:
- profiles: Users can read and update only their own row (where id = auth.uid())
- plans: Users can CRUD only their own rows (where user_id = auth.uid())
- sessions: Users can CRUD only their own rows (where user_id = auth.uid())

Also create a database trigger: when a new user signs up (insert into auth.users), automatically create a row in the profiles table with their id and resilience_score = 0.
```

### Prompt 3.2 -- Wire Dashboard to Supabase

```
Now connect the Dashboard to real Supabase data:

1. Add Supabase Auth -- simple email/password sign-up and login. Create a clean login/signup page at "/auth" with the same calm design system (rounded inputs, teal button, no harsh colors). Redirect to "/" after login.

2. Replace the hardcoded Routine Cards on the Dashboard with a real query:
   - Fetch all sessions for the logged-in user where scheduled_time falls on today's date
   - Order by scheduled_time ascending
   - Display them as Routine Cards (same design as before)
   - If no sessions exist for today, show a friendly empty state: "No routines today. Visit the Planner to create one!" with a button linking to "/planner"

3. Fetch the user's resilience_score from the profiles table and display it in the top bar.

4. For now, the Complete and Life Happened buttons don't need to work yet -- we'll add that next.
```

---

## Step 4: Complete and Life Happened Logic

**Goal:** Make the core interaction loop functional.

### Prompt 4.1 -- Complete Button

```
Implement the "Complete" button on each Routine Card:

When a user clicks the CheckCircle (Complete) button on a pending session:
1. Update that session's status to 'completed' in Supabase
2. Add 10 to the user's resilience_score in the profiles table
3. Animate the card: add a teal-500 left border, fade the content slightly, show a checkmark
4. The Resilience Score in the header should animate up (count from old value to new value over 500ms)
5. Trigger a subtle glow/pulse on the score number using a teal box-shadow animation

The button should be disabled for sessions that are already completed, completed_mvr, or missed.
```

### Prompt 4.2 -- Life Happened Bottom Sheet

```
Now build the "Life Happened" flow:

When a user clicks the RefreshCw (Life Happened) button on a pending session, open a Bottom Sheet / Drawer that slides up from the bottom of the screen. Do NOT use a centered modal popup.

Bottom Sheet content:
- A small drag handle at the top
- Header: "No stress. How do we adjust?" in text-lg font-bold text-slate-700
- Subheader showing the session info: "[Topic] at [Time]" in text-sm text-slate-400
- Three option cards stacked vertically, each as a tappable card (bg-slate-50 rounded-2xl p-4):

  Option A -- "Do the Minimum":
  - Icon: Zap from lucide-react (amber-500)
  - Title: "Downgrade to MVR (5 mins)" in font-semibold
  - Subtitle: Show the session's actual mvr_description text from the database
  - Badge: "+5 resilience" in a small teal pill

  Option B -- "Push Back 2 Hours":
  - Icon: Clock from lucide-react (indigo-400)
  - Title: "Push back 2 hours" in font-semibold
  - Subtitle: "Reschedule to [calculated new time]"
  - Badge: "+2 resilience" in a small teal pill

  Option C -- "Skip & Cascade":
  - Icon: ArrowRight from lucide-react (indigo-400)
  - Title: "Skip and shift everything" in font-semibold
  - Subtitle: "This session moves to the next free slot"
  - Badge: "+2 resilience" in a small teal pill

Implement the logic for each option:

Option A (MVR):
- Set session status to 'completed_mvr'
- Add 5 to resilience_score
- Close drawer, update card to show indigo left border

Option B (Push Back):
- Save current scheduled_time into original_time
- Update scheduled_time to +2 hours
- Add 2 to resilience_score
- Close drawer, card should animate/move to its new position in the timeline

Option C (Cascade):
- Set this session's status to 'reshuffled'
- Save current time to original_time
- Find all future pending sessions for the same plan, ordered by scheduled_time
- Push each one forward by the duration of this session
- Add 2 to resilience_score
- Close drawer, refresh timeline

After any option, show the glow animation on the Resilience Score.
```

---

## Step 5: Salvage the Day

**Goal:** Build the end-of-day rescue feature.

### Prompt 5.1 -- Salvage Day FAB

```
Add a "Salvage the Day" floating action button to the Dashboard:

Logic:
- After 6:00 PM local time, check if there are any sessions with status 'pending' for today
- If yes, show a floating button at the bottom center of the screen (above the bottom nav)
- Button style: bg-teal-500 text-white rounded-full shadow-lg px-6 py-3 with a subtle pulse animation
- Button text: "Salvage the Day" with a Sparkles icon

When tapped:
1. Collect all today's pending sessions
2. Show a Bottom Sheet with a summary:
   - Header: "Quick Catch-Up (15 minutes)"
   - List all the MVR descriptions from those pending sessions as a bulleted checklist
   - Example: "- Read one LeetCode solution" / "- Put on shoes, walk one block"
   - A big teal "I Did It" button at the bottom
3. When "I Did It" is tapped:
   - Set all those sessions' status to 'completed_mvr'
   - Add 5 points per session to resilience_score
   - Close the sheet and update the timeline
   - Show the Resilience Score glow animation
```

---

## Step 6: AI Planner

**Goal:** Build the AI-powered plan generation page.

### Prompt 6.1 -- Planner Chat UI

```
Create the AI Planner page at route "/planner" (accessible from the bottom nav "Planner" tab).

Layout -- make it look like a chat interface (similar to ChatGPT or iMessage):

1. Top bar: "AI Planner" title with a Sparkles icon

2. Chat area (scrollable, takes remaining space):
   - Start with a single AI message bubble (left-aligned, bg-white rounded-2xl p-4 shadow-sm):
     "Hi! Tell me about a habit or skill you want to build. Include how often, what time, and for how long. For example: 'I want to practice guitar for 20 minutes every evening at 7 PM for 2 months.'"

3. Input area (sticky bottom):
   - Text input field: bg-slate-100 rounded-2xl p-4, placeholder "Describe your goal and schedule..."
   - Send button: teal-500 circle with Send icon (ArrowUp)

When the user types a message and hits send:
- Show their message as a right-aligned bubble (bg-teal-500 text-white rounded-2xl)
- Show a typing indicator (three animated dots in an AI bubble)
- Call a Supabase Edge Function that:
  a. Receives the user's prompt
  b. Sends it to the Google Gemini API (model: gemini-3.1-pro) with this prompt:

PROMPT (sent as the user message, since Gemini doesn't have a separate system role in the REST API):
"You are an expert habit coach and schedule planner. The user will describe a goal, preferred schedule, and duration. Return a JSON object with this structure:
{
  \"plan_title\": \"A short motivating name\",
  \"sessions\": [
    {
      \"date\": \"YYYY-MM-DD\",
      \"time\": \"HH:MM\",
      \"duration_minutes\": 30,
      \"topic\": \"Specific progressive topic. Be concrete -- not 'Practice guitar' but 'Learn Am and Em chord transitions'\",
      \"mvr\": \"A minimum viable version achievable in under 5 minutes -- e.g., 'Strum each chord 10 times'\"
    }
  ]
}
Rules: Generate sessions for the FULL duration. Make topics progressive. Each MVR must be genuinely doable in under 5 minutes. Respect day exclusions. Vary topics to prevent monotony.

USER GOAL: [insert user prompt here]"

  c. The Gemini API must be called with generationConfig: { responseMimeType: "application/json", temperature: 0.7 } to enforce JSON output
  d. Parse the response from response.candidates[0].content.parts[0].text
  e. Returns the parsed JSON plan to the client

After receiving the AI response, render it as a PLAN PREVIEW COMPONENT (not raw text):
- Plan title in text-xl font-bold
- A horizontal scrollable row of week chips: "Week 1", "Week 2", etc. (bg-slate-100 rounded-xl px-3 py-1)
- Below that, show the first 5 session cards as a preview:
  - Each shows: date, topic, and MVR in a compact card format
- A count badge: "42 sessions over 3 months" (or whatever the actual count is)
- A large CTA button: bg-teal-500 text-white rounded-2xl py-4 w-full font-bold text-lg
  Text: "Looks Good, Add to Calendar"

When "Looks Good, Add to Calendar" is clicked:
1. Create a new row in the plans table with the title and original prompt
2. Batch insert all sessions into the sessions table linked to that plan
3. Show a success message: "Plan added! Check your timeline."
4. Navigate to the Dashboard "/"
```

### Prompt 6.2 -- Edge Function

```
Create a Supabase Edge Function called "generate-plan" that:

1. Accepts a POST request with JSON body: { "prompt": "user's goal description" }
2. Validates the user is authenticated (check the Authorization header JWT)
3. Calls the Google Gemini API using a direct REST call (no SDK needed in Deno):

   URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro:generateContent?key=${GEMINI_API_KEY}
   Method: POST
   Headers: { "Content-Type": "application/json" }
   Body: {
     "contents": [
       {
         "role": "user",
         "parts": [{ "text": "<system prompt instructions> + USER GOAL: <user's prompt>" }]
       }
     ],
     "generationConfig": {
       "responseMimeType": "application/json",
       "temperature": 0.7
     }
   }

4. Extracts the JSON string from: response.candidates[0].content.parts[0].text
5. Parses that string as JSON and returns the plan object to the client

Store the Gemini API key as a Supabase secret named GEMINI_API_KEY (not in client code).
Handle errors gracefully -- if Gemini returns malformed JSON, retry once, then return a friendly error message.
```

---

## Step 7: Plans Library

**Goal:** Let users view and manage their plans.

### Prompt 7.1 -- Plans Page

```
Create a Plans page at route "/plans" (accessible from bottom nav "Plans" tab).

Layout:
1. Header: "Your Plans" in text-xl font-bold

2. Plan Cards (vertical list):
   - Fetch all plans for the current user from Supabase, ordered by created_at desc
   - Each card (bg-white rounded-2xl shadow-sm p-4):
     - Plan title in font-bold text-slate-800
     - Created date in text-sm text-slate-400
     - Progress bar showing (completed + completed_mvr sessions) / total sessions
     - Progress text: "12 / 42 sessions completed"
     - The progress bar should use teal-500 for the filled portion

3. Empty state:
   - If no plans exist, show a friendly message: "No plans yet. Let's create one!"
   - Button linking to "/planner"

4. Tapping a plan card navigates to a plan detail view showing ALL sessions for that plan in a list, with their dates, topics, and statuses. Use the same Routine Card design but in a compact version.
```

---

## Step 8: Polish and Micro-Interactions

**Goal:** Add the finishing touches that make the app feel alive.

### Prompt 8.1 -- Animations and Haptics

```
Add these micro-interactions throughout the app:

1. SWIPE GESTURES on Routine Cards (Dashboard only):
   - Swipe right: triggers the Complete action (same as tapping the check button)
   - Swipe left: opens the Life Happened bottom sheet
   - Show a teal background when swiping right, indigo background when swiping left
   - Use a swipe gesture library compatible with React

2. RESILIENCE SCORE ANIMATION:
   - When the score increases, animate the number counting up over 500ms
   - Add a soft glow pulse (teal box-shadow that fades) around the score on increase
   - When the increase came from a reshuffle, make the glow indigo instead of teal

3. CARD TRANSITIONS:
   - When a session is pushed back 2 hours, animate the card sliding down to its new position (transition-all duration-500 ease-in-out)
   - When a session is completed, add a brief scale-down-then-up "pop" effect

4. HAPTIC FEEDBACK:
   - On task completion, reshuffle confirmation, and plan creation: call navigator.vibrate(50) if available

5. PAGE TRANSITIONS:
   - Use subtle fade transitions when switching between bottom nav tabs
```

### Prompt 8.2 -- PWA Setup

```
Configure this app as a Progressive Web App:

1. Add a manifest.json with:
   - name: "Adaptive Routines"
   - short_name: "Routines"
   - theme_color: "#0d9488" (teal-600)
   - background_color: "#f8fafc" (slate-50)
   - display: "standalone"
   - Appropriate icons (generate simple placeholder icons)

2. Register a basic service worker for offline caching of the app shell

3. Add the appropriate meta tags in index.html for mobile:
   - viewport meta for mobile scaling
   - apple-mobile-web-app-capable
   - theme-color meta tag
```

---

## Step 9: Testing and Seed Data

**Goal:** Make sure everything works end-to-end.

### Prompt 9.1 -- Seed Data and QA

```
Help me test the app by:

1. Creating a seed function (or SQL script) that inserts test data for a logged-in user:
   - 1 plan called "LeetCode Mastery" with prompt "LeetCode 30 mins daily at 5 PM for 1 month"
   - 7 sessions for this week, each at 5:00 PM, with these topics and statuses:
     - Monday: "Arrays: Two Sum & Contains Duplicate" (completed)
     - Tuesday: "Two Pointers: Valid Palindrome" (completed_mvr)
     - Wednesday: "Sliding Window: Max Subarray" (reshuffled, moved to Thursday 7 PM)
     - Thursday: "Sliding Window: Max Subarray" + "Stack: Valid Parentheses" (pending)
     - Friday: "Binary Search: Search Insert Position" (pending)
     - Saturday: "Linked List: Reverse Linked List" (pending)
   - Each session should have a realistic mvr_description

2. Set the user's resilience_score to 42

This will let me verify the dashboard timeline, status colors, and all interactions work correctly.
```

---

## Implementation Order Summary

| Step | What You Build | Key Outcome |
|---|---|---|
| 1 | Design system | Consistent visual language |
| 2 | Dashboard + Routine Cards | Main screen with timeline UI |
| 3 | Supabase tables + Auth + data binding | Real backend, login flow |
| 4 | Complete + Life Happened logic | Core interaction loop works |
| 5 | Salvage the Day FAB | End-of-day rescue feature |
| 6 | AI Planner + Edge Function | Users can generate plans via AI |
| 7 | Plans library | Users can browse and track plans |
| 8 | Animations, swipes, PWA | Polish and native-app feel |
| 9 | Seed data + QA | End-to-end verification |

---

## Tips for Working with Lovable

1. **One prompt at a time.** Wait for Lovable to finish rendering before sending the next prompt. Review the output visually before proceeding.

2. **Fix before moving forward.** If a step produces a bug or visual issue, describe the problem to Lovable and fix it before continuing. Example: "The Routine Cards are too wide on mobile. Please constrain them to max-w-md mx-auto."

3. **Use the Supabase integration early.** Connect Supabase in Step 3 and don't delay it. Data-connected UI is much easier to debug than mocked-up UI.

4. **Keep the Edge Function simple.** If the Edge Function fails to deploy, ask Lovable to show you the function code so you can deploy it manually via the Supabase dashboard. Store your Gemini API key as a Supabase secret named `GEMINI_API_KEY`.

5. **Test on mobile.** After each step, open the Lovable preview on your phone browser to verify the mobile layout. The app is designed mobile-first.
