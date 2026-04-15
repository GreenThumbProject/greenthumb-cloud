"""GreenThumb Cloud API — FastAPI application entry point.

Route groups:
    /admin/...  — Full CRUD for all Tier 1/2 entities. Protected by user JWT.
    /sync/...   — Pi ↔ Cloud sync endpoints. Protected by device bearer token.

Environment variables:
    DATABASE_URL     — PostgreSQL connection string (required).
    AUTH_SERVICE_URL — Internal URL of the Java auth-service (default: http://auth-service:8081).
    DEV_AUTH_BYPASS  — Set to "true" to skip JWT validation in local dev.
"""
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import create_db_and_tables
from routes.admin.router import router as admin_router
from routes.sync.sync_routes import router as sync_router


@asynccontextmanager
async def lifespan(app: Any):
    """Run DDL on startup; nothing special on shutdown."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="GreenThumb Cloud API",
    description=(
        "Centralized cloud backend for GreenThumb greenhouse fleet management. "
        "Admin routes provide full CRUD for configuration entities. "
        "Sync routes handle Pi ↔ Cloud data exchange."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict in production to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(sync_router)


@app.get("/", tags=["Health"])
def health():
    """Basic liveness check."""
    return {"status": "ok", "service": "greenthumb-api"}
