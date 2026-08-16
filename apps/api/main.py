"""
MISTY FastAPI Application.

Main application entry point with lifespan handler that initializes
the Brain instance and SQLite database. Provides REST and WebSocket
endpoints for the cognitive system.

Run with:
    uvicorn apps.api.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from brain.core.brain import Brain
from apps.api.database import Database
from apps.api.routes.chat import router as chat_router
from apps.api.routes.brain import router as brain_router
from apps.api.websocket.brain_stream import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Initializes Brain instance and database on startup,
    and cleans up resources on shutdown.
    """
    # Startup: Initialize brain and database
    brain = Brain()
    database = Database()
    await database.initialize()

    # Store in app state for access in route handlers
    app.state.brain = brain
    app.state.database = database

    yield

    # Shutdown: Close database connection
    await database.close()


# Create FastAPI application
app = FastAPI(
    title="MISTY Brain API",
    description=(
        "REST and WebSocket API for the MISTY Artificial Cognitive System. "
        "No LLM dependency - pure spiking neural network, knowledge graph, "
        "and cognitive cycle processing."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(brain_router, prefix="/api/brain")
app.include_router(ws_router)


@app.get("/")
async def root() -> dict:
    """Root endpoint - health check and API info."""
    return {
        "name": "MISTY Brain API",
        "version": "0.1.0",
        "status": "running",
        "description": "Artificial Cognitive System - No LLM dependency",
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
