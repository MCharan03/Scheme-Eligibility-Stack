#!/usr/bin/env python
"""
Ingestion script for official Indian government scheme documents.
Loads scheme files from data/schemes/, chunks them with rich metadata,
and populates the persistent ChromaDB collection.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config.settings import settings
from app.rag.document_loader import SchemeDocumentLoader
from app.rag.chunker import SchemeChunker
from app.rag.vector_store import VectorStoreManager

def run_ingestion():
    print("=" * 60)
    print("Government Scheme Eligibility Navigator - Document Ingestion")
    print("=" * 60)
    print(f"Loading schemes from: {settings.DATA_SCHEMES_DIRECTORY}")
    print(f"Persisting ChromaDB at: {settings.CHROMA_PERSIST_DIRECTORY}")

    loader = SchemeDocumentLoader(settings.DATA_SCHEMES_DIRECTORY)
    raw_schemes = loader.load_documents()
    print(f"Found {len(raw_schemes)} official scheme documents.")

    all_chunks = []
    for s in raw_schemes:
        chunks = SchemeChunker.chunk_scheme(s)
        all_chunks.extend(chunks)
        print(f" -> {s.get('scheme_name')}: generated {len(chunks)} section chunks.")

    print(f"\nTotal generated chunks across all schemes: {len(all_chunks)}")
    
    vs = VectorStoreManager()
    count_added = vs.add_chunks(all_chunks)
    print(f"Successfully upserted {count_added} chunks into collection '{vs.collection_name}'.")
    print(f"Total documents now in ChromaDB collection: {vs.count()}")
    print("=" * 60)
    print("Ingestion completed successfully.")

if __name__ == "__main__":
    run_ingestion()
