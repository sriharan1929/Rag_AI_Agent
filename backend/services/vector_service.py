import os
from config import VECTOR_DB, OLLAMA_URL
from multi_query_retriever import MultiQueryRetriever
from contextual_compression import ContextualCompressor

_embedding_model = None
_vector_db       = None
_mqr: MultiQueryRetriever | None = None
_compressor: ContextualCompressor | None = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("[Embeddings] Loading all-MiniLM-L6-v2...", flush=True)
        from langchain_community.embeddings import HuggingFaceEmbeddings
        _embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embedding_model

def get_vector_db():
    """Lazy-load FAISS from disk and initialise retrievers on first access."""
    global _vector_db, _mqr, _compressor

    if _vector_db is None and os.path.exists(VECTOR_DB) and os.listdir(VECTOR_DB):
        from langchain_community.vectorstores import FAISS
        try:
            print("[VectorDB] Loading FAISS from disk...", flush=True)
            _vector_db = FAISS.load_local(
                VECTOR_DB,
                get_embedding_model(),
                allow_dangerous_deserialization=True,
            )
        except Exception as e:
            print(f"[VectorDB] Load error: {e}", flush=True)
            return None

    if _vector_db is not None:
        if _mqr is None:
            _mqr = MultiQueryRetriever(
                faiss_db=_vector_db,
                ollama_url=OLLAMA_URL,
                model="mistral",
                n_variants=4,
                candidates=10,
                timeout=30,
            )
        if _compressor is None:
            _compressor = ContextualCompressor(
                ollama_url=OLLAMA_URL,
                model="mistral",
                max_concurrency=4,
                timeout=60,
            )

    return _vector_db

def reset_vector_db():
    global _vector_db, _mqr, _compressor
    _vector_db = None
    _mqr       = None
    _compressor = None

def _reinit_retrievers(db):
    """Re-create retrievers after the vector DB is rebuilt."""
    global _vector_db, _mqr, _compressor
    _vector_db = db
    _mqr = MultiQueryRetriever(
        faiss_db=_vector_db,
        ollama_url=OLLAMA_URL,
        model="mistral",
        n_variants=4,
        candidates=10,
        timeout=30,
    )
    _compressor = ContextualCompressor(
        ollama_url=OLLAMA_URL,
        model="mistral",
        max_concurrency=4,
        timeout=60,
    )

def get_mqr():
    get_vector_db() # Ensures initialization
    return _mqr

def get_compressor():
    get_vector_db() # Ensures initialization
    return _compressor
