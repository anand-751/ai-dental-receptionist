"""
Document chunking module.
Splits documents into manageable chunks for embedding.
"""
from typing import List


class Chunker:
    """Handles document chunking"""

    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Split raw text into overlapping chunks.
        """
        if not text:
            return []

        text = text.replace("\n", " ").strip()

        chunks = []
        start = 0
        length = len(text)

        while start < length:
            end = start + self.chunk_size
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            start = end - self.overlap

        return chunks

    def chunk_document(self, document_path: str) -> List[str]:
        """
        Chunk a plain text document (MVP).
        """
        with open(document_path, "r", encoding="utf-8") as f:
            text = f.read()

        return self.chunk_text(text)
