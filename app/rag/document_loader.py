import json
import os
from pathlib import Path
from typing import List, Dict, Any
from app.models.schemas import DocumentChunk, DocumentChunkMetadata

class SchemeDocumentLoader:
    """Loads official government scheme documents from data/schemes/."""

    def __init__(self, schemes_dir: str):
        self.schemes_dir = Path(schemes_dir)

    def load_documents(self) -> List[Dict[str, Any]]:
        if not self.schemes_dir.exists():
            raise FileNotFoundError(f"Schemes directory not found: {self.schemes_dir}")

        raw_schemes: List[Dict[str, Any]] = []
        for file_path in self.schemes_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["_file_name"] = file_path.name
                    raw_schemes.append(data)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        return raw_schemes
