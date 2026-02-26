from rag.rag_pipeline import handle_rag_query

if __name__ == "__main__":
    query = "what is the price of white whitening service?"
    answer = handle_rag_query(query)
    print("\n--- RAG ANSWER ---")
    print(answer)
