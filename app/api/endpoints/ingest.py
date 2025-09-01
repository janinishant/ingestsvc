from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List
from datetime import datetime

router = APIRouter()


@router.post("/ingest")
async def ingest_logs(
    logs: List[Dict[str, Any]] = Body(...)
) -> Dict[str, Any]:
    """
    Endpoint to ingest logs from fluent-bit
    """
    # Placeholder logic
    return {
        "status": "success",
        "received": len(logs),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/ingest/batch")
async def ingest_logs_batch(
    payload: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Endpoint to ingest batch logs
    """
    # Placeholder logic
    return {
        "status": "success",
        "message": "Batch received",
        "timestamp": datetime.utcnow().isoformat()
    }