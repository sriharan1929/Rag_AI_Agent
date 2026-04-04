"""
config.py — Central configuration for ZIP-RAG backend.
Reads from backend/.env with sensible defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
VECTOR_DB  = os.getenv("VECTOR_DB", "vectorstore")