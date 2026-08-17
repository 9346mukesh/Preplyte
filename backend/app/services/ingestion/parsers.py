"""Resume ingestion: PDF/DOCX -> section-tagged text (BRD FR-01).

Section-aware extraction preserves skills/experience/projects/education
boundaries so downstream chunking and retrieval can cite evidence per
section (BRD section 10, Resume Chunk.source_section).
"""

from __future__ import annotations

import io
import re
from typing import Dict, List, Optional

from ...schemas import Section


class ParseError(Exception):
    """Raised when a resume document cannot be parsed (BRD NFR: Reliability)."""


_SECTION_HEADINGS: Dict[Section, List[str]] = {
    Section.SKILLS: [
        "skills",
        "technical skills",
        "core competencies",
        "technologies",
        "tech stack",
    ],
    Section.EXPERIENCE: [
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "internship",
        "internships",
        "work history",
    ],
    Section.PROJECTS: [
        "projects",
        "academic projects",
        "personal projects",
        "project experience",
    ],
    Section.EDUCATION: [
        "education",
        "academic background",
        "academic qualifications",
        "qualifications",
    ],
}


def extract_text_from_docx(content: bytes) -> str:
    """Extract all paragraph text from a DOCX document."""
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover
        raise ParseError("python-docx is not installed (see backend/requirements.txt)") from exc
    try:
        document = Document(io.BytesIO(content))
    except Exception as exc:
        raise ParseError("Unable to read DOCX file") from exc
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text_from_pdf(content: bytes, max_pages: Optional[int] = None) -> str:
    """Extract text from a PDF, page by page (BRD FR-01).

    When ``max_pages`` is set, resumes longer than the limit are rejected
    with a clear error rather than silently truncated (BRD NFR Reliability;
    the limit is MAX_RESUME_PAGES, default 5).
    """
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover
        raise ParseError("pdfplumber is not installed (see backend/requirements.txt)") from exc
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            if max_pages is not None and len(pdf.pages) > max_pages:
                raise ParseError(
                    f"Resume has {len(pdf.pages)} pages, which exceeds the "
                    f"{max_pages}-page limit (MAX_RESUME_PAGES). "
                    "Please upload a shorter resume."
                )
            pages = [page.extract_text() or "" for page in pdf.pages]
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError("Unable to read PDF file") from exc
    return "\n".join(pages).strip()


def detect_section(line: str) -> Optional[Section]:
    """Return the section a heading line belongs to, if any."""
    normalized = re.sub(r"[^a-z0-9 ]", " ", line.strip().lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    for section, headings in _SECTION_HEADINGS.items():
        for heading in headings:
            if normalized == heading or normalized.startswith(heading + " "):
                return section
    return None


def extract_sections(text: str) -> Dict[Section, List[str]]:
    """Split flat resume text into section buckets using heading heuristics.

    Lines before the first recognized heading are treated as header/contact
    information and fall into Section.OTHER.
    """
    sections: Dict[Section, List[str]] = {section: [] for section in Section}
    current = Section.OTHER
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        detected = detect_section(line)
        if detected is not None:
            current = detected
            continue
        sections[current].append(line)
    return sections
