"""
Run this ONCE locally to populate Supabase with the knowledge base.
$ python scripts/ingest_knowledge_base.py
"""
from sentence_transformers import SentenceTransformer
from supabase import create_client
from pathlib import Path
import os
from dotenv import load_dotenv

env_path = Path('backend/.env')
load_dotenv(dotenv_path=env_path)

model = SentenceTransformer('all-MiniLM-L6-v2')
supabase = create_client(os.environ['SUPABASE_URL'],
                         os.environ['SUPABASE_SERVICE_ROLE_KEY'])

DOCS_PATH = Path('backend/knowledge_base/documents')
CHUNK_SIZE = 500
OVERLAP = 50

def chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), CHUNK_SIZE - OVERLAP):
        chunk = ' '.join(words[i:i + CHUNK_SIZE])
        if chunk:
            chunks.append(chunk)
    return chunks

for doc_path in DOCS_PATH.glob('*.txt'):
    text = doc_path.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    print(f"Ingesting {doc_path.name}: {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        embedding = model.encode(chunk).tolist()
        supabase.table('rag_documents').insert({
            'content': chunk,
            'metadata': {
                'source': doc_path.name,
                'chunk_index': i
            },
            'embedding': embedding
        }).execute()

print("Ingestion complete.")
