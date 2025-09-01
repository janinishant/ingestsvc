from fastapi import APIRouter
from typing import Dict, Any

from app.core.database import db

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "ingest-service"}


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check including database connectivity."""
    db_health = await db.health_check()
    
    if db_health["status"] == "healthy":
        return {
            "status": "ready",
            "database": db_health
        }
    else:
        return {
            "status": "not_ready",
            "database": db_health
        }