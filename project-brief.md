# Project Brief: healthcare-claims-rag-chatbot
## Stack: Vercel + Render + Supabase pgvector + Groq

---

## One-Line Description
A RAG-powered chatbot that answers healthcare provider and operations team queries
about pharmacy claims adjudication, grounded in a knowledge base of CMS guidelines
and RxClaim adjudication logic. Fully hosted, free, live demo URL.

---

## Free Hybrid Stack

| Layer | Service | URL Pattern |
|-------|---------|-------------|
| Frontend (React) | Vercel | https://claims-rag-chatbot.vercel.app |
| Backend (FastAPI) | Render | https://claims-rag-api.onrender.com |
| Vector Store | Supabase pgvector | your-project.supabase.co |
| LLM | Groq (Llama 3.1 70B) | api.groq.com |
| Embeddings | sentence-transformers (on Render) | local model, no API cost |

---

## Folder Structure

```
healthcare-claims-rag-chatbot/
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── chat.py                     # POST /api/chat, GET /api/health
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── chain.py                    # RAG chain: retrieve → prompt → LLM
│   │   ├── retriever.py                # Supabase pgvector similarity search
│   │   └── prompts.py                  # System prompt templates
│   ├── knowledge_base/
│   │   ├── loader.py                   # Load + chunk .txt documents
│   │   ├── embedder.py                 # sentence-transformers embedder
│   │   ├── ingest.py                   # One-time script: embed + upload to Supabase
│   │   └── documents/
│   │       ├── ncpdp_reject_codes.txt
│   │       ├── cms_guidelines.txt
│   │       ├── rxclaim_adjudication_rules.txt
│   │       ├── prior_auth_requirements.txt
│   │       └── formulary_tiers.txt
│   ├── guardrails/
│   │   ├── pii_mask.py                 # Mask member IDs, SSNs before LLM
│   │   └── grounding.py                # Verify answer in retrieved context
│   ├── models/
│   │   └── schemas.py                  # Pydantic models
│   ├── requirements.txt
│   ├── .env.example
│   ├── render.yaml                     # Render deployment config
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── SourceCitations.jsx
│   │   │   └── InputBar.jsx
│   │   └── api/
│   │       └── chat.js                 # calls VITE_API_URL/api/chat
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
├── scripts/
│   └── ingest_knowledge_base.py        # Run once locally to populate Supabase
├── tests/
│   ├── test_rag_chain.py
│   └── test_api.py
├── .github/
│   └── workflows/
│       └── ci.yml
└── README.md
```

---

## Supabase Setup (Run Once)

```sql
-- In Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE rag_documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  source TEXT NOT NULL,               -- which document file
  chunk_index INTEGER,
  embedding VECTOR(384),              -- all-MiniLM-L6-v2 dimensions
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX ON rag_documents
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- RPC function for similarity search
CREATE OR REPLACE FUNCTION match_rag_documents(
  query_embedding VECTOR(384),
  match_threshold FLOAT DEFAULT 0.75,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id BIGINT,
  content TEXT,
  source TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    rag_documents.id,
    rag_documents.content,
    rag_documents.source,
    1 - (rag_documents.embedding <=> query_embedding) AS similarity
  FROM rag_documents
  WHERE 1 - (rag_documents.embedding <=> query_embedding) > match_threshold
  ORDER BY rag_documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

---

## Key Implementation Files

### backend/rag/retriever.py
```python
from sentence_transformers import SentenceTransformer
from supabase import create_client
import os

model = SentenceTransformer('all-MiniLM-L6-v2')  # loads once at startup
supabase = create_client(os.environ['SUPABASE_URL'],
                         os.environ['SUPABASE_SERVICE_ROLE_KEY'])

def retrieve(query: str, top_k: int = 5) -> list[dict]:
    # Mask PII before embedding
    from guardrails.pii_mask import mask_pii
    safe_query = mask_pii(query)

    embedding = model.encode(safe_query).tolist()

    result = supabase.rpc('match_rag_documents', {
        'query_embedding': embedding,
        'match_threshold': 0.70,
        'match_count': top_k
    }).execute()

    return result.data  # [{content, source, similarity}]
```

### backend/rag/chain.py
```python
from groq import Groq
from .retriever import retrieve
from .prompts import build_prompt
import os

client = Groq(api_key=os.environ['GROQ_API_KEY'])

def answer(query: str, session_id: str) -> dict:
    docs = retrieve(query)

    if not docs:
        return {
            "answer": "I don't have information about that in my knowledge base.",
            "sources": [],
            "session_id": session_id
        }

    context = "\n\n".join([
        f"[Source: {d['source']}]\n{d['content']}" for d in docs
    ])

    prompt = build_prompt(context=context, question=query)

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": prompt['system']},
            {"role": "user", "content": prompt['user']}
        ],
        temperature=0.1,    # low temp for factual healthcare answers
        max_tokens=800
    )

    answer_text = response.choices[0].message.content

    return {
        "answer": answer_text,
        "sources": [
            {"document": d['source'],
             "excerpt": d['content'][:200],
             "similarity": round(d['similarity'], 3)}
            for d in docs
        ],
        "session_id": session_id
    }
```

### backend/rag/prompts.py
```python
def build_prompt(context: str, question: str) -> dict:
    return {
        "system": """You are a healthcare claims adjudication assistant for a pharmacy
benefit management system. You help claims processors and providers understand claim
outcomes, rejection reasons, and PBM rules.

RULES:
1. Answer ONLY from the provided context. Never invent codes or rules.
2. Always cite the source document for every fact.
3. If context doesn't contain the answer, say exactly:
   "I don't have that in my knowledge base. Please consult your PBM administrator."
4. Never reveal or repeat member PII. Refer to members as 'the member' only.
5. Format rejection codes as: Code → Meaning → Resolution Steps.""",

        "user": f"""Context from knowledge base:
{context}

Question: {question}

Answer with source citations:"""
    }
```

### scripts/ingest_knowledge_base.py
```python
"""
Run this ONCE locally to populate Supabase with the knowledge base.
$ python scripts/ingest_knowledge_base.py
"""
from sentence_transformers import SentenceTransformer
from supabase import create_client
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

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
    text = doc_path.read_text()
    chunks = chunk_text(text)
    print(f"Ingesting {doc_path.name}: {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        embedding = model.encode(chunk).tolist()
        supabase.table('rag_documents').insert({
            'content': chunk,
            'source': doc_path.name,
            'chunk_index': i,
            'embedding': embedding
        }).execute()

print("Ingestion complete.")
```

---

## requirements.txt
```
fastapi==0.110.0
uvicorn==0.27.0
groq==0.4.0
sentence-transformers==2.6.0
supabase==2.3.0
python-dotenv==1.0.0
pydantic==2.6.0
pytest==7.4.0
httpx==0.26.0
```

---

## .env.example
```bash
GROQ_API_KEY=gsk_your_key_here
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
```

---

## render.yaml
```yaml
services:
  - type: web
    name: claims-rag-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
      - key: ENVIRONMENT
        value: production
      - key: FRONTEND_URL
        value: https://claims-rag-chatbot.vercel.app
```

---

## frontend/vercel.json
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite"
}
```

## frontend/.env.production
```
VITE_API_URL=https://claims-rag-api.onrender.com
```

---

## Session-by-Session Claude Code Prompts

### Session A — Backend (Render + Supabase + Groq)
```
Build the backend for healthcare-claims-rag-chatbot.
Stack: Python FastAPI on Render, Supabase pgvector for vector store,
Groq API (llama-3.1-70b-versatile) for LLM, sentence-transformers
all-MiniLM-L6-v2 for embeddings. Do NOT use OpenAI or ChromaDB.

Create this exact folder structure: [paste folder structure]

Implement:
- main.py: FastAPI app, CORS allowing FRONTEND_URL env var, /health endpoint
- rag/retriever.py: [paste retriever code above exactly]
- rag/chain.py: [paste chain code above exactly]
- rag/prompts.py: [paste prompts code above exactly]
- guardrails/pii_mask.py: regex masking for member IDs (MBR-XXXXXXX format),
  SSNs (XXX-XX-XXXX), dates of birth, phone numbers, emails
- api/chat.py: POST /api/chat (calls chain.answer), GET /api/health
  (returns status + document count from Supabase)
- models/schemas.py: ChatRequest, ChatResponse, SourceDocument Pydantic models
- knowledge_base/documents/: generate all 5 synthetic healthcare documents
  with realistic content (50+ NCPDP codes, CMS Part D rules, adjudication logic,
  PA criteria, formulary tiers)
- scripts/ingest_knowledge_base.py: [paste ingest script above exactly]
- requirements.txt: [paste requirements above]
- .env.example: [paste env example]
- render.yaml: [paste render config]
```

### Session B — Frontend (Vercel + React)
```
Here is my backend for healthcare-claims-rag-chatbot (FastAPI on Render):
[paste main.py and schemas.py]

Build the React Vite Tailwind frontend for Vercel deployment.
- The API URL comes from import.meta.env.VITE_API_URL (not hardcoded)
- ChatWindow.jsx: chat interface, calls POST $VITE_API_URL/api/chat,
  shows typing indicator (3 animated dots) while waiting for Render response
  (can take 2-3 seconds, normal)
- MessageBubble.jsx: user messages right-aligned blue, AI messages left-aligned white
- SourceCitations.jsx: collapsible "Sources" panel below each AI message showing
  document name and similarity score
- InputBar.jsx: text input + send button, Enter key sends, disabled while loading
- Add a banner: "⚡ Note: First response may take 30s if service is waking up"
- vercel.json: [paste vercel config]
- package.json with vite, react, tailwindcss, axios
Professional healthcare enterprise look — blue/white/gray, no playful elements.
```

### Session C — Tests + CI + README
```
Add to healthcare-claims-rag-chatbot:
1. tests/test_rag_chain.py: mock Groq client and Supabase, test chain.answer()
   returns correct structure, test empty retrieval case
2. tests/test_api.py: FastAPI TestClient, test /health returns 200,
   test /api/chat returns ChatResponse shape
3. .github/workflows/ci.yml: pytest on push to main
4. README.md with:
   - Live demo links (Vercel frontend + Render API)
   - Architecture diagram showing Vercel→Render→Supabase→Groq flow
   - Setup instructions for local dev AND deployment
   - Supabase SQL setup section [paste SQL from above]
   - UptimeRobot setup note (keep Render warm)
   - Sample queries section with 5 real examples
   - Responsible AI section: PII masking, source grounding, no-hallucination guardrails
   - Tech stack table
```

---

## Deployment Checklist (Do After Code is Done)

- [ ] Run `python scripts/ingest_knowledge_base.py` locally — populates Supabase once
- [ ] Push code to GitHub
- [ ] Render: New Web Service → connect repo → set env vars → deploy
- [ ] Vercel: Import repo → set VITE_API_URL to Render URL → deploy
- [ ] UptimeRobot: monitor Render /health every 5 minutes
- [ ] Test live demo end to end
- [ ] Add live URLs to GitHub repo description and README badges

---

## What to Say in Interview

> "The vector store is Supabase pgvector — PostgreSQL with a vector column. I moved
> from ChromaDB because ChromaDB is in-memory and dies when the server restarts.
> Supabase is persistent, has a generous free tier, and the pgvector similarity search
> with an IVFFlat index is fast enough for a 500-document knowledge base. The embeddings
> are generated locally on the Render server using sentence-transformers — no embedding
> API cost. The LLM is Groq's Llama 3.1 70B — comparable quality to GPT-4o for
> structured Q&A tasks, completely free tier."

---

## Resume Bullet
```
Built healthcare-claims-rag-chatbot: production RAG chatbot (LangChain-pattern,
Groq Llama 3.1, Supabase pgvector, sentence-transformers) for pharmacy claims
adjudication Q&A. PII masking + grounding guardrails. Deployed: React on Vercel,
FastAPI on Render. Live demo: [URL]
```
