from pathlib import Path

import pymupdf


def extract_text_from_pdf(file_path: Path) -> str:
    doc = pymupdf.open(str(file_path))
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_text(file_path: Path, lesson_type: str) -> str:
    if lesson_type == "pdf":
        return extract_text_from_pdf(file_path)
    if lesson_type == "text":
        return file_path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported lesson type for extraction: {lesson_type}")
