import os
import json
import asyncio
import base64
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.request_models import ChatRequest
from services.ollama_service import get_best_vision_model, is_vision_available, ollama_chat, ollama_stream, get_available_models
from services.vector_service import get_vector_db, get_mqr, get_compressor
from services.rag_service import _resolve_direct_file, _read_file_for_direct_query, _filter_by_selected, _topic_from_path
from utils.constants import FILE_EXT_RE, CODE_EXTS
from config import UPLOAD_DIR
from prompts import build_prompt, build_general_prompt, build_vision_prompt
from contextual_compression import CompressedChunk

router = APIRouter()

@router.get("/models/list")
@router.get("/models/list/")
async def list_models():
    """Returns available Ollama models."""
    return {"models": get_available_models()}

@router.post("/ask")
@router.post("/ask/")
def ask_question(request: ChatRequest):
    """
    Synchronous RAG endpoint.
    mode = "advanced" → multi-query + contextual compression
    mode = "basic"    → direct FAISS similarity search, no compression
    """
    query = request.query
    files = request.selected_files
    mode = request.mode
    web_search = request.web_search
    images = request.images

    # Note: request.selected_files is a List[str], but historically sometimes passed as comma separated.
    # We will assume it's a List[str] because of the Pydantic model Optional[List[str]].
    selected_files = [f.strip().lower() for f in files] if files else []
    
    # Optional: If images provided, force the best available vision model
    active_model = get_best_vision_model() if images else "llama3"

    # 1. Vision Capability Check
    if images and not is_vision_available():
        return {
            "isRelevant": False,
            "topic": "Error",
            "results": [{"content": "⚠️ Vision model missing. Please run `ollama pull moondream` in your terminal to analyze images.", "score": 0.0, "source": "System"}]
        }

    # 2. Image Bypass (Skip auto-RAG if no files selected)
    if images and not selected_files:
        abs_path, _ = _resolve_direct_file(query)
        if not abs_path:
            print("[Ask] Processing Image natively (SKIPPING auto-RAG).", flush=True)
            vis_prompt = query.strip() if query.strip() else "Describe this image in detail."
            final_prompt = vis_prompt if active_model in ["moondream", "llava", "bakllava"] else build_general_prompt(vis_prompt)
            
            answer = ollama_chat(final_prompt, preferred_model=active_model, images=images)
            return {
                "isRelevant": False,
                "topic":  "Image Analysis",
                "source": "Ollama",
                "results": [{"content": answer, "score": 0.0, "source": "Ollama"}]
            }

    # ── Path 1: Direct file mention ──────────────────────────────────────────
    abs_path, rel_path = _resolve_direct_file(query)
    if abs_path:
        content = _read_file_for_direct_query(abs_path)
        prompt  = build_prompt(rel_path, content, query)
        if active_model in ["moondream", "llava", "bakllava"]:
            prompt = f"Context:\\n{content[:1000]}\\n\\nQuestion: {query}"
        
        answer  = ollama_chat(prompt, preferred_model=active_model, images=images)
        return {
            "isRelevant": True,
            "topic":   _topic_from_path(rel_path),
            "results": [{"content": answer, "score": 0.0, "source": rel_path}],
        }

    # ── Path 2: RAG retrieval ─────────────────────────────────────────────────
    db = get_vector_db()
    _mqr = get_mqr()
    _compressor = get_compressor()
    
    if db is None or _mqr is None or _compressor is None:
        raise HTTPException(
            status_code=500,
            detail="Vector DB not ready. Please upload and index files first.",
        )

    print(f"\\n[Ask] '{query}'", flush=True)

    # 1. Retrieve
    if mode == "advanced":
        res = _mqr.search_sync(query, k=15, include_web=web_search, include_images=web_search)
        raw_docs = res["docs"]
        web_images = res["images"]
        web_results = res.get("web_results", [])
    elif web_search:
        # Basic mode with Web Search enabled
        res = _mqr.search_sync(query, k=10, n_variants=0, include_web=True, include_images=True)
        raw_docs = res["docs"]
        web_images = res["images"]
        web_results = res.get("web_results", [])
    else:
        raw_docs = db.similarity_search_with_score(
            query, k=30 if selected_files else 10
        )
        web_images = []
        web_results = []

    # 2. Filter by selected files
    raw_docs = _filter_by_selected(raw_docs, selected_files)

    if not raw_docs:
        return {
            "isRelevant": False,
            "topic":       "No Match",
            "results":     [],
            "generalAnswer": (
                "No relevant content found in the selected files. "
                "Try broadening your query or selecting different files."
            ),
        }

    # 3. Compress (advanced) or pass through (basic)
    if mode == "advanced":
        compressed = _compressor.compress_sync(query, raw_docs)
    else:
        compressed = [
            CompressedChunk(
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                original_length=len(doc.page_content),
                compressed_length=len(doc.page_content),
                compression_ratio=1.0,
                retrieval_score=score,
                was_compressed=False,
            )
            for doc, score in raw_docs[:5]
        ]

    if not compressed:
        return {
            "isRelevant": False,
            "topic":       "No Relevant Content",
            "results":     [],
            "generalAnswer": (
                "The retrieved chunks contained no information relevant "
                "to your query. Please try rephrasing or uploading more files."
            ),
        }

    # 4. Build context → prompt → answer
    context   = _compressor.build_context_string(compressed, max_total_chars=8000)
    rel_src   = os.path.relpath(compressed[0].source, UPLOAD_DIR).replace("\\\\", "/")
    prompt    = build_prompt(rel_src, context, query)
    if active_model in ["moondream", "llava", "bakllava"]:
        prompt = f"Context:\\n{context[:1000]}\\n\\nQuestion: {query}"
        
    answer    = ollama_chat(prompt, preferred_model=active_model, images=images)

    return {
        "isRelevant": True,
        "topic":   _topic_from_path(rel_src),
        "results": [{
            "content": answer,
            "score":   compressed[0].retrieval_score,
            "source":  rel_src,
            "images":  web_images,
            "web_results": web_results,
            "compressionStats": {
                "chunksRetrieved":       len(raw_docs),
                "chunksAfterCompression": len(compressed),
                "contextCharsBefore":    sum(len(d.page_content) for d, _ in raw_docs),
                "contextCharsAfter":     sum(c.compressed_length for c in compressed),
            },
        }],
    }


@router.post("/ask_stream")
@router.post("/ask_stream/")
async def ask_stream(request: ChatRequest):
    """
    Streaming RAG endpoint (Server-Sent Events).
    Support for Comparative Mode via 'models' parameter (comma-separated).
    """
    query           = request.query
    selected_files  = request.selected_files or []
    mode            = request.mode or "basic"
    web_search      = request.web_search or False
    requested_models = request.models.split(",") if request.models else None
    images          = request.images or []

    # Initial model selection
    best_vision = get_best_vision_model()
    active_model = best_vision if (images and best_vision) else ("llama3" if not requested_models else requested_models[0])

    async def _generate():
        nonlocal active_model
        try:
            # 1. Vision Capability Check
            if images and not is_vision_available():
                yield f"data: {json.dumps({'event': 'error', 'message': '⚠️ Vision model missing. Please run `ollama pull moondream` in your terminal to analyze images.'})}\n\n"
                return

            # 2. Image Bypass (Skip auto-RAG if no files selected)
            if images and not selected_files:
                abs_path, _ = _resolve_direct_file(query)
                if not abs_path:
                    print("[Stream] Processing Image natively (SKIPPING auto-RAG).", flush=True)
                    vis_prompt = query.strip() if query.strip() else "Describe this image in detail."
                    
                    # Update: Include llama3.2-vision in focused vision models
                    is_focused_vision = any(vm in active_model.lower() for vm in ["llama3.2-vision", "moondream", "llava", "bakllava"])
                    final_prompt = build_vision_prompt(vis_prompt) if is_focused_vision else build_general_prompt(vis_prompt)
                    
                    yield f"data: {json.dumps({'event': 'meta', 'isRelevant': False, 'topic': 'Image Analysis', 'source': 'Ollama'})}\n\n"
                    async for token in ollama_stream(final_prompt, model=active_model, images=images):
                        yield f"data: {json.dumps({'event': 'token', 'text': token})}\n\n"
                    yield f"data: {json.dumps({'event': 'done'})}\n\n"
                    return

            # ── Path 1: Direct file mention ───────────────────────────────
            abs_path, rel_path = _resolve_direct_file(query)
            if abs_path:
                content = _read_file_for_direct_query(abs_path)
                
                # Update: Use optimized vision prompt for vision models
                is_focused_vision = any(vm in active_model.lower() for vm in ["llama3.2-vision", "moondream", "llava", "bakllava"])
                if images and is_focused_vision:
                    prompt = build_vision_prompt(query)
                else:
                    prompt  = build_prompt(rel_path, content, query)
                    if is_focused_vision: # Fallback if no images but model is vision
                        prompt = f"Context:\\n{content[:1000]}\\n\\nQuestion: {query}"
                
                yield f"data: {json.dumps({'event': 'meta', 'isRelevant': True, 'topic': _topic_from_path(rel_path), 'source': rel_path})}\n\n"
                async for token in ollama_stream(prompt, model=active_model, images=images):
                    yield f"data: {json.dumps({'event': 'token', 'text': token})}\n\n"
                yield f"data: {json.dumps({'event': 'done'})}\n\n"
                return

            # ── Path 2: RAG retrieval ─────────────────────────────────────
            db = get_vector_db()
            _mqr = get_mqr()
            _compressor = get_compressor()
            
            if db is None or _mqr is None or _compressor is None:
                yield f"data: {json.dumps({'event': 'error', 'message': 'RAG not ready. Please upload files first.'})}\n\n"
                return

            print(f"\\n[Stream] '{query}'", flush=True)

            # 1. Retrieve
            selected_norm = [f.replace("\\\\", "/").lower() for f in selected_files]

            if mode == "advanced":
                res = await _mqr.search(query, k=15, include_web=web_search, include_images=web_search)
                raw_docs = res["docs"]
                web_images = res["images"]
                web_results = res.get("web_results", [])
            elif web_search:
                # Basic mode with Web Search enabled
                res = await _mqr.search(query, k=10, n_variants=0, include_web=True, include_images=True)
                raw_docs = res["docs"]
                web_images = res["images"]
                web_results = res.get("web_results", [])
            else:
                raw_docs = db.similarity_search_with_score(
                    query, k=30 if selected_norm else 10
                )
                web_images = []
                web_results = []

            # Inject any directly-mentioned file at the top
            fm = FILE_EXT_RE.search(query)
            if fm:
                target = fm.group(1).strip().lower()
                found  = None
                for root, _, fnames in os.walk(UPLOAD_DIR):
                    for fname in fnames:
                        if fname.lower() == target:
                            found = os.path.join(root, fname)
                            rel   = os.path.relpath(found, UPLOAD_DIR).replace("\\\\", "/").lower()
                            if rel not in selected_norm:
                                selected_norm.append(rel)
                            break
                    if found:
                        break

                # Inject full content for small text/code files
                if found:
                    ext = os.path.splitext(found)[1].lower()
                    if ext in CODE_EXTS:
                        try:
                            with open(found, "r", encoding="utf-8", errors="ignore") as f:
                                raw_text = f.read()
                            if len(raw_text) < 20_000:
                                from langchain_core.documents import Document
                                raw_docs = [(Document(
                                    page_content=raw_text,
                                    metadata={"source": found},
                                ), 1.0)] + list(raw_docs)
                        except Exception:
                            pass

            # 2. Filter & Detect Images
            raw_docs = _filter_by_selected(raw_docs, selected_norm)

            # Update: If selected files include images, extract them for Ollama
            image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
            for sel_file in selected_norm:
                if any(sel_file.lower().endswith(ext) for ext in image_exts):
                    img_path = os.path.join(UPLOAD_DIR, sel_file)
                    if os.path.exists(img_path):
                        try:
                            with open(img_path, "rb") as f:
                                b64 = base64.b64encode(f.read()).decode("utf-8")
                                if b64 not in images:
                                    images.append(b64)
                                    print(f"[Stream] Added image from selection: {sel_file}", flush=True)
                        except Exception as e:
                            print(f"[Stream] Failed to read image {sel_file}: {e}", flush=True)

            # Re-evaluate active model if images were detected from selection
            if images and best_vision:
                active_model = best_vision
                print(f"[Stream] Switched to vision model: {active_model}", flush=True)

            if not raw_docs:
                # If files are selected but RAG found nothing, read them directly from disk
                if selected_norm:
                    direct_parts = []
                    primary_rel = None
                    for sel_file in selected_norm:
                        abs_p = os.path.join(UPLOAD_DIR, sel_file)
                        if os.path.isfile(abs_p):
                            content = _read_file_for_direct_query(abs_p)
                            if content and content not in ("Could not read file.", "Could not read spreadsheet."):
                                direct_parts.append(content)
                                if primary_rel is None:
                                    primary_rel = sel_file

                    if direct_parts:
                        context = "\\n\\n---\\n\\n".join(direct_parts)[:8000]
                        prompt  = build_prompt(primary_rel, context, query)
                        topic   = _topic_from_path(primary_rel)
                        print(f"[Stream] RAG miss — using direct file read for: {primary_rel}", flush=True)
                        yield f"data: {json.dumps({'event': 'meta', 'isRelevant': True, 'topic': topic, 'source': primary_rel})}\n\n"
                        async for token in ollama_stream(prompt, model=active_model, images=images):
                            yield f"data: {json.dumps({'event': 'token', 'text': token})}\n\n"
                        yield f"data: {json.dumps({'event': 'done'})}\n\n"
                        return

                print("[Stream] No relevant context — falling back to general.", flush=True)
                # Use specialized vision prompt if images are present
                if images:
                    prompt = build_vision_prompt(query)
                    topic = "Vision Analysis"
                    source = "Vision Model"
                else:
                    prompt = build_general_prompt(query)
                    topic = "General Knowledge"
                    source = "Ollama"

                yield f"data: {json.dumps({'event': 'meta', 'isRelevant': False, 'topic': topic, 'source': source})}\n\n"
                async for token in ollama_stream(prompt, model=active_model, images=images):
                    yield f"data: {json.dumps({'event': 'token', 'text': token})}\n\n"
                yield f"data: {json.dumps({'event': 'done'})}\n\n"
                return

            # 3. Compress
            if mode == "advanced":
                compressed = await _compressor.compress(query, raw_docs)
            else:
                compressed = [
                    CompressedChunk(
                        content=doc.page_content,
                        source=doc.metadata.get("source", "unknown"),
                        original_length=len(doc.page_content),
                        compressed_length=len(doc.page_content),
                        compression_ratio=1.0,
                        retrieval_score=score,
                        was_compressed=False,
                    )
                    for doc, score in raw_docs[:5]
                ]

            if not compressed:
                # If files are selected but compression wiped everything, read selected files directly
                if selected_norm:
                    direct_parts = []
                    primary_rel = None
                    for sel_file in selected_norm:
                        abs_p = os.path.join(UPLOAD_DIR, sel_file)
                        if os.path.isfile(abs_p):
                            content = _read_file_for_direct_query(abs_p)
                            if content and content not in ("Could not read file.", "Could not read spreadsheet."):
                                direct_parts.append(content)
                                if primary_rel is None:
                                    primary_rel = sel_file

                    if direct_parts:
                        context = "\\n\\n---\\n\\n".join(direct_parts)[:8000]
                        prompt  = build_prompt(primary_rel, context, query)
                        topic   = _topic_from_path(primary_rel)
                        print(f"[Stream] Compression empty — using direct file read for: {primary_rel}", flush=True)
                        yield f"data: {json.dumps({'event': 'meta', 'isRelevant': True, 'topic': topic, 'source': primary_rel})}\n\n"
                        async for token in ollama_stream(prompt, model=active_model, images=images):
                            yield f"data: {json.dumps({'event': 'token', 'text': token})}\n\n"
                        yield f"data: {json.dumps({'event': 'done'})}\n\n"
                        return

                # Use specialized vision prompt if images are present
                if images:
                    prompt = build_vision_prompt(query)
                    topic = "Vision Analysis"
                    source = "Vision Model"
                else:
                    prompt = build_general_prompt(query)
                    topic = "General Knowledge"
                    source = "Ollama"

                yield f"data: {json.dumps({'event': 'meta', 'isRelevant': False, 'topic': topic, 'source': source})}\n\n"
                async for token in ollama_stream(prompt, model=active_model, images=images):
                    yield f"data: {json.dumps({'event': 'token', 'text': token})}\n\n"
                yield f"data: {json.dumps({'event': 'done'})}\n\n"
                return

            # 4. Build prompt → stream answer
            context   = _compressor.build_context_string(compressed, max_total_chars=8000)
            rel_src   = os.path.relpath(compressed[0].source, UPLOAD_DIR).replace("\\\\", "/")
            topic     = _topic_from_path(rel_src)
            
            is_focused_vision = any(vm in active_model.lower() for vm in ["llama3.2-vision", "moondream", "llava", "bakllava"])
            if images and is_focused_vision:
                prompt = build_vision_prompt(query)
            else:
                prompt = build_prompt(rel_src, context, query)
                if is_focused_vision:
                    prompt = f"Context:\\n{context[:1000]}\\n\\nQuestion: {query}"

            yield f"data: {json.dumps({'event': 'meta', 'isRelevant': True, 'topic': topic, 'source': rel_src, 'images': web_images, 'web_results': web_results})}\n\n"
            
            if not requested_models:
                async for token in ollama_stream(prompt, model=active_model, images=images):
                    yield f"data: {json.dumps({'event': 'token', 'text': token})}\n\n"
            else:
                # Multiplexed streaming for comparison
                queue = asyncio.Queue()
                
                async def produce(model_name):
                    try:
                        async for token in ollama_stream(prompt, model=model_name, images=images):
                            await queue.put({"model": model_name, "token": token})
                        await queue.put({"model": model_name, "done": True})
                    except Exception as e:
                        await queue.put({"model": model_name, "error": str(e)})

                for m in requested_models:
                    asyncio.create_task(produce(m))

                done_count = 0
                while done_count < len(requested_models):
                    item = await queue.get()
                    if "error" in item:
                        yield f"data: {json.dumps({'event': 'error', 'model': item['model'], 'message': item['error']})}\n\n"
                        done_count += 1
                    elif "done" in item:
                        done_count += 1
                    else:
                        yield f"data: {json.dumps({'event': 'token', 'model': item['model'], 'text': item['token']})}\n\n"

            yield f"data: {json.dumps({'event': 'done'})}\n\n"

        except Exception as e:
            print(f"[Stream] Error: {e}", flush=True)
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
