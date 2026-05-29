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

    result = supabase.rpc('match_rag_documents', {
        'query_embedding': embedding,
        'match_threshold': 0.70,
        'match_count': top_k
    }).execute()

    return result.data  # [{content, source, similarity}]
