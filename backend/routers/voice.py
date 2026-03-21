import os
from datetime import date, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from database import get_session
from models import RoutineSession, UserProfile

router = APIRouter(prefix="/api/voice", tags=["voice"])

SLNG_API_KEY = os.getenv("SLNG_API_KEY", "")
SLNG_TTS_ENDPOINT = os.getenv("SLNG_TTS_ENDPOINT", "slng/deepgram/aura:2-en")
SLNG_TTS_VOICE = os.getenv("SLNG_TTS_VOICE", "aura-2-theia-en")
SLNG_TTS_URL = "https://api.slng.ai/v1/tts/{endpoint}"


def _format_time_12h(time_str: str) -> str:
    hour, minute = map(int, time_str.split(":"))
    suffix = "AM" if hour < 12 else "PM"
    display_hour = hour % 12 or 12
    if minute == 0:
        return f"{display_hour} {suffix}"
    return f"{display_hour}:{minute:02d} {suffix}"


def build_briefing_text(sessions: list[RoutineSession], score: int) -> str:
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
        n = len(completed)
        parts.append(
            f"You've already knocked out {n} session{'s' if n != 1 else ''} today. Nice work!"
        )

    if pending:
        n = len(pending)
        parts.append(f"You have {n} session{'s' if n != 1 else ''} coming up.")
        for s in pending[:3]:
            parts.append(f"At {_format_time_12h(s.scheduled_time)}: {s.contextual_topic}.")
        if len(pending) > 3:
            parts.append(f"Plus {len(pending) - 3} more later.")

    parts.append(
        f"Your resilience score is {score}. "
        f"Remember, even five minutes counts. You've got this!"
    )

    return " ".join(parts)


async def _call_slng_tts(text: str) -> bytes:
    url = SLNG_TTS_URL.format(endpoint=SLNG_TTS_ENDPOINT)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            json={"text": text, "model": SLNG_TTS_VOICE},
            headers={
                "Authorization": f"Bearer {SLNG_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        return response.content


@router.get("/daily-briefing")
async def daily_briefing(db: Session = Depends(get_session)):
    if not SLNG_API_KEY:
        raise HTTPException(501, "Voice feature not configured")

    today = date.today()
    sessions = db.exec(
        select(RoutineSession)
        .where(RoutineSession.scheduled_date == today)
        .order_by(RoutineSession.scheduled_time)
    ).all()

    profile = db.get(UserProfile, 1)
    score = profile.resilience_score if profile else 0

    text = build_briefing_text(sessions, score)

    try:
        audio_bytes = await _call_slng_tts(text)
    except (httpx.HTTPStatusError, httpx.RequestError):
        raise HTTPException(502, "Voice service temporarily unavailable")

    return Response(content=audio_bytes, media_type="audio/mpeg")
