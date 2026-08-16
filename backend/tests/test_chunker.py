from app.services.ingestion.chunker import chunk_document, chunk_text
from app.schemas import Section


def test_chunk_text_creates_stable_ids():
    chunks = chunk_text("word " * 500, Section.SKILLS, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert chunks[0].chunk_id == "skills:0"
    assert chunks[1].chunk_id == "skills:1"
    assert all(c.source_section == Section.SKILLS for c in chunks)
    # Overlap means the tail of chunk 0 reappears at the start of chunk 1.
    assert chunks[0].raw_text[-20:] in chunks[1].raw_text


def test_chunk_text_empty():
    assert chunk_text("", Section.OTHER) == []


def test_chunk_text_smaller_than_chunk_size():
    chunks = chunk_text("hello", Section.OTHER, chunk_size=512, overlap=64)
    assert len(chunks) == 1
    assert chunks[0].raw_text == "hello"


def test_chunk_text_rejects_bad_params():
    try:
        chunk_text("x" * 10, Section.OTHER, chunk_size=0)
        assert False, "expected ValueError"
    except ValueError:
        pass
    try:
        chunk_text("x" * 10, Section.OTHER, chunk_size=10, overlap=10)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_chunk_document_preserves_sections():
    sections = {
        Section.SKILLS: ["Python", "FastAPI"],
        Section.EXPERIENCE: ["Worked at X for 2 years"],
    }
    chunks = chunk_document(sections, chunk_size=512, overlap=64)
    assert any(c.source_section == Section.SKILLS for c in chunks)
    assert any(c.source_section == Section.EXPERIENCE for c in chunks)
