"""
knowledge_base/embedder.py

Embedding pipeline: takes document chunks from the loader and ingests them
into ChromaDB using OpenAI text-embedding-3-small.
"""

import logging
from typing import Optional

from langchain_core.documents import Document

from rag.retriever import get_vector_store, reset_collection, get_document_count
from knowledge_base.loader import load_and_split

logger = logging.getLogger(__name__)

# Batch size for ChromaDB ingestion (avoids large single-request payloads)
INGESTION_BATCH_SIZE = 100


def ingest_documents(
    documents: Optional[list[Document]] = None,
    reset: bool = True,
) -> int:
    """
    Embed document chunks and ingest them into ChromaDB.

    This function:
    1. Optionally resets the existing ChromaDB collection to avoid duplicates.
    2. Loads and splits documents if not provided.
    3. Batches the chunks and adds them to the Chroma vector store.
    4. Returns the total number of chunks indexed.

    Args:
        documents: Pre-loaded and split Document chunks. If None, loads from
                   the knowledge_base/documents/ directory automatically.
        reset:     Whether to clear the existing collection before ingesting.
                   Set False for incremental ingestion (not recommended for
                   initial load as it may create duplicates).

    Returns:
        Total number of document chunks successfully ingested.
    """
    logger.info("Starting knowledge base ingestion (reset=%s)...", reset)

    # Step 1: Reset collection if requested
    if reset:
        reset_collection()
        logger.info("ChromaDB collection reset. Starting fresh ingestion.")

    # Step 2: Load documents if not provided
    if documents is None:
        logger.info("Loading documents from knowledge_base/documents/...")
        documents = load_and_split()

    if not documents:
        logger.error("No document chunks to ingest. Knowledge base will be empty.")
        return 0

    logger.info("Ingesting %d chunks into ChromaDB...", len(documents))

    # Step 3: Batch ingestion
    vector_store = get_vector_store()
    total_ingested = 0

    for batch_start in range(0, len(documents), INGESTION_BATCH_SIZE):
        batch = documents[batch_start: batch_start + INGESTION_BATCH_SIZE]
        batch_num = (batch_start // INGESTION_BATCH_SIZE) + 1
        total_batches = (len(documents) + INGESTION_BATCH_SIZE - 1) // INGESTION_BATCH_SIZE

        try:
            vector_store.add_documents(batch)
            total_ingested += len(batch)
            logger.info(
                "Ingested batch %d/%d (%d chunks).",
                batch_num, total_batches, len(batch)
            )
        except Exception as e:
            logger.error(
                "Failed to ingest batch %d/%d: %s",
                batch_num, total_batches, e,
                exc_info=True
            )
            # Continue with remaining batches rather than failing completely
            continue

    # Step 4: Verify ingestion
    final_count = get_document_count()
    logger.info(
        "Knowledge base ingestion complete. Chunks ingested: %d. "
        "ChromaDB total count: %d.",
        total_ingested, final_count
    )

    return total_ingested


def run_ingestion_pipeline() -> dict:
    """
    Full ingestion pipeline entry point for use in FastAPI lifespan startup
    and the /api/ingest admin endpoint.

    Returns:
        Dict with ingestion summary: status, documents_ingested, message.
    """
    try:
        count = ingest_documents(reset=True)
        return {
            "status": "success",
            "documents_ingested": count,
            "message": f"Successfully ingested {count} document chunks into ChromaDB."
        }
    except Exception as e:
        logger.error("Ingestion pipeline failed: %s", e, exc_info=True)
        return {
            "status": "failed",
            "documents_ingested": 0,
            "message": f"Ingestion failed: {str(e)}"
        }
