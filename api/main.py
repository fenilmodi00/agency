"""FastAPI application with CORS, Clerk JWT auth, and route stubs.

Provides the API skeleton for the Instagram creator dashboard MVP.
Routes return 501 stubs (to be implemented in Task 4).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown context for the FastAPI app."""
    logger.info("API server starting up")
    yield
    logger.info("API server shutting down")


app = FastAPI(
    title="Vernacular Creator API",
    description="Instagram creator dashboard backend — MVP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: allow all origins for MVP (Expo Go sends from different origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# ── Route stubs (Task 4 implementations) ──────────────────────────────────────


@app.post("/login", status_code=501)
async def login():
    """Stub: Instagram OAuth / credentials login."""
    return {"status": "not_implemented"}


@app.get("/profile", status_code=501)
async def profile():
    """Stub: Get creator profile data."""
    return {"status": "not_implemented"}


@app.get("/media", status_code=501)
async def media():
    """Stub: Get creator media/posts."""
    return {"status": "not_implemented"}


@app.get("/insights", status_code=501)
async def insights():
    """Stub: Get creator account insights."""
    return {"status": "not_implemented"}


@app.post("/disconnect", status_code=501)
async def disconnect():
    """Stub: Disconnect Instagram session."""
    return {"status": "not_implemented"}
