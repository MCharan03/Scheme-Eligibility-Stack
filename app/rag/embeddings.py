from typing import List
import chromadb.utils.embedding_functions as ef

class EmbeddingManager:
    """Manages local embedding functions for ChromaDB."""

    def __init__(self):
        try:
            self._fn = ef.DefaultEmbeddingFunction()
        except Exception as e:
            print(f"Warning: Falling back to SentenceTransformer or basic function: {e}")
            self._fn = ef.DefaultEmbeddingFunction()

    def get_embedding_function(self):
        return self._fn

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._fn(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._fn([text])[0]
