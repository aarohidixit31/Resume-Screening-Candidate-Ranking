"""Extract raw text from resume/job-description files (PDF or DOCX)."""
import tempfile
from pathlib import Path

import pdfplumber
from docx import Document


def extract_text_from_pdf(path: Path) -> str:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def extract_text_from_docx(path: Path) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(path: Path, display_name: str | None = None) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix == ".docx":
        return extract_text_from_docx(path)
    raise ValueError(f"Unsupported file type: {suffix} ({display_name or path.name})")


def extract_text_from_bytes(data: bytes, filename: str) -> str:
    """Used by the API layer, which receives uploaded files as bytes rather than paths."""
    suffix = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        return extract_text(tmp_path, display_name=filename)
    finally:
        tmp_path.unlink(missing_ok=True)
