from langchain_core.documents import Document

def _load_pdf_with_ocr(path: str):
    """
    Enhanced PDF loader using PyMuPDF (fitz) with RapidOCR fallback for image pages.
    """
    import fitz  # PyMuPDF
    try:
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        # Fallback to standard PyPDF if dependencies are missing
        from langchain_community.document_loaders import PyPDFLoader
        return PyPDFLoader(path).load()

    docs = []
    ocr_engine = None  # Lazy load OCR engine

    try:
        pdf_doc = fitz.open(path)
        for page_num, page in enumerate(pdf_doc):
            text = page.get_text().strip()
            
            # If text is insufficient (likely a scan), try OCR
            if len(text) < 100:
                print(f"  [PDF-OCR] Page {page_num+1} seems to be an image. Running OCR...", flush=True)
                if ocr_engine is None:
                    ocr_engine = RapidOCR()
                
                # Render page to image (pixmap)
                # 2x zoom (DPI 144) is usually enough for OCR without being too slow
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
                
                # Convert Pixmap to image array
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                
                result, _ = ocr_engine(img)
                if result:
                    # result is a list of [box, text, score]
                    ocr_text = "\\n".join([line[1] for line in result])
                    if ocr_text.strip():
                        text = ocr_text
            
            if text.strip():
                docs.append(Document(
                    page_content=text,
                    metadata={"source": path, "page": page_num + 1}
                ))
        pdf_doc.close()
    except Exception as e:
        print(f"[PDF-OCR] Error loading {path}: {e}", flush=True)
        # Final fallback to standard PyPDF
        from langchain_community.document_loaders import PyPDFLoader
        try:
            return PyPDFLoader(path).load()
        except:
            return []

    return docs
