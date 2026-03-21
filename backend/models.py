from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Field


# ---------------------------------------------------------------------------
# Table models
# ---------------------------------------------------------------------------

class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    resilience_score: int = Field(default=0)


class Plan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    prompt_used: str
    high_level_plan: str  # JSON string
    total_months: int
    current_month: int = Field(default=1)
    start_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RoutineSession(SQLModel, table=True):
    """Named RoutineSession to avoid collision with sqlmodel.Session."""
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="plan.id")
    scheduled_date: date
    scheduled_time: str  # "HH:MM" 24-hour
    duration_minutes: int = Field(default=30)
    contextual_topic: str
    mvr_description: str
    status: str = Field(default="pending")
    original_time: Optional[str] = None
    month_number: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class GeneratePlanRequest(BaseModel):
    prompt: str


class SessionOut(BaseModel):
    id: int
    plan_id: int
    plan_title: str = ""
    scheduled_date: date
    scheduled_time: str
    duration_minutes: int
    contextual_topic: str
    mvr_description: str
    status: str
    original_time: Optional[str] = None
    month_number: int


class SessionUpdateResponse(BaseModel):
    session: SessionOut
    points_earned: int
    resilience_score: int


class CascadeResponse(BaseModel):
    session: SessionOut
    shifted_count: int
    points_earned: int
    resilience_score: int


class SalvageResponse(BaseModel):
    salvaged_count: int
    points_earned: int
    resilience_score: int
    sessions: list[SessionOut]


class TodayResponse(BaseModel):
    date: date
    sessions: list[SessionOut]
    resilience_score: int


class PlanSummary(BaseModel):
    id: int
    title: str
    total_months: int
    current_month: int
    total_sessions: int
    completed_sessions: int
    created_at: datetime


class PlanDetail(BaseModel):
    id: int
    title: str
    total_months: int
    current_month: int
    start_date: date
    high_level_plan: dict
    sessions: list[SessionOut]


class GeneratePlanResponse(BaseModel):
    plan_id: int
    title: str
    total_months: int
    high_level_plan: dict
    first_month_sessions: list[SessionOut]


class ExtendPlanResponse(BaseModel):
    month_number: int
    theme: str
    sessions_created: int
    sessions: list[SessionOut]
