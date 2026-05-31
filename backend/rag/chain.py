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
        model="llama-3.3-70b-versatile",
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
