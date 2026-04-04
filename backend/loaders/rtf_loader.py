from langchain_core.documents import Document

def _load_rtf(path: str):
    """Strip RTF markup and return a plain-text Document."""
    try:
        from striprtf.striprtf import rtf_to_text
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        return [Document(page_content=rtf_to_text(raw), metadata={"source": path})]
    except Exception as e:
        print(f"[RTF] Load error ({path}): {e}", flush=True)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return [Document(page_content=f.read(), metadata={"source": path})]
        except Exception:
            return []
