"""Resume ingestion: PDF/DOCX -> section-tagged chunks (BRD FR-01).

Day 2 milestone: `ingest_resume` is the single entry point that turns an
uploaded resume (PDF or DOCX bytes) into retrievable, section-tagged
`ResumeChunk`s — the unit consumed by the Day 3 retrieval pipeline.
"""

from __future__ import annotations

from typing import List, Optional

from ...config import get_settings
from ...schemas import ResumeChunk
from .chunker import chunk_document, chunk_text
from .parsers import (
    ParseError,
    detect_section,
    extract_sections,
    extract_text_from_docx,
    extract_text_from_pdf,
)

__all__ = [
    "ParseError",
    "chunk_document",
    "chunk_text",
    "detect_section",
    "extract_sections",
    "ingest_resume",
]


def ingest_resume(
    content: bytes,
    filename: str,
    max_chunk_tokens: Optional[int] = None,
    overlap_sentences: Optional[int] = None,
    max_pages: Optional[int] = None,
) -> List[ResumeChunk]:
    """Parse a resume (PDF/DOCX) into section-tagged chunks (FR-01).

    The parser is selected from the file extension rather than the upload
    content-type header, so the file type cannot be spoofed. Values default
    to the env-driven settings.
    """
    settings = get_settings()
    name = filename.lower()

    if name.endswith(".pdf"):
        raw_text = extract_text_from_pdf(
            content,
            max_pages=max_pages
            if max_pages is not None
            else settings.max_resume_pages,
        )
    elif name.endswith((".docx", ".doc")):
        raw_text = extract_text_from_docx(content)
    else:
        raise ParseError(
            f"Unsupported file type: {filename!r} (expected PDF or DOCX)"
        )

    sections = extract_sections(raw_text)
    return chunk_document(
        sections,
        max_chunk_tokens=max_chunk_tokens
        if max_chunk_tokens is not None
        else settings.max_chunk_tokens,
        overlap_sentences=overlap_sentences
        if overlap_sentences is not None
        else settings.overlap_sentences,
    )
