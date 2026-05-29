"""
models/schemas.py

Pydantic request/response models for the Healthcare Claims RAG Chatbot API.
"""

from pydantic import BaseModel, Field
from typing import Optional
import uuid


class ChatRequest(BaseModel):
    """
    Incoming chat request from a user or claims processor.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question or query to answer from the healthcare knowledge base.",
        examples=["What does NCPDP reject code 75 mean and how do I resolve it?"]
    )
    session_id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Optional session identifier for conversation tracking."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Why was claim for drug NDC 12345 rejected with code 75?",
                "session_id": "user-abc-123"
            }
        }
    }


class SourceDocument(BaseModel):
    """
    A retrieved knowledge base document chunk with relevance metadata.
    """
    document: str = Field(
        ...,
        description="Source filename from the knowledge base."
    )
    excerpt: str = Field(
        ...,
        description="Relevant text excerpt from the source document."
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score between the query and this chunk (0.0–1.0)."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "document": "ncpdp_reject_codes.txt",
                "excerpt": "Code 75: Prior Authorization Required. The drug requires prior authorization from the plan...",
                "relevance_score": 0.92
            }
        }
    }


class ChatResponse(BaseModel):
    """
    Response from the RAG chain including the answer and source citations.
    """
    answer: str = Field(
        ...,
        description="LLM-generated answer grounded in retrieved knowledge base documents."
    )
    sources: list[SourceDocument] = Field(
        default_factory=list,
        description="List of source document chunks used to generate the answer."
    )
    session_id: str = Field(
        ...,
        description="Session identifier echoed back from the request."
    )
    response_time_ms: int = Field(
        ...,
        ge=0,
        description="Total end-to-end response time in milliseconds."
    )
    pii_detected: bool = Field(
        default=False,
        description="Whether PII was detected and masked in the input query."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "Reject code 75 means Prior Authorization Required. The member's plan requires PA for this medication...",
                "sources": [
                    {
                        "document": "ncpdp_reject_codes.txt",
                        "excerpt": "Code 75: Prior Authorization Required...",
                        "relevance_score": 0.92
                    }
                ],
                "session_id": "user-abc-123",
                "response_time_ms": 1240,
                "pii_detected": False
            }
        }
    }


class HealthResponse(BaseModel):
    """
    Health check response with system status information.
    """
    status: str = Field(..., description="Overall API health status: 'healthy' or 'degraded'.")
    version: str = Field(default="1.0.0", description="API version string.")
    document_count: int = Field(
        ...,
        description="Total number of document chunks currently indexed in ChromaDB."
    )
    knowledge_base_loaded: bool = Field(
        ...,
        description="Whether the knowledge base was successfully ingested at startup."
    )


class IngestResponse(BaseModel):
    """
    Response from the knowledge base re-ingestion endpoint.
    """
    status: str = Field(..., description="Ingestion status: 'success' or 'failed'.")
    documents_ingested: int = Field(
        ...,
        description="Number of document chunks ingested into ChromaDB."
    )
    message: str = Field(..., description="Human-readable summary of the ingestion result.")
