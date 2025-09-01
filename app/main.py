from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.endpoints import health, ingest
from app.core.config import settings
from app.core.database import db

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Ingest Service...")
    await db.connect()
    yield
    # Shutdown
    logger.info("Shutting down Ingest Service...")
    await db.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])

@app.get("/")
async def root():
    return {"message": "Ingest Service API", "version": settings.VERSION}