import os
from config import UPLOAD_DIR
from utils.constants import FILE_EXT_RE, TABULAR_EXTS
from loaders.excel_loader import _load_excel

def _resolve_direct_file(query: str) -> tuple[str | None, str | None]:
    """
    If the query explicitly names a file that exists in uploads/,
    return (absolute_path, relative_path).  Otherwise (None, None).
    """
    fm = FILE_EXT_RE.search(query)
    if not fm:
        return None, None

    target = fm.group(1).strip().lower()
    for root, _, fnames in os.walk(UPLOAD_DIR):
        for fname in fnames:
            if fname.lower() == target:
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, UPLOAD_DIR).replace("\\\\", "/")
                return abs_path, rel_path

    return None, None

def _read_file_for_direct_query(abs_path: str) -> str:
    """Read raw file content for a directly-named file query."""
    ext = os.path.splitext(abs_path)[1].lower()

    if ext in TABULAR_EXTS:
        try:
            docs = _load_excel(abs_path)
            return "\\n\\n".join(d.page_content for d in docs)
        except Exception:
            return "Could not read spreadsheet."

    try:
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return "Could not read file."

def _topic_from_path(rel_path: str) -> str:
    return (
        os.path.splitext(os.path.basename(rel_path))[0]
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )

def _filter_by_selected(
    raw_docs: list,
    selected_files: list[str],
) -> list:
    """Keep only chunks whose source is in the selected-files list."""
    if not selected_files:
        return raw_docs

    norm = [f.replace("\\\\", "/").lower() for f in selected_files]
    filtered = []
    for doc, score in raw_docs:
        src = os.path.relpath(
            doc.metadata.get("source", ""), UPLOAD_DIR
        ).replace("\\\\", "/").lower()
        if src in norm:
            filtered.append((doc, score))
    return filtered
