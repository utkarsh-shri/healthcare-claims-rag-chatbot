"""
main.py

FastAPI application entry point for the Healthcare Claims RAG Chatbot backend.
Handles:
  - Application lifecycle (startup knowledge base ingestion via lifespan)
  - CORS configuration for the React frontend
  - Router registration for /api/* endpoints
  - Root redirect and OpenAPI docs
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Load environment variables from .env before any module imports that need them
load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ──────────────────────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# CORS Origins
# ──────────────────────────────────────────────────────────────────────────────

_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
CORS_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]


# ──────────────────────────────────────────────────────────────────────────────
# Application Lifespan (startup / shutdown)
# ──────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    """
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Healthcare Claims RAG Chatbot — starting up")
    logger.info("=" * 60)

    # Validate required environment variables
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY is not set.")
    if not os.getenv("SUPABASE_URL"):
        logger.error("SUPABASE_URL is not set.")

    logger.info("Server is ready to accept requests.")
    yield  # Application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Healthcare Claims RAG Chatbot — shutting down.")


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Healthcare Claims RAG Chatbot API",
    description=(
        "A Retrieval-Augmented Generation chatbot for pharmacy benefit management. "
        "Answers questions about claim adjudication, NCPDP reject codes, CMS guidelines, "
        "prior authorization requirements, and formulary tiers. "
        "Powered by Gemini 1.5 Pro + ChromaDB."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("APP_ENV", "development") == "development" else None,
    redoc_url="/redoc" if os.getenv("APP_ENV", "development") == "development" else None,
    openapi_url="/openapi.json" if os.getenv("APP_ENV", "development") == "development" else None,
)

# ──────────────────────────────────────────────────────────────────────────────
# Rate Limiting Configuration
# ──────────────────────────────────────────────────────────────────────────────

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from api.limiter import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ──────────────────────────────────────────────────────────────────────────────
# CORS Middleware
# ──────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Session-ID"],
    expose_headers=["X-Response-Time-MS"],
)

logger.info("CORS configured for origins: %s", CORS_ORIGINS)

# ──────────────────────────────────────────────────────────────────────────────
# Router Registration
# ──────────────────────────────────────────────────────────────────────────────

from api.chat import router as chat_router

app.include_router(
    chat_router,
    prefix="/api",
    tags=["Healthcare Claims RAG"],
)

# ──────────────────────────────────────────────────────────────────────────────
# Root Endpoint
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root URL to the interactive API docs."""
    return RedirectResponse(url="/docs")


# ──────────────────────────────────────────────────────────────────────────────
# Entrypoint for direct execution
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=os.getenv("APP_ENV", "development") == "development",
        log_level=LOG_LEVEL.lower(),
    )
