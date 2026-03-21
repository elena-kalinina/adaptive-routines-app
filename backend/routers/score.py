from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from models import UserProfile

router = APIRouter(prefix="/api/score", tags=["score"])


@router.get("")
def get_score(db: Session = Depends(get_session)):
    profile = db.get(UserProfile, 1)
    score = profile.resilience_score if profile else 0
    return {"resilience_score": score}
