import hashlib
import io
from pathlib import Path
from typing import Tuple

import docx
import pymupdf

from ..config import settings

_rapid_ocr_engine = None


def _get_ocr_engine():
    global _rapid_ocr_engine
    if _rapid_ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR

            _rapid_ocr_engine = RapidOCR()
        except Exception:
            _rapid_ocr_engine = False
    return _rapid_ocr_engine if _rapid_ocr_engine is not False else None


def validate_upload_file(filename: str, content: bytes) -> Tuple[str, str]:
    """Validate extension, size, and return (ext, sha256_hash)."""
    if not filename:
        raise ValueError("Missing filename.")
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file format '{ext}'. Allowed: PDF and DOCX.")
    if not content or len(content) == 0:
        raise ValueError("Uploaded file is empty.")
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(
            f"File size ({len(content) / (1024 * 1024):.2f} MB) exceeds limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )
    file_hash = hashlib.sha256(content).hexdigest()
    return ext, file_hash


def extract_text_from_pdf(content: bytes) -> dict:
    """Extract text from PDF using PyMuPDF, with OCR fallback for scanned PDFs."""
    doc = pymupdf.open(stream=content, filetype="pdf")
    pages_text: list[str] = []
    for page in doc:
        text = page.get_text("text") or ""
        pages_text.append(text.strip())

    combined = "\n".join(t for t in pages_text if t).strip()
    ocr_used = False

    # Fallback to OCR if PDF appears to be scanned / image-only
    if len(combined) < 80 and len(doc) > 0:
        ocr_engine = _get_ocr_engine()
        ocr_pages: list[str] = []
        if ocr_engine is not None:
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                result, _ = ocr_engine(img_bytes)
                if result:
                    lines = [item[1] for item in result if len(item) >= 2 and item[1]]
                    ocr_pages.append("\n".join(lines))
        else:
            # Secondary fallback if pytesseract + system tesseract are available
            try:
                import pytesseract
                from PIL import Image

                for page in doc:
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_pages.append(pytesseract.image_to_string(img))
            except Exception:
                pass

        ocr_combined = "\n".join(p for p in ocr_pages if p.strip()).strip()
        if len(ocr_combined) > len(combined):
            combined = ocr_combined
            ocr_used = True

    page_count = len(doc)
    doc.close()
    return {
        "text": combined,
        "ocr_used": ocr_used,
        "page_count": page_count,
        "file_type": "pdf",
    }


def extract_text_from_docx(content: bytes) -> dict:
    """Extract text from DOCX paragraphs and tables."""
    document = docx.Document(io.BytesIO(content))
    parts: list[str] = []

    for para in document.paragraphs:
        txt = para.text.strip()
        if txt:
            parts.append(txt)

    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(dict.fromkeys(cells)))

    return {
        "text": "\n".join(parts).strip(),
        "ocr_used": False,
        "page_count": 1,
        "file_type": "docx",
    }


def extract_resume_text(filename: str, content: bytes) -> dict:
    """Dispatch extraction by file extension after validation."""
    ext, file_hash = validate_upload_file(filename, content)
    if ext == ".pdf":
        result = extract_text_from_pdf(content)
    elif ext == ".docx":
        result = extract_text_from_docx(content)
    else:
        raise ValueError(f"Unsupported extension: {ext}")

    if not result["text"] or len(result["text"].strip()) < 20:
        raise ValueError("Unable to extract meaningful text from the uploaded document.")

    result["file_hash"] = file_hash
    result["file_size"] = len(content)
    return result
