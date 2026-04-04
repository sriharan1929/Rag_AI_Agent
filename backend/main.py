"""
main.py  —  ZIP-RAG Backend (Modular)
================================================
Full-stack RAG backend integrating:
  • HybridRetriever      — BM25 + FAISS + RRF fusion
  • MultiQueryRetriever  — query expansion via Ollama + parallel FAISS search
  • ContextualCompressor — strips each chunk to only relevant sentences
  • prompts.py           — intent-aware, persona-tuned prompt router

Start with:
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.upload_routes import router as upload_router
from routes.rag_routes import router as rag_router
from routes.history_routes import router as history_router
from routes.file_routes import router as file_router
from config import OLLAMA_URL

app = FastAPI(title="ZIP-RAG API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(rag_router)
app.include_router(history_router)
app.include_router(file_router)

@app.get("/")
def root():
    ollama_ok = False
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        ollama_ok = r.status_code == 200
    except Exception:
        pass
    return {
        "status": "ok",
        "version": "2.0.0",
        "ollama_running": ollama_ok,
        "message": (
            "ZIP-RAG backend running — Ollama AI active ✅"
            if ollama_ok
            else "ZIP-RAG backend running — Ollama NOT detected ⚠️"
        ),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)