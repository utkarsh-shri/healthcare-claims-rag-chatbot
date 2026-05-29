"""
knowledge_base/loader.py

Document loader and text splitter for the healthcare knowledge base.
Loads .txt files from the documents/ directory and splits them into
500-token chunks with 50-token overlap for ChromaDB ingestion.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

DOCUMENTS_DIR = Path(__file__).parent / "documents"
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
SUPPORTED_EXTENSIONS = {".txt", ".md"}

# Use cl100k_base tokenizer (same as text-embedding-3-small and GPT-4)
TOKENIZER_NAME = "cl100k_base"


# ──────────────────────────────────────────────────────────────────────────────
# Token-Aware Length Function
# ──────────────────────────────────────────────────────────────────────────────

def _get_token_length_function():
    """
    Return a length function that counts tokens using tiktoken.
    This ensures chunk sizes are measured in tokens, not characters.
    """
    encoding = tiktoken.get_encoding(TOKENIZER_NAME)

    def token_length(text: str) -> int:
        return len(encoding.encode(text))

    return token_length


# ──────────────────────────────────────────────────────────────────────────────
# Core Loading Functions
# ──────────────────────────────────────────────────────────────────────────────

def load_document(file_path: Path) -> Optional[Document]:
    """
    Load a single .txt document and wrap it in a LangChain Document.

    Metadata includes:
    - source: filename (used in SourceDocument citations)
    - file_path: absolute path for debugging
    - file_size_bytes: raw file size

    Args:
        file_path: Path object pointing to the source file.

    Returns:
        LangChain Document, or None if the file cannot be read.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            logger.warning("Skipping empty file: %s", file_path.name)
            return None

        doc = Document(
            page_content=content,
            metadata={
                "source": file_path.name,
                "file_path": str(file_path.resolve()),
                "file_size_bytes": file_path.stat().st_size,
            }
        )
        logger.debug("Loaded document: %s (%d chars)", file_path.name, len(content))
        return doc

    except (OSError, IOError) as e:
        logger.error("Failed to load document %s: %s", file_path, e)
        return None


def load_all_documents(documents_dir: Path = DOCUMENTS_DIR) -> list[Document]:
    """
    Load all supported documents from the knowledge base directory.

    Args:
        documents_dir: Path to the directory containing knowledge base files.

    Returns:
        List of LangChain Document objects (unsplit).
    """
    if not documents_dir.exists():
        logger.error("Documents directory not found: %s", documents_dir)
        return []

    documents = []
    found_files = sorted(
        f for f in documents_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not found_files:
        logger.warning("No supported files found in: %s", documents_dir)
        return []

    for file_path in found_files:
        doc = load_document(file_path)
        if doc is not None:
            documents.append(doc)

    logger.info(
        "Loaded %d documents from '%s': %s",
        len(documents),
        documents_dir,
        [d.metadata["source"] for d in documents]
    )
    return documents


def split_documents(
    documents: list[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """
    Split documents into token-sized chunks for embedding.

    Uses RecursiveCharacterTextSplitter with a tiktoken-based length function
    to ensure chunks are measured in tokens (matching embedding model limits).

    Split hierarchy (tries each separator in order):
    1. Paragraph breaks (double newline)
    2. Single newline
    3. Sentence-ending periods
    4. Spaces
    5. Individual characters (last resort)

    Args:
        documents:     List of full-text Documents to split.
        chunk_size:    Target chunk size in tokens (default: 500).
        chunk_overlap: Overlap between adjacent chunks in tokens (default: 50).

    Returns:
        List of chunked Document objects with inherited metadata.
    """
    token_length_fn = _get_token_length_function()

    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=token_length_fn,
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)

    # Add chunk index metadata for traceability
    source_chunk_counts: dict[str, int] = {}
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        idx = source_chunk_counts.get(source, 0)
        chunk.metadata["chunk_index"] = idx
        source_chunk_counts[source] = idx + 1

    logger.info(
        "Split %d documents into %d chunks (size=%d tokens, overlap=%d tokens)",
        len(documents), len(chunks), chunk_size, chunk_overlap
    )
    for source, count in source_chunk_counts.items():
        logger.debug("  %s → %d chunks", source, count)

    return chunks


def load_and_split(
    documents_dir: Path = DOCUMENTS_DIR,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """
    Convenience function: load all documents and split them into chunks.

    This is the primary entry point called during application startup ingestion.

    Args:
        documents_dir: Directory containing knowledge base .txt files.
        chunk_size:    Token chunk size (default from env: 500).
        chunk_overlap: Token overlap between chunks (default from env: 50).

    Returns:
        List of chunked Document objects ready for embedding and indexing.
    """
    documents = load_all_documents(documents_dir)
    if not documents:
        logger.error("No documents loaded — knowledge base ingestion will be empty.")
        return []

    chunks = split_documents(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunks
