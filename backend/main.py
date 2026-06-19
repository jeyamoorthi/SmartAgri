"""
SmartAgri — Unified FastAPI Backend
====================================
Single FastAPI service combining:
- Core agricultural APIs (advisory, pest, market, recommendations)
- MongoDB integration
- User authentication
- Voice processing and AI advisory
- Email reminders via APScheduler

Stack:
- FastAPI + Uvicorn
- Motor (async MongoDB)
- Python-Jose (JWT auth)
- Groq API (AI advisory)
- Bhashini (multilingual voice)
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# ── Import DB and routers ─────────────────────────────────────────────────
from db.mongodb import connect_db, close_db
from routers import auth, advisory, pest, recommendations, market, voice_consultant, subsidies, natural_farming

# Startup and shutdown events.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # ── Startup ──
    await connect_db()
    print("[SmartAgri] backend started")
    print("[SmartAgri] Voice service available at /api/voice-consultant")
    yield
    # ── Shutdown ──
    await close_db()
    print("[SmartAgri] backend stopped")


app = FastAPI(
    title="SmartAgri API",
    description="AI-Powered Precision Farming Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://smart-agri-alpha-cyan.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include all routers ───────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(advisory.router)
app.include_router(pest.router)
app.include_router(recommendations.router)
app.include_router(market.router)
app.include_router(voice_consultant.router)
app.include_router(subsidies.router)
app.include_router(natural_farming.router)


@app.get("/")
async def root():
    return {"message": "🌾 SmartAgri API is running", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "smartagri-backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

