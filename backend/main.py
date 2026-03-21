import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

# Load .env from the repo root (one level up from backend/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from database import engine, init_db
from models import UserProfile
from routers import plans, sessions, score, voice


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Ensure a default user profile exists
    with Session(engine) as db:
        if not db.get(UserProfile, 1):
            db.add(UserProfile(id=1, resilience_score=0))
            db.commit()
    yield


app = FastAPI(
    title="Adaptive Routines API",
    description="AI-powered routine generation and management",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plans.router)
app.include_router(sessions.router)
app.include_router(score.router)
app.include_router(voice.router)


@app.get("/")
def root():
    return {"status": "ok", "app": "Adaptive Routines API"}
