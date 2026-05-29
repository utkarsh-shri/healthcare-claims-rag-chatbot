# Healthcare Claims RAG Chatbot

An enterprise-grade, Retrieval-Augmented Generation (RAG) chatbot designed specifically for Pharmacy Benefit Management (PBM) and healthcare claims adjudication.

This system assists claims processors, pharmacy technicians, and healthcare providers by providing immediate, grounded answers regarding NCPDP reject codes, CMS Part D guidelines, Prior Authorization criteria, and formulary tier structures.

## Architecture

The system follows a modern RAG architecture with built-in responsible AI guardrails, ensuring that responses are safe, factual, and devoid of hallucinated rules.

```ascii
                      +-------------------+
                      |   User / Client   |
                      +---------+---------+
                                |
                        (1) Question
                                |
                      +---------v---------+
                      |   FastAPI Backend |
                      +---------+---------+
                                |
                        (2) PII Masking
                     (Strips SSN, Member ID)
                                |
                      +---------v---------+
                      |  ChromaDB Vector  | <--- (Ingested Clinical/Claims Docs)
                      |  Store Retrieval  |
                      +---------+---------+
                                |
                     (3) Top K Context Docs
                                |
                      +---------v---------+
                      |  Gemini 2.0 Flash |
                      |    Generation     |
                      +---------+---------+
                                |
                     (4) Hallucination Check
                    (Verifies answer grounding)
                                |
                      +---------v---------+
                      |  Grounded Answer  |
                      |   with Citations  |
                      +-------------------+
```

## Tech Stack

| Component | Technology | Purpose |
| --- | --- | --- |
| **Frontend** | React + Vite | Fast, modern SPA framework |
| **Styling** | Tailwind CSS | Enterprise-grade UI design system |
| **Backend** | FastAPI | High-performance Python API framework |
| **LLM Orchestration** | LangChain | Coordinates prompts, memory, and retrieval |
| **Generative AI** | Google Gemini 2.0 Flash Lite | Fast, cost-effective inference |
| **Embeddings** | Gemini Embeddings (text-embedding-004) | High-quality semantic search vectors |
| **Vector Database** | ChromaDB | Local, persistent semantic document store |

## Healthcare PBM Use Cases

This RAG chatbot translates directly into time and cost savings in a live healthcare environment:

1. **Reject Code Resolution**: Rather than looking up generic NCPDP manual pages, a claims processor can ask: *"What does NCPDP reject code 75 mean and how do I resolve it?"* and get immediate steps tailored to the organization's specific adjudication logic.
2. **Prior Authorization Workflows**: Quickly verify if a drug requires step therapy or specific diagnostic codes before approval (e.g., *"What are the PA criteria for TNF inhibitors?"*).
3. **Formulary Management**: Clarify tier exceptions and transition fill policies during the critical Q1 plan year rollover.
4. **CMS Compliance**: Ask questions about CMS Part D rules to ensure claim overrides do not violate federal compliance guidelines.

## Responsible AI & Security

In healthcare, AI must be deterministic, secure, and privacy-conscious:
- **PII Masking**: A middleware layer intercepts incoming queries and masks patterns resembling SSNs, Member IDs, and Dates of Birth before the prompt ever reaches the external LLM.
- **Strict Grounding**: The LLM is instructed via system prompts to *only* answer using the retrieved context. If it doesn't know, it refuses to answer rather than hallucinating policies.
- **Post-Generation Verification**: The backend explicitly validates the LLM's generated answer against the retrieved context to detect ungrounded facts.
- **Rate Limiting & Auth**: Endpoints are protected against DoS attacks, and database-modifying endpoints require admin authentication.

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Google Gemini API Key

### 1. Environment Configuration
Create a `.env` file in the `backend/` directory:
```env
GOOGLE_API_KEY=your-api-key-here
ADMIN_SECRET_KEY=your-secure-password
GEMINI_LLM_MODEL=gemini-2.0-flash-lite
```

### 2. Docker Compose (Recommended)
The easiest way to run the full stack (Frontend on port 80, Backend on port 8000) is via Docker:
```bash
docker-compose up --build -d
```
The application will be available at `http://localhost`.

### 3. Local Development Setup
**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Sample Queries to Try
- *"What does NCPDP reject code 75 mean and how do I resolve it?"*
- *"What are the prior auth requirements for TNF Inhibitors?"*
- *"Explain the transition fill policy for CMS Part D members."*
- *"If a drug is on Tier 3, can the member request a tier exception to Tier 1?"*
