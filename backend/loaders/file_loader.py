import os
from .pdf_loader import _load_pdf_with_ocr
from .excel_loader import _load_excel
from .rtf_loader import _load_rtf

def _load_file(path: str):
    """
    Dispatch to the correct LangChain loader for a given file path.
    Returns a list of Documents (empty list on failure).
    """
    from langchain_community.document_loaders import (
        PyPDFLoader, TextLoader, Docx2txtLoader,
        UnstructuredWordDocumentLoader, CSVLoader,
        UnstructuredPowerPointLoader, UnstructuredODTLoader,
    )

    ext  = os.path.splitext(path)[1].lower()
    docs = []

    try:
        if ext == ".pdf":
            docs = _load_pdf_with_ocr(path)

        elif ext in (".docx", ".doc"):
            try:
                docs = Docx2txtLoader(path).load()
            except Exception:
                docs = UnstructuredWordDocumentLoader(path).load()

        elif ext in (".xlsx", ".xls"):
            docs = _load_excel(path)

        elif ext == ".csv":
            docs = CSVLoader(path).load()

        elif ext in (".pptx", ".ppt"):
            try:
                docs = UnstructuredPowerPointLoader(path).load()
            except Exception as e:
                print(f"[PPT] Load error ({os.path.basename(path)}): {e}", flush=True)

        elif ext in (".odt", ".ods", ".odp"):
            docs = UnstructuredODTLoader(path).load()

        elif ext == ".rtf":
            docs = _load_rtf(path)

        elif ext in (
            ".txt", ".py", ".js", ".ts", ".jsx", ".tsx",
            ".css", ".json", ".xml", ".md", ".c", ".cpp",
            ".cs", ".go", ".java", ".rb", ".php", ".html",
            ".htm", ".sh", ".bash", ".yaml", ".yml", ".toml",
        ):
            docs = TextLoader(path, encoding="utf-8").load()

    except Exception as e:
        print(f"[Loader] Error loading {os.path.basename(path)}: {e}", flush=True)

    return docs
