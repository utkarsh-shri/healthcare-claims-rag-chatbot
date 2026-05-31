"""
api/chat.py

FastAPI router for the Healthcare Claims RAG Chatbot.
Exposes:
  POST /api/chat   — main RAG query endpoint
  GET  /api/health — system health + ChromaDB document count
  POST /api/ingest — admin: trigger knowledge base re-ingestion
"""

import time
import logging
from fastapi import APIRouter, HTTPException, status, Request
import os

from models.schemas import ChatRequest, ChatResponse, HealthResponse
from rag.chain import answer
from api.limiter import limiter
from guardrails.pii_mask import mask_pii
from supabase import create_client

logger = logging.getLogger(__name__)
router = APIRouter()

# Reuse a single Supabase client rather than creating a new one per request
_supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Submit a healthcare claims question"
)
@limiter.limit("10/minute")
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    start_time = time.monotonic()
    session_id = body.session_id or "unknown"

    logger.info("Chat request received | session=%s", session_id)

    # ── Step 1: PII Masking
    mask_result = mask_pii(body.message)
    sanitized_query = mask_result.masked_text

    # ── Step 2: RAG Chain
    try:
        rag_result = answer(sanitized_query, session_id)
    except Exception as e:
        logger.error("RAG chain failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="The RAG pipeline encountered an error.") from e

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    return ChatResponse(
        answer=rag_result["answer"],
        sources=rag_result["sources"],
        session_id=session_id,
        response_time_ms=elapsed_ms,
        pii_detected=mask_result.pii_detected,
    )

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    try:
        # Check Supabase connection and document count
        res = _supabase.table('rag_documents').select('id', count='exact').limit(1).execute()
        doc_count = res.count
        kb_loaded = doc_count > 0
    except Exception as e:
        logger.error("Health check failed: %s", e)
        doc_count = 0
        kb_loaded = False

    return HealthResponse(
        status="healthy" if kb_loaded else "degraded",
        version="1.0.0",
        document_count=doc_count,
        knowledge_base_loaded=kb_loaded,
    )
