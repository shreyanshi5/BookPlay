from typing import Optional
import fitz  # PyMuPDF


def extract_text_from_pdf(path: str) -> str:
    """
    Extract text from a PDF file located at the given path using PyMuPDF.
    """
    doc: Optional[fitz.Document] = None
    try:
        doc = fitz.open(path)
        texts = []
        for page in doc:
            texts.append(page.get_text("text"))
        return "\n".join(texts)
    finally:
        if doc is not None:
            doc.close()

