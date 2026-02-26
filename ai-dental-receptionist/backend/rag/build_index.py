import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from rag.chunker import Chunker

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # project root

SOURCE_DOC = BASE_DIR / "backend" / "data" / "raw" / "clinic_info.txt"
INDEX_PATH = BASE_DIR / "backend" / "rag" / "clinic.index"
META_PATH = BASE_DIR / "backend" / "rag" / "clinic_meta.json"


# ------------------------
model = SentenceTransformer(
    "all-MiniLM-L6-v2",
    device="cpu"
)
chunker = Chunker(chunk_size=250, overlap=35)

with SOURCE_DOC.open("r", encoding="utf-8") as f:
    text = f.read()

chunks = chunker.chunk_text(text)
embeddings = model.encode(chunks, convert_to_numpy=True)

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

faiss.write_index(index, str(INDEX_PATH))

with open(META_PATH, "w") as f:
    json.dump(chunks, f)

print(f"✅ Built FAISS index with {len(chunks)} chunks")
