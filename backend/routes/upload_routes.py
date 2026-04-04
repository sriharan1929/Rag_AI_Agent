import os
import zipfile
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from config import UPLOAD_DIR, VECTOR_DB
from utils.constants import SUPPORTED_EXTENSIONS
from services.indexing_service import stream_create_vector_db
from utils.tree_builder import build_tree

router = APIRouter()

@router.post("/upload")
@router.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(VECTOR_DB,  exist_ok=True)

    newly_uploaded: list[str] = []

    for file in files:
        dest = os.path.join(UPLOAD_DIR, file.filename)

        if os.path.exists(dest):
            print(f"[Upload] Overwriting existing file: {file.filename}", flush=True)
            # Optional: os.remove(dest) if you want to be super clean, 
            # but opening in "wb" mode will overwrite it anyway.

        content = await file.read()

        if file.filename.lower().endswith(".zip"):
            # Write, extract, delete the ZIP itself
            with open(dest, "wb") as f:
                f.write(content)
            with zipfile.ZipFile(dest, "r") as zf:
                zf.extractall(UPLOAD_DIR)
            os.remove(dest)
        else:
            with open(dest, "wb") as f:
                f.write(content)
            newly_uploaded.append(file.filename.replace("\\\\", "/"))

    # Full file tree after extraction
    all_paths = [
        os.path.relpath(os.path.join(r, n), UPLOAD_DIR).replace("\\\\", "/")
        for r, _, ns in os.walk(UPLOAD_DIR)
        for n in ns
    ]

    # If only a ZIP was uploaded, index everything that came out of it
    if not newly_uploaded:
        newly_uploaded = all_paths

    newly_abs = [
        os.path.join(UPLOAD_DIR, p)
        for p in newly_uploaded
        if os.path.isfile(os.path.join(UPLOAD_DIR, p))
    ]

    async def _stream():
        async for chunk in stream_create_vector_db(newly_abs):
            yield chunk
        yield json.dumps({
            "event":          "metadata",
            "structure":      build_tree(all_paths),
            "newly_uploaded": newly_uploaded,
        }) + "\\n"

    return StreamingResponse(_stream(), media_type="application/x-ndjson")
