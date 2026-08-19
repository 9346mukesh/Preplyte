"""Section-aware chunking (BRD FR-01, section 12.2 chunk-size constraint).

Improved chunking strategy:
1. Split sections into sentences first
2. Group sentences into semantic chunks (max ~3-4 sentences each)
3. Preserve sentence boundaries — no mid-thought splits
4. Add sentence-level overlap between chunks for context continuity
5. Each chunk gets a section label for evidence citation
"""

from __future__ import annotations

import re
from typing import Dict, List

from ...schemas import ResumeChunk, Section

# Approximate token count per sentence (words + punctuation)
_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences, preserving the delimiters."""
    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _estimate_tokens(text: str) -> int:
    """Rough word count as a proxy for tokens."""
    return len(text.split())


def chunk_text(
    text: str,
    section: Section,
    max_chunk_tokens: int = 80,
    overlap_sentences: int = 1,
) -> List[ResumeChunk]:
    """Split a section's text into sentence-aware chunks.

    Args:
        text: Raw section text.
        section: Which resume section this is.
        max_chunk_tokens: Approximate max tokens per chunk (default 80 ~ 2-4 sentences).
        overlap_sentences: Number of sentences to overlap between consecutive chunks.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: List[ResumeChunk] = []
    start = 0
    index = 0

    while start < len(sentences):
        # Accumulate sentences until we hit the token budget
        end = start
        current_tokens = 0
        while end < len(sentences):
            sent_tokens = _estimate_tokens(sentences[end])
            if current_tokens + sent_tokens > max_chunk_tokens and end > start:
                break
            current_tokens += sent_tokens
            end += 1

        chunk_text_str = " ".join(sentences[start:end])
        chunks.append(
            ResumeChunk(
                chunk_id=f"{section.value}:{index}",
                source_section=section,
                raw_text=chunk_text_str,
            )
        )
        index += 1

        # Advance by (chunk_length - overlap) sentences
        advance = max(1, (end - start) - overlap_sentences)
        start += advance

    return chunks


def chunk_document(
    sections: Dict[Section, List[str]],
    max_chunk_tokens: int = 80,
    overlap_sentences: int = 1,
) -> List[ResumeChunk]:
    """Chunk every section of an extracted resume document."""
    chunks: List[ResumeChunk] = []
    for section, lines in sections.items():
        section_text = "\n".join(lines)
        chunks.extend(
            chunk_text(
                section_text,
                section,
                max_chunk_tokens=max_chunk_tokens,
                overlap_sentences=overlap_sentences,
            )
        )
    return chunks
