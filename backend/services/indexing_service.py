import os
import json
from config import UPLOAD_DIR, VECTOR_DB
from loaders.file_loader import _load_file
from utils.tree_builder import _quick_summary
from services.vector_service import get_embedding_model, _reinit_retrievers

async def stream_create_vector_db(file_paths: list[str] | None = None):
    """
    Index files into FAISS.  Yields NDJSON lines:
      {"event": "log",      "message": "..."}
      {"event": "done",     "summaries": {...}, "logs": [...]}
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS

    logs      = []
    summaries = {}

    def log(msg: str) -> str:
        print(msg, flush=True)
        logs.append(msg)
        return json.dumps({"event": "log", "message": msg}) + "\\n"

    # Resolve file list
    if file_paths:
        files_to_process = [p for p in file_paths if os.path.isfile(p)]
    else:
        files_to_process = [
            os.path.join(root, fname)
            for root, _, fnames in os.walk(UPLOAD_DIR)
            for fname in fnames
        ]

    yield log(f"[Indexing] Processing {len(files_to_process)} file(s)...")

    splitter  = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documents = []

    for path in files_to_process:
        rel   = os.path.relpath(path, UPLOAD_DIR).replace("\\\\", "/")
        fname = os.path.basename(path)
        docs  = _load_file(path)

        if docs:
            summaries[rel] = _quick_summary(docs)
            chunks = splitter.split_documents(docs)
            documents.extend(chunks)
            yield log(f"  [✓] {fname} — {len(docs)} doc(s), {len(chunks)} chunk(s)")
        else:
            yield log(f"  [!] {fname} — no content extracted (skipped)")

    if not documents:
        yield log("[Indexing] No indexable content found.")
        yield json.dumps({"event": "done", "summaries": summaries, "logs": logs}) + "\\n"
        return

    yield log(f"\\n[Indexing] Building vector store from {len(documents)} chunks...")

    try:
        embeddings = get_embedding_model()

        if os.path.exists(VECTOR_DB) and os.listdir(VECTOR_DB):
            yield log("[Indexing] Appending to existing vector store...")
            db = FAISS.load_local(
                VECTOR_DB, embeddings, allow_dangerous_deserialization=True
            )
            db.add_documents(documents)
        else:
            yield log("[Indexing] Creating new vector store...")
            db = FAISS.from_documents(documents, embeddings)

        db.save_local(VECTOR_DB)
        _reinit_retrievers(db)
        yield log(f"[Indexing] ✅ Vector store saved — {len(documents)} chunks indexed.")

    except Exception as e:
        yield log(f"[Indexing] ⚠️  Error during indexing: {e}")
        yield log("[Indexing] Retrying with fresh vector store...")
        try:
            db = FAISS.from_documents(documents, get_embedding_model())
            db.save_local(VECTOR_DB)
            _reinit_retrievers(db)
            yield log("[Indexing] ✅ Fresh vector store created successfully.")
        except Exception as e2:
            yield log(f"[Indexing] ❌ Fatal indexing error: {e2}")

    yield json.dumps({"event": "done", "summaries": summaries, "logs": logs}) + "\\n"
