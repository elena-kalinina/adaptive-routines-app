"""
Seed script for demo data. Run from the backend/ directory:
    python seed.py

Populates the database with two plans and sessions spanning the current week,
giving the dashboard a realistic mix of statuses.
"""

import json
import os
import sys
from datetime import date, datetime, timedelta

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlmodel import Session, select
from database import engine, init_db
from models import UserProfile, Plan, RoutineSession

LEETCODE_HIGH_LEVEL = {
    "plan_title": "LeetCode Mastery",
    "total_months": 3,
    "schedule": {
        "days_per_week": 6,
        "excluded_days": ["Sunday"],
        "preferred_time": "17:00",
        "session_duration_minutes": 30,
    },
    "months": [
        {
            "month_number": 1,
            "theme": "Foundations & Core Patterns",
            "focus_areas": ["Arrays & Hashing", "Two Pointers", "Sliding Window", "Stack"],
            "difficulty_level": "beginner",
            "weekly_progression": [
                "Week 1: Arrays & Hashing fundamentals",
                "Week 2: Two Pointers pattern mastery",
                "Week 3: Sliding Window techniques",
                "Week 4: Stack-based problems & review",
            ],
            "key_milestones": [
                "Solve 20 easy/medium problems",
                "Recognize core patterns on sight",
            ],
        },
        {
            "month_number": 2,
            "theme": "Intermediate Patterns",
            "focus_areas": ["Binary Search", "Linked Lists", "Trees", "Graphs basics"],
            "difficulty_level": "intermediate",
            "weekly_progression": [
                "Week 1: Binary Search variations",
                "Week 2: Linked List manipulation",
                "Week 3: Binary Trees & BSTs",
                "Week 4: Graph traversal (BFS/DFS)",
            ],
            "key_milestones": [
                "Comfortable with medium-difficulty problems",
                "Can implement BFS/DFS from scratch",
            ],
        },
        {
            "month_number": 3,
            "theme": "Advanced & Contest Prep",
            "focus_areas": ["Dynamic Programming", "Greedy", "Backtracking", "Timed practice"],
            "difficulty_level": "advanced",
            "weekly_progression": [
                "Week 1: 1D Dynamic Programming",
                "Week 2: 2D DP & Greedy strategies",
                "Week 3: Backtracking & advanced patterns",
                "Week 4: Mock contests & review",
            ],
            "key_milestones": [
                "Solve DP problems independently",
                "Complete a mock contest in 90 minutes",
            ],
        },
    ],
}

MINDFULNESS_HIGH_LEVEL = {
    "plan_title": "Morning Mindfulness",
    "total_months": 2,
    "schedule": {
        "days_per_week": 5,
        "excluded_days": ["Saturday", "Sunday"],
        "preferred_time": "07:30",
        "session_duration_minutes": 15,
    },
    "months": [
        {
            "month_number": 1,
            "theme": "Building the Habit",
            "focus_areas": ["Breathing", "Body Scan", "Gratitude"],
            "difficulty_level": "beginner",
            "weekly_progression": [
                "Week 1: Basic breath awareness",
                "Week 2: Body scan meditation",
                "Week 3: Gratitude journaling",
                "Week 4: Combining techniques",
            ],
            "key_milestones": [
                "Meditate 5 days in a row",
                "Notice reduced morning anxiety",
            ],
        },
        {
            "month_number": 2,
            "theme": "Deepening Practice",
            "focus_areas": ["Visualization", "Loving-kindness", "Mindful movement"],
            "difficulty_level": "intermediate",
            "weekly_progression": [
                "Week 1: Guided visualization",
                "Week 2: Loving-kindness meditation",
                "Week 3: Mindful stretching & yoga",
                "Week 4: Freestyle practice",
            ],
            "key_milestones": [
                "15-minute unguided sessions",
                "Morning practice feels automatic",
            ],
        },
    ],
}


def seed():
    init_db()

    with Session(engine) as db:
        # Clear existing data
        for model in [RoutineSession, Plan, UserProfile]:
            for row in db.exec(select(model)).all():
                db.delete(row)
        db.commit()

        # User profile
        profile = UserProfile(id=1, resilience_score=47)
        db.add(profile)

        today = date.today()

        # ---- Plan 1: LeetCode Mastery ----
        plan1 = Plan(
            title="LeetCode Mastery",
            prompt_used="I want to practice LeetCode for 30 minutes every day at 5 PM except Sundays for 3 months",
            high_level_plan=json.dumps(LEETCODE_HIGH_LEVEL),
            total_months=3,
            current_month=1,
            start_date=today - timedelta(days=5),
        )
        db.add(plan1)
        db.commit()
        db.refresh(plan1)

        leetcode_sessions = [
            {
                "offset": -2,
                "time": "17:00",
                "topic": "Arrays: Two Sum & Contains Duplicate",
                "mvr": "Read one solution for Two Sum and trace the hash map approach",
                "status": "completed",
            },
            {
                "offset": -1,
                "time": "17:00",
                "topic": "Two Pointers: Valid Palindrome",
                "mvr": "Read one palindrome solution and identify the pointer movement",
                "status": "completed_mvr",
            },
            {
                "offset": 0,
                "time": "09:00",
                "topic": "Morning Review: Hash Map Patterns",
                "mvr": "Skim your notes on hash map patterns for 5 minutes",
                "status": "completed",
            },
            {
                "offset": 0,
                "time": "17:00",
                "topic": "Sliding Window: Maximum Subarray",
                "mvr": "Read one sliding window solution and note the window expansion logic",
                "status": "pending",
            },
            {
                "offset": 1,
                "time": "17:00",
                "topic": "Stack: Valid Parentheses & Min Stack",
                "mvr": "Write pseudocode for Valid Parentheses on paper",
                "status": "pending",
            },
            {
                "offset": 2,
                "time": "17:00",
                "topic": "Binary Search: Search Insert Position",
                "mvr": "Read one binary search solution and trace the mid-point logic",
                "status": "pending",
            },
        ]

        for s in leetcode_sessions:
            db.add(
                RoutineSession(
                    plan_id=plan1.id,
                    scheduled_date=today + timedelta(days=s["offset"]),
                    scheduled_time=s["time"],
                    duration_minutes=30,
                    contextual_topic=s["topic"],
                    mvr_description=s["mvr"],
                    status=s["status"],
                    month_number=1,
                )
            )

        # ---- Plan 2: Morning Mindfulness ----
        plan2 = Plan(
            title="Morning Mindfulness",
            prompt_used="I want a 15-minute morning mindfulness routine at 7:30 AM on weekdays for 2 months",
            high_level_plan=json.dumps(MINDFULNESS_HIGH_LEVEL),
            total_months=2,
            current_month=1,
            start_date=today - timedelta(days=3),
        )
        db.add(plan2)
        db.commit()
        db.refresh(plan2)

        mindfulness_sessions = [
            {
                "offset": -1,
                "time": "07:30",
                "topic": "4-7-8 Breathing: Calm Your Nervous System",
                "mvr": "Do three slow breaths right now, inhale 4 counts, hold 7, exhale 8",
                "status": "completed",
            },
            {
                "offset": 0,
                "time": "07:30",
                "topic": "Body Scan: Release Morning Tension",
                "mvr": "Sit still for 2 minutes and notice where you feel tight",
                "status": "pending",
            },
            {
                "offset": 1,
                "time": "07:30",
                "topic": "Gratitude Journaling: Three Good Things",
                "mvr": "Write down one thing you're grateful for today",
                "status": "pending",
            },
        ]

        for s in mindfulness_sessions:
            db.add(
                RoutineSession(
                    plan_id=plan2.id,
                    scheduled_date=today + timedelta(days=s["offset"]),
                    scheduled_time=s["time"],
                    duration_minutes=15,
                    contextual_topic=s["topic"],
                    mvr_description=s["mvr"],
                    status=s["status"],
                    month_number=1,
                )
            )

        db.commit()
        print(f"Seeded database with 2 plans and {len(leetcode_sessions) + len(mindfulness_sessions)} sessions.")
        print(f"Resilience score: {profile.resilience_score}")
        print(f"Today ({today}): {sum(1 for s in leetcode_sessions + mindfulness_sessions if s['offset'] == 0)} sessions")


if __name__ == "__main__":
    seed()
