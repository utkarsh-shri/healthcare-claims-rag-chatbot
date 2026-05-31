from fastembed import TextEmbedding
from supabase import create_client
import os

model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")  # highly memory efficient
supabase = create_client(os.environ['SUPABASE_URL'],
                         os.environ['SUPABASE_SERVICE_ROLE_KEY'])

def retrieve(query: str, top_k: int = 5) -> list[dict]:
    # Mask PII before embedding
    from guardrails.pii_mask import mask_pii
    safe_query = mask_pii(query)

    embedding = list(model.embed([safe_query.masked_text]))[0].tolist()

    threshold = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.30"))

    result = supabase.rpc('match_rag_documents', {
        'query_embedding': embedding,
        'match_threshold': threshold,
        'match_count': top_k
    }).execute()

    # Robustly map results to ensure 'source' is always present at the top level
    docs = []
    for doc in result.data or []:
        source = doc.get('source')
        if not source and 'metadata' in doc and isinstance(doc['metadata'], dict):
            source = doc['metadata'].get('source')
        docs.append({
            'id': doc.get('id'),
            'content': doc.get('content', ''),
            'source': source or 'Unknown',
            'similarity': doc.get('similarity', 0.0)
        })
    return docs
