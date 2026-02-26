from .retriever import retrieve_chunks
from ..llm.model_loader import groq_chat
from ..llm.prompt_templates import rag_answer_prompt

# Simple in-memory cache (per process)
RAG_CACHE = {}


def handle_rag_query(query: str) -> str:
    normalized_query = query.strip().lower()

    # 1️⃣ Cache hit (instant)
    if normalized_query in RAG_CACHE:
        return RAG_CACHE[normalized_query]

    # 2️⃣ Retrieve relevant chunks from Pinecone
    chunks = retrieve_chunks(query)

    if not chunks:
        fallback = (
            "I’m sorry, I don’t have that information right now. "
            "Would you like me to help you book an appointment?"
        )
        RAG_CACHE[normalized_query] = fallback
        return fallback

    # 3️⃣ FAST PATH — factual answers (NO LLM)
    if len(chunks) == 1 and len(chunks[0]) < 400:
        answer = chunks[0]
        RAG_CACHE[normalized_query] = answer
        return answer

    # 4️⃣ Groq generation (USING WORKING CLIENT)
    prompt = rag_answer_prompt(chunks, query)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional dental clinic receptionist. "
                "Answer clearly and concisely using ONLY the provided information. "
                "Do not guess or hallucinate."
            )
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    answer = groq_chat(messages)

    # 5️⃣ Cache & return
    RAG_CACHE[normalized_query] = answer
    return answer
