import os
import shutil
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from config import UPLOAD_DIR, VECTOR_DB
from utils.tree_builder import build_tree
from services.vector_service import reset_vector_db
from services.indexing_service import stream_create_vector_db

router = APIRouter()

@router.get("/list_files")
@router.get("/list_files/")
async def list_files():
    if not os.path.exists(UPLOAD_DIR):
        return {"structure": {}, "summaries": {}}

    paths = [
        os.path.relpath(os.path.join(r, n), UPLOAD_DIR).replace("\\\\", "/")
        for r, _, ns in os.walk(UPLOAD_DIR)
        for n in ns
    ]
    return {"structure": build_tree(paths), "summaries": {}}

@router.delete("/delete/")
async def delete_file(path: str):
    abs_path = os.path.join(UPLOAD_DIR, path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File or folder not found.")

    async def _stream():
        try:
            if os.path.isdir(abs_path):
                shutil.rmtree(abs_path)
            else:
                os.remove(abs_path)
            yield json.dumps({"event": "log", "message": f"[Delete] Removed: {path}"}) + "\\n"

            # Rebuild the full index from remaining files
            if os.path.exists(VECTOR_DB):
                shutil.rmtree(VECTOR_DB)
            reset_vector_db()

            yield json.dumps({"event": "log", "message": "[Indexing] Rebuilding vector index..."}) + "\\n"
            async for chunk in stream_create_vector_db():
                yield chunk

        except Exception as e:
            yield json.dumps({"event": "error", "detail": f"Delete failed: {e}"}) + "\\n"

    return StreamingResponse(_stream(), media_type="application/x-ndjson")
