import json
import os
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from llm import call_gemini
from models import (
    Plan,
    RoutineSession,
    GeneratePlanRequest,
    GeneratePlanResponse,
    PlanSummary,
    PlanDetail,
    ExtendPlanResponse,
    SessionOut,
)
from prompts import TIER1_HIGH_LEVEL, TIER2_MONTHLY_DETAIL

router = APIRouter(prefix="/api/plans", tags=["plans"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.0-pro")


def _session_to_out(s: RoutineSession, plan_title: str = "") -> SessionOut:
    return SessionOut(
        id=s.id,
        plan_id=s.plan_id,
        plan_title=plan_title,
        scheduled_date=s.scheduled_date,
        scheduled_time=s.scheduled_time,
        duration_minutes=s.duration_minutes,
        contextual_topic=s.contextual_topic,
        mvr_description=s.mvr_description,
        status=s.status,
        original_time=s.original_time,
        month_number=s.month_number,
    )


def _build_tier2_prompt(high_level: dict, month_number: int, month_start: date) -> str:
    month_info = high_level["months"][month_number - 1]
    schedule = high_level["schedule"]
    return TIER2_MONTHLY_DETAIL.format(
        high_level_plan_json=json.dumps(high_level, indent=2),
        month_number=month_number,
        month_theme=month_info["theme"],
        focus_areas=", ".join(month_info["focus_areas"]),
        weekly_progression="\n".join(month_info["weekly_progression"]),
        month_start_date=month_start.isoformat(),
        days_per_week=schedule["days_per_week"],
        excluded_days=", ".join(schedule.get("excluded_days", [])),
        preferred_time=schedule["preferred_time"],
        duration_minutes=schedule["session_duration_minutes"],
    )


def _insert_sessions(
    db: Session,
    plan_id: int,
    sessions_data: list[dict],
    month_number: int,
    default_duration: int,
) -> list[RoutineSession]:
    rows = []
    for s in sessions_data:
        row = RoutineSession(
            plan_id=plan_id,
            scheduled_date=date.fromisoformat(s["date"]),
            scheduled_time=s["time"],
            duration_minutes=s.get("duration_minutes", default_duration),
            contextual_topic=s["topic"],
            mvr_description=s["mvr"],
            status="pending",
            month_number=month_number,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows


# ---- Endpoints -----------------------------------------------------------


@router.post("/generate", response_model=GeneratePlanResponse)
async def generate_plan(body: GeneratePlanRequest, db: Session = Depends(get_session)):
    if not GEMINI_API_KEY:
        raise HTTPException(500, "GEMINI_API_KEY not configured")

    # Tier 1: high-level plan
    tier1_prompt = TIER1_HIGH_LEVEL.format(user_prompt=body.prompt)
    high_level = await call_gemini(tier1_prompt, GEMINI_API_KEY, GEMINI_MODEL)

    total_months = high_level.get("total_months", len(high_level.get("months", [])))
    schedule = high_level.get("schedule", {})
    duration = schedule.get("session_duration_minutes", 30)

    # Tier 2: first month detail
    today = date.today()
    tier2_prompt = _build_tier2_prompt(high_level, 1, today)
    month1 = await call_gemini(tier2_prompt, GEMINI_API_KEY, GEMINI_MODEL)

    sessions_data = month1.get("sessions", [])
    start_date = (
        date.fromisoformat(sessions_data[0]["date"]) if sessions_data else today
    )

    plan = Plan(
        title=high_level.get("plan_title", "My Plan"),
        prompt_used=body.prompt,
        high_level_plan=json.dumps(high_level),
        total_months=total_months,
        current_month=1,
        start_date=start_date,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    rows = _insert_sessions(db, plan.id, sessions_data, 1, duration)

    return GeneratePlanResponse(
        plan_id=plan.id,
        title=plan.title,
        total_months=total_months,
        high_level_plan=high_level,
        first_month_sessions=[_session_to_out(r, plan.title) for r in rows],
    )


@router.get("", response_model=list[PlanSummary])
def list_plans(db: Session = Depends(get_session)):
    plans = db.exec(select(Plan).order_by(Plan.created_at.desc())).all()
    results = []
    for p in plans:
        sessions = db.exec(
            select(RoutineSession).where(RoutineSession.plan_id == p.id)
        ).all()
        total = len(sessions)
        completed = sum(
            1 for s in sessions if s.status in ("completed", "completed_mvr")
        )
        results.append(
            PlanSummary(
                id=p.id,
                title=p.title,
                total_months=p.total_months,
                current_month=p.current_month,
                total_sessions=total,
                completed_sessions=completed,
                created_at=p.created_at,
            )
        )
    return results


@router.get("/{plan_id}", response_model=PlanDetail)
def get_plan(plan_id: int, db: Session = Depends(get_session)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    sessions = db.exec(
        select(RoutineSession)
        .where(RoutineSession.plan_id == plan_id)
        .order_by(RoutineSession.scheduled_date, RoutineSession.scheduled_time)
    ).all()

    return PlanDetail(
        id=plan.id,
        title=plan.title,
        total_months=plan.total_months,
        current_month=plan.current_month,
        start_date=plan.start_date,
        high_level_plan=json.loads(plan.high_level_plan),
        sessions=[_session_to_out(s, plan.title) for s in sessions],
    )


@router.post("/{plan_id}/extend", response_model=ExtendPlanResponse)
async def extend_plan(plan_id: int, db: Session = Depends(get_session)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    next_month = plan.current_month + 1
    if next_month > plan.total_months:
        raise HTTPException(400, "All months have already been generated")

    high_level = json.loads(plan.high_level_plan)
    schedule = high_level.get("schedule", {})
    duration = schedule.get("session_duration_minutes", 30)

    last_session = db.exec(
        select(RoutineSession)
        .where(RoutineSession.plan_id == plan_id)
        .order_by(RoutineSession.scheduled_date.desc())
    ).first()
    month_start = (
        last_session.scheduled_date + timedelta(days=1) if last_session else date.today()
    )

    tier2_prompt = _build_tier2_prompt(high_level, next_month, month_start)
    month_data = await call_gemini(tier2_prompt, GEMINI_API_KEY, GEMINI_MODEL)

    sessions_data = month_data.get("sessions", [])
    rows = _insert_sessions(db, plan.id, sessions_data, next_month, duration)

    plan.current_month = next_month
    db.add(plan)
    db.commit()

    month_info = high_level["months"][next_month - 1]

    return ExtendPlanResponse(
        month_number=next_month,
        theme=month_info["theme"],
        sessions_created=len(rows),
        sessions=[_session_to_out(r, plan.title) for r in rows],
    )


@router.delete("/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_session)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    sessions = db.exec(
        select(RoutineSession).where(RoutineSession.plan_id == plan_id)
    ).all()
    for s in sessions:
        db.delete(s)

    db.delete(plan)
    db.commit()
    return {"detail": "Plan deleted"}
