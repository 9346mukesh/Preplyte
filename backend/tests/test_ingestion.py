"""End-to-end ingestion tests: real PDF/DOCX bytes -> section-tagged chunks.

Day 2 push goal: PDF/DOCX -> section-tagged chunks (BRD FR-01). These tests
exercise the actual file parsers (not just the section heuristics) by
building a real DOCX in memory with python-docx and a minimal valid PDF.
"""

from io import BytesIO
from typing import List

import pytest

from app.services.ingestion import ingest_resume
from app.services.ingestion.parsers import ParseError, extract_text_from_pdf
from app.schemas import Section

RESUME_LINES = [
    "John Doe",
    "john@example.com | Bengaluru, India",
    "SKILLS",
    "Python, FastAPI, PostgreSQL, React",
    "EXPERIENCE",
    "Backend Engineer Intern at Acme Corp",
    "Built a REST API with FastAPI",
    "PROJECTS",
    "Resume Analyzer - RAG app comparing resumes to JDs",
    "EDUCATION",
    "B.Tech CSE, GITAM University, 2023-2027",
]


def _build_docx(lines: List[str]) -> bytes:
    """Create an in-memory DOCX whose paragraphs are the given lines."""
    from docx import Document

    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(pages: List[str]) -> bytes:
    """Build a minimal valid PDF with one content stream per page.

    Object layout per page i (0-based): page=3+3i, content=4+3i, font=5+3i.
    """
    out = bytearray(b"%PDF-1.4\n")
    num_pages = len(pages)
    kids = " ".join(f"{3 + 3 * i} 0 R" for i in range(num_pages))

    bodies: List[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {num_pages} >>".encode(),
    ]
    for i, text in enumerate(pages):
        page_num, content_num, font_num = 3 + 3 * i, 4 + 3 * i, 5 + 3 * i
        bodies.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_num} 0 R "
                f"/Resources << /Font << /F1 {font_num} 0 R >> >> >>"
            ).encode()
        )
        lines = text.splitlines() or [""]
        # 12 TL sets the text leading so each T* drops to a distinct baseline.
        stream = "BT /F1 12 Tf 12 TL 72 720 Td\n" + "\n".join(
            f"({_pdf_escape(line)}) Tj T*" for line in lines
        ) + "\nET"
        stream_bytes = stream.encode("latin-1")
        bodies.append(
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1")
            + stream_bytes
            + b"\nendstream"
        )
        bodies.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    offsets = []
    for number, body in enumerate(bodies, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_position = len(out)
    out += f"xref\n0 {len(bodies) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(bodies) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_position}\n%%EOF\n"
    ).encode()
    return bytes(out)


def _assert_section_tagged(chunks):
    by_section = {
        section: [c.raw_text for c in chunks if c.source_section == section]
        for section in Section
    }
    assert any("Python, FastAPI" in t for t in by_section[Section.SKILLS])
    assert any("REST API with FastAPI" in t for t in by_section[Section.EXPERIENCE])
    assert any("RAG app" in t for t in by_section[Section.PROJECTS])
    assert any("GITAM University" in t for t in by_section[Section.EDUCATION])
    assert any(
        "john@example.com | Bengaluru, India" in t for t in by_section[Section.OTHER]
    )
    assert all(c.chunk_id.startswith(c.source_section.value + ":") for c in chunks)


def test_docx_to_section_tagged_chunks():
    chunks = ingest_resume(_build_docx(RESUME_LINES), "resume.docx")
    assert chunks
    _assert_section_tagged(chunks)


def test_pdf_to_section_tagged_chunks():
    pdf = _build_pdf(["\n".join(RESUME_LINES)])
    chunks = ingest_resume(pdf, "resume.pdf")
    assert chunks
    _assert_section_tagged(chunks)


def test_pdf_page_limit_rejected_clearly():
    pdf = _build_pdf(["page one", "page two", "page three"])
    with pytest.raises(ParseError, match="3 pages"):
        extract_text_from_pdf(pdf, max_pages=2)
    with pytest.raises(ParseError, match="MAX_RESUME_PAGES"):
        ingest_resume(pdf, "resume.pdf", max_pages=1)


def test_unsupported_extension_rejected():
    with pytest.raises(ParseError, match="Unsupported file type"):
        ingest_resume(b"not a real resume", "resume.txt")


def test_garbage_pdf_rejected():
    with pytest.raises(ParseError, match="Unable to read PDF"):
        extract_text_from_pdf(b"this is not a pdf at all")


def test_run_analysis_pipeline_accepts_docx_and_jd():
    """The /analyze path parses a real DOCX and returns JD requirements."""
    from app.services.pipeline import run_analysis

    report = run_analysis(
        _build_docx(RESUME_LINES),
        "resume.docx",
        jd_text="Requirements: Python (must have), FastAPI, Docker",
    )
    assert report.latency_ms is not None
    assert any("FastAPI" in r.requirement_text for r in report.requirements)
    assert any("Days 4-5" in w for w in report.warnings)
