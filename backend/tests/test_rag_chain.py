import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

from guardrails.pii_mask import mask_pii
from rag.chain import query_rag

def test_pii_masking():
    """Test that sensitive identifiers like Member ID and SSN are masked before querying the LLM."""
    text = "My member ID is MBR-1234567 and my SSN is 123-45-6789. Explain reject code 75."
    result = mask_pii(text)
    
    assert result.pii_detected is True
    assert "MBR-1234567" not in result.masked_text
    assert "123-45-6789" not in result.masked_text
    assert "[MEMBER_ID_REDACTED]" in result.masked_text
    assert "[SSN_REDACTED]" in result.masked_text
    assert "reject code 75" in result.masked_text

@patch("rag.chain.get_vector_store")
@patch("rag.chain.get_rag_chain")
def test_query_rag_mocked(mock_get_rag_chain, mock_get_vector_store):
    """Test the RAG pipeline end-to-end using a mocked ChromaDB and LLM Chain."""
    # Mock ChromaDB similarity search
    mock_vector_store = MagicMock()
    doc1 = Document(page_content="Prior auth requires step therapy.", metadata={"source": "policy.txt"})
    mock_vector_store.similarity_search_with_relevance_scores.return_value = [
        (doc1, 0.85)
    ]
    mock_get_vector_store.return_value = mock_vector_store
    
    # Mock LangChain QA Chain invocation
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "result": "You need step therapy for prior auth.",
        "source_documents": [doc1]
    }
    mock_get_rag_chain.return_value = mock_chain
    
    # Execute query
    result = query_rag("What is required for prior auth?")
    
    assert result.answer == "You need step therapy for prior auth."
    assert len(result.source_documents) == 1
    assert result.source_documents[0].page_content == "Prior auth requires step therapy."
    assert result.source_scores[0] == 0.85
