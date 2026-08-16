"""Section-aware chunking (BRD FR-01, section 12.2 chunk-size constraint).

Resume text is chunked *within* sections so a chunk never spans two
sections, keeping its source_section label truthful for evidence citation.
"""

from __future__ import annotations

from typing import Dict, List

from ...schemas import ResumeChunk, Section


def chunk_text(
    text: str,
    section: Section,
    chunk_size: int = 512,
    overlap: int = 64,
) -> List[ResumeChunk]:
    """Split a section's text into overlapping character-based chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    chunks: List[ResumeChunk] = []
    start = 0
    index = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        piece = text[start:end].strip()
        if piece:
            chunks.append(
                ResumeChunk(
                    chunk_id=f"{section.value}:{index}",
                    source_section=section,
                    raw_text=piece,
                )
            )
            index += 1
        if end == text_len:
            break
        start = end - overlap

    return chunks


def chunk_document(
    sections: Dict[Section, List[str]],
    chunk_size: int = 512,
    overlap: int = 64,
) -> List[ResumeChunk]:
    """Chunk every section of an extracted resume document."""
    chunks: List[ResumeChunk] = []
    for section, lines in sections.items():
        section_text = "\n".join(lines)
        chunks.extend(chunk_text(section_text, section, chunk_size, overlap))
    return chunks
