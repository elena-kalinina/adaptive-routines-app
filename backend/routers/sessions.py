from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import (
    Plan,
    RoutineSession,
    UserProfile,
    SessionOut,
    SessionUpdateResponse,
    CascadeResponse,
    SalvageResponse,
    TodayResponse,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _get_profile(db: Session) -> UserProfile:
    profile = db.get(UserProfile, 1)
    if not profile:
        profile = UserProfile(id=1, resilience_score=0)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _add_points(db: Session, points: int) -> int:
    profile = _get_profile(db)
    profile.resilience_score += points
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile.resilience_score


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


def _get_pending_session(db: Session, session_id: int) -> RoutineSession:
    s = db.get(RoutineSession, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    if s.status != "pending":
        raise HTTPException(400, f"Session is already '{s.status}', expected 'pending'")
    return s


def _plan_title(db: Session, plan_id: int) -> str:
    plan = db.get(Plan, plan_id)
    return plan.title if plan else ""


# ---- Endpoints -----------------------------------------------------------


@router.get("/today", response_model=TodayResponse)
def get_today(db: Session = Depends(get_session)):
    today = date.today()
    sessions = db.exec(
        select(RoutineSession)
        .where(RoutineSession.scheduled_date == today)
        .order_by(RoutineSession.scheduled_time)
    ).all()

    profile = _get_profile(db)

    plan_cache: dict[int, str] = {}
    out = []
    for s in sessions:
        if s.plan_id not in plan_cache:
            plan_cache[s.plan_id] = _plan_title(db, s.plan_id)
        out.append(_session_to_out(s, plan_cache[s.plan_id]))

    return TodayResponse(date=today, sessions=out, resilience_score=profile.resilience_score)


@router.patch("/{session_id}/complete", response_model=SessionUpdateResponse)
def complete_session(session_id: int, db: Session = Depends(get_session)):
    s = _get_pending_session(db, session_id)
    s.status = "completed"
    db.add(s)
    db.commit()
    db.refresh(s)

    new_score = _add_points(db, 10)
    return SessionUpdateResponse(
        session=_session_to_out(s, _plan_title(db, s.plan_id)),
        points_earned=10,
        resilience_score=new_score,
    )


@router.patch("/{session_id}/complete-mvr", response_model=SessionUpdateResponse)
def complete_mvr(session_id: int, db: Session = Depends(get_session)):
    s = _get_pending_session(db, session_id)
    s.status = "completed_mvr"
    db.add(s)
    db.commit()
    db.refresh(s)

    new_score = _add_points(db, 5)
    return SessionUpdateResponse(
        session=_session_to_out(s, _plan_title(db, s.plan_id)),
        points_earned=5,
        resilience_score=new_score,
    )


@router.patch("/{session_id}/push-back", response_model=SessionUpdateResponse)
def push_back(session_id: int, db: Session = Depends(get_session)):
    s = _get_pending_session(db, session_id)

    s.original_time = s.scheduled_time
    hour, minute = map(int, s.scheduled_time.split(":"))
    new_hour = hour + 2
    if new_hour >= 24:
        new_hour = 23
        minute = 59
    s.scheduled_time = f"{new_hour:02d}:{minute:02d}"

    db.add(s)
    db.commit()
    db.refresh(s)

    new_score = _add_points(db, 2)
    return SessionUpdateResponse(
        session=_session_to_out(s, _plan_title(db, s.plan_id)),
        points_earned=2,
        resilience_score=new_score,
    )


@router.patch("/{session_id}/cascade", response_model=CascadeResponse)
def cascade_session(session_id: int, db: Session = Depends(get_session)):
    s = _get_pending_session(db, session_id)

    s.original_time = s.scheduled_time
    s.status = "reshuffled"
    db.add(s)

    # Shift all future pending sessions for same plan forward by 1 day
    future = db.exec(
        select(RoutineSession)
        .where(
            RoutineSession.plan_id == s.plan_id,
            RoutineSession.id != s.id,
            RoutineSession.status == "pending",
            RoutineSession.scheduled_date >= s.scheduled_date,
        )
        .order_by(RoutineSession.scheduled_date, RoutineSession.scheduled_time)
    ).all()

    for fs in future:
        fs.scheduled_date = fs.scheduled_date + timedelta(days=1)
        db.add(fs)

    db.commit()
    db.refresh(s)

    new_score = _add_points(db, 2)
    return CascadeResponse(
        session=_session_to_out(s, _plan_title(db, s.plan_id)),
        shifted_count=len(future),
        points_earned=2,
        resilience_score=new_score,
    )


@router.post("/salvage", response_model=SalvageResponse)
def salvage_day(db: Session = Depends(get_session)):
    today = date.today()
    pending = db.exec(
        select(RoutineSession)
        .where(
            RoutineSession.scheduled_date == today,
            RoutineSession.status == "pending",
        )
    ).all()

    if not pending:
        raise HTTPException(400, "No pending sessions to salvage today")

    plan_cache: dict[int, str] = {}
    for s in pending:
        s.status = "completed_mvr"
        db.add(s)
        if s.plan_id not in plan_cache:
            plan_cache[s.plan_id] = _plan_title(db, s.plan_id)

    db.commit()

    points = 5 * len(pending)
    new_score = _add_points(db, points)

    out = []
    for s in pending:
        db.refresh(s)
        out.append(_session_to_out(s, plan_cache[s.plan_id]))

    return SalvageResponse(
        salvaged_count=len(pending),
        points_earned=points,
        resilience_score=new_score,
        sessions=out,
    )
