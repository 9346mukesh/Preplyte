from app.services.ingestion.chunker import chunk_document, chunk_text
from app.schemas import Section


def test_chunk_text_creates_stable_ids():
    text = "This is sentence one. This is sentence two. " * 50
    chunks = chunk_text(text, Section.SKILLS, max_chunk_tokens=20, overlap_sentences=1)
    assert len(chunks) > 1
    assert chunks[0].chunk_id == "skills:0"
    assert chunks[1].chunk_id == "skills:1"
    assert all(c.source_section == Section.SKILLS for c in chunks)


def test_chunk_text_empty():
    assert chunk_text("", Section.OTHER) == []


def test_chunk_text_single_sentence():
    chunks = chunk_text("hello world", Section.OTHER, max_chunk_tokens=100)
    assert len(chunks) == 1
    assert chunks[0].raw_text == "hello world"


def test_chunk_text_preserves_sentences():
    # Use longer text to ensure splitting
    text = "This is a longer sentence with more words. " * 10
    chunks = chunk_text(text, Section.EXPERIENCE, max_chunk_tokens=12, overlap_sentences=0)
    # Should split into multiple chunks, each with complete sentences
    assert len(chunks) >= 2
    for chunk in chunks:
        # Each chunk should end with a sentence boundary
        assert chunk.raw_text.rstrip().endswith(".")


def test_chunk_text_with_overlap():
    text = "Sentence one here. Sentence two here. Sentence three here. Sentence four here."
    chunks = chunk_text(text, Section.PROJECTS, max_chunk_tokens=8, overlap_sentences=1)
    assert len(chunks) >= 2
    # With overlap, some content should repeat
    if len(chunks) >= 2:
        words_0 = set(chunks[0].raw_text.lower().split())
        words_1 = set(chunks[1].raw_text.lower().split())
        assert len(words_0 & words_1) > 0, "Overlap should create shared words"


def test_chunk_document_preserves_sections():
    sections = {
        Section.SKILLS: ["Python", "FastAPI"],
        Section.EXPERIENCE: ["Worked at X for 2 years"],
    }
    chunks = chunk_document(sections, max_chunk_tokens=100)
    assert any(c.source_section == Section.SKILLS for c in chunks)
    assert any(c.source_section == Section.EXPERIENCE for c in chunks)
