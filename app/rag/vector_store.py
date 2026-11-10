import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config.settings import settings
from app.rag.embeddings import EmbeddingManager
from app.models.schemas import DocumentChunk, DocumentChunkMetadata

class VectorStoreManager:
    """Manages ChromaDB persistent storage, indexing, and retrieval for official scheme data."""

    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        
        # Ensure target directory exists
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.embedding_manager = EmbeddingManager()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_manager.get_embedding_function(),
            metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        return self.collection.count()

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        if not chunks:
            return 0
        
        ids = [c.id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [c.metadata.model_dump() for c in chunks]

        # Chroma upsert replaces or adds without duplicate key errors
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def query(
        self, 
        query_text: str, 
        n_results: int = 5, 
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """Performs similarity search with optional metadata filter."""
        total_docs = self.collection.count()
        if total_docs == 0:
            return []

        actual_n = min(n_results, total_docs)
        kwargs: Dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": actual_n
        }
        if where:
            kwargs["where"] = where
        if where_document:
            kwargs["where_document"] = where_document

        results = self.collection.query(**kwargs)

        retrieved_chunks: List[DocumentChunk] = []
        if not results or not results.get("ids") or len(results["ids"][0]) == 0:
            return []

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results.get("distances", [[0.0] * len(ids)])[0]

        for cid, doc, meta, dist in zip(ids, documents, metadatas, distances):
            retrieved_chunks.append(
                DocumentChunk(
                    id=cid,
                    content=doc,
                    metadata=DocumentChunkMetadata(**meta),
                    score=float(dist)
                )
            )
        return retrieved_chunks

    def reset(self):
        """Resets the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_manager.get_embedding_function(),
            metadata={"hnsw:space": "cosine"}
        )
