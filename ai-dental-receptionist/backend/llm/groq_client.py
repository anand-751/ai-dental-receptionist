from rag.retriever import retrieve_chunks
from llm.model_loader import groq_chat
from llm.prompt_templates import rag_answer_prompt

RAG_CACHE = {}

def handle_rag_query(query: str) -> str:
    key = query.lower().strip()

    if key in RAG_CACHE:
        return RAG_CACHE[key]

    chunks = retrieve_chunks(query)

    if not chunks:
        fallback = (
            "I’m sorry, I don’t have that information right now. "
            "Would you like me to help you book an appointment?"
        )
        RAG_CACHE[key] = fallback
        return fallback

    # FAST PATH (no LLM)
    if len(chunks) == 1 and len(chunks[0]) < 400:
        RAG_CACHE[key] = chunks[0]
        return chunks[0]

    prompt = rag_answer_prompt(chunks, query)

    messages = [
        {"role": "system", "content": "Answer clearly and concisely using only the provided info."},
        {"role": "user", "content": prompt},
    ]

    answer = groq_chat(messages)
    RAG_CACHE[key] = answer
    return answer
