from .vector_store import search


def retrieve_chunks(query: str, top_k: int = 5):
    return search(query, top_k)
