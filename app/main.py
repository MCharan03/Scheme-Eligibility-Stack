"""National Scheme Eligibility Navigator - Primary Application Entry Point.

Starts the FastAPI server serving both the REST API and the Citizen Web Portal.
"""

import sys
from pathlib import Path

# Ensure workspace root is on Python module search path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from app.api.server import app

def main():
    """Launch the FastAPI server via Uvicorn."""
    print("================================================================")
    print("  National Scheme Eligibility Navigator (FastAPI Server)")
    print("  Portal URL:       http://127.0.0.1:8000/")
    print("  API Docs:         http://127.0.0.1:8000/docs")
    print("  API Status:       http://127.0.0.1:8000/api/status")
    print("================================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
