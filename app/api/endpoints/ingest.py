from fastapi import APIRouter, HTTPException, Body, Request
from typing import Dict, Any, List
from datetime import datetime
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ingest")
async def ingest_logs(
    request: Request,
    logs: List[Dict[str, Any]] = Body(...)
) -> Dict[str, Any]:
    """
    Endpoint to ingest logs from fluent-bit
    """
    logger.info(f"Received request to /ingest from {request.client.host}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Raw payload: {json.dumps(logs, indent=2)}")
    logger.info(f"Number of log entries: {len(logs)}")

    for i, log_entry in enumerate(logs[:5]):
        logger.debug(f"Log entry {i}: {json.dumps(log_entry, indent=2)}")

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