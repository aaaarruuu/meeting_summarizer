import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .routes.meetings import router as meetings_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Meeting Summarizer API",
    description="Transcribes meeting audio and generates action-oriented summaries.",
    version="1.0.0",
)

origins = ["*"] if settings.CORS_ORIGINS == "*" else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


# Serve the plain HTML/CSS/JS frontend at "/" so the whole app is a single
# `uvicorn backend.main:app` away from being usable - no separate frontend
# server or build step required.
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
