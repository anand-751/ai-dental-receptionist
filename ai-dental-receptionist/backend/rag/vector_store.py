import os
import faiss
import json
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from pathlib import Path

# 🔒 HARD DISABLE CUDA
os.environ["CUDA_VISIBLE_DEVICES"] = ""

BASE_DIR = Path(__file__).resolve().parents[2]

INDEX_PATH = BASE_DIR / "backend" / "rag" / "clinic.index"
META_PATH = BASE_DIR / "backend" / "rag" / "clinic_meta.json"

# 🔒 FORCE CPU
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2",
    device="cpu"
)

index = faiss.read_index(str(INDEX_PATH))

with open(META_PATH, "r") as f:
    METADATA = json.load(f)


def embed_text(text: str) -> np.ndarray:
    return embedding_model.encode([text], device="cpu")


def search(query: str, top_k: int = 5) -> List[str]:
    query_vec = embed_text(query)
    _, indices = index.search(query_vec, top_k)
    return [METADATA[i] for i in indices[0]]
