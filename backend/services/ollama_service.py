import os
import time
import json
import requests
import subprocess
from config import OLLAMA_URL

def ensure_ollama_running() -> bool:
    """Ping Ollama; start it automatically if not running."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            return True
    except Exception:
        pass

    print("[Ollama] Not detected — attempting to start...", flush=True)
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
        time.sleep(4)
        return True
    except Exception as e:
        print(f"[Ollama] Could not start: {e}", flush=True)
        return False

def get_available_models() -> list[str]:
    """Lists installed models from Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return []

def get_best_vision_model() -> str:
    """Find the most capable vision model among installed Ollama models."""
    installed = get_available_models()
    
    # Check for full names first
    vision_bases = ["llama3.2-vision", "llava", "bakllava", "moondream"]
    
    # Match full name (e.g. llama3.2-vision:latest) or base name
    for vb in vision_bases:
        for full_name in installed:
            if full_name == vb or full_name.startswith(f"{vb}:"):
                return full_name
            
    return None

def is_vision_available() -> bool:
    """Checks if any common vision-capable model is installed."""
    installed = get_available_models()
    vision_models = ["llama3.2-vision", "llava", "bakllava", "moondream"]
    return any(vm in [m.split(":")[0] for m in installed] for vm in vision_models)

def ollama_chat(prompt: str, preferred_model: str = "llama3", images: list[str] = None) -> str:
    """Synchronous Ollama call with model fallback chain and optional images."""
    ensure_ollama_running()
    
    # If images but no vision model installed, fail early
    has_vision = is_vision_available()
    if images and not has_vision:
        return "⚠️ Vision capability is disabled. Please run `ollama pull moondream` in your terminal to analyze images."

    # If images are provided, use a vision model as preference
    models = [preferred_model]
    if images and preferred_model not in ["llama3.2-vision", "moondream", "llava", "bakllava"]:
        best_vision = get_best_vision_model()
        models = [best_vision] + models

    # Add standard fallbacks
    for m in ["llama3:latest", "mistral", "llama3", "mistral:latest"]:
        if m not in models:
            models.append(m)

    # Dynamic fallback: if all else fails, use whatever is actually installed
    installed = get_available_models()
    if installed:
        for m in installed:
            if m not in models:
                models.append(m)

    for model in models:
        try:
            print(f"[Ollama] Calling {model}...", flush=True)
            payload = {"model": model, "prompt": prompt, "stream": False}
            if images:
                payload["images"] = [img.split("base64,")[1] if "base64," in img else img for img in images]
                
            resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=300)
            if resp.status_code == 200:
                result = resp.json().get("response", "").strip()
                if result:
                    print(f"[Ollama] ✅ {model} responded.", flush=True)
                    return result
        except Exception as e:
            print(f"[Ollama] ⚠️  {model} failed: {e}", flush=True)

    return (
        "⚠️ Error: Ollama failed to respond. "
        "Ensure Ollama is running (`ollama serve`) and try again. "
        "First generation may take 2–3 minutes on CPU-only systems."
    )

async def ollama_stream(prompt: str, model: str = "llama3", images: list[str] = None):
    """
    Async generator — yields tokens from Ollama as they arrive.
    Used by the SSE /ask_stream/ endpoint.
    """
    ensure_ollama_running()

    # If a specific model is requested, try it first, then fallback to defaults.
    models_to_try = [model]
    
    # If images but no vision model installed, yield warning and stop
    has_vision = is_vision_available()
    if images and not has_vision:
        yield "⚠️ Vision capability is disabled. Please run `ollama pull moondream` in your terminal to analyze images."
        return

    # If images are provided, inject the best vision model as a preference
    if images and model not in ["llama3.2-vision", "llava", "moondream", "bakllava"]:
        best_vision = get_best_vision_model()
        models_to_try = [best_vision] + models_to_try

    models_to_try += ["llama3:latest", "mistral", "llama3", "mistral:latest"]
    
    # Dynamic fallback: ensure we try AT LEAST one model that exists
    installed = get_available_models()
    if installed:
        for m in installed:
            if m not in models_to_try:
                models_to_try.append(m)

    # Remove duplicates while preserving order
    seen = set()
    unique_models = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

    # Filter unique_models to only those that are actually installed to avoid "model not found" errors
    # during the primary attempt, unless we want to try them anyway as a last resort.
    # Actually, we should try the requested one first, then fallback.

    for m in unique_models:
        try:
            print(f"[Ollama] Streaming from {m}...", flush=True)
            # Use httpx for async streaming instead of requests.post(stream=True)
            import httpx
            async with httpx.AsyncClient(timeout=300) as client:
                payload = {"model": m, "prompt": prompt, "stream": True}
                if images:
                    payload["images"] = [img.split("base64,")[1] if "base64," in img else img for img in images]
                
                async with client.stream(
                    "POST",
                    f"{OLLAMA_URL}/api/generate",
                    json=payload,
                ) as resp:
                    if resp.status_code != 200:
                        continue
                        
                    # Buffer to accumulate tokens into chunked words/phrases for a smoother UI UX
                    buffer = ""
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except Exception:
                            continue
                        token = chunk.get("response", "")
                        if token:
                            buffer += token
                            # Yield only when we hit a logical break (space, newline, punctuation) or max size
                            if any(c in buffer for c in [" ", "\n", ".", ",", "!", "?", ":", ";"]) or len(buffer) > 20:
                                yield buffer
                                buffer = ""
                        if chunk.get("done", False):
                            if buffer:
                                yield buffer
                            print(f"[Ollama] ✅ Stream complete ({m}).", flush=True)
                            return
            return
        except Exception as e:
            print(f"[Ollama] ⚠️  Stream error ({m}): {e}", flush=True)

    # If we reached here, all models in unique_models failed.
    installed_str = ", ".join(installed) if installed else "No models found"
    yield f"\n\n⚠️ Error: Ollama failed to respond. Tried: {', '.join(unique_models)}. \n\nInstalled models: {installed_str}"

