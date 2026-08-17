"""End-to-end analysis orchestrator (BRD section 11 workflow).

Stages:
  1. parse resume (FR-01)                 -- Day 1/2 (implemented)
  2. extract JD requirements (FR-02)      -- Day 2 (implemented, heuristics)
  3. embed chunks + requirements (FR-03)  -- Day 3
  4. store resume embeddings (FR-04)      -- Day 3
  5. top-k retrieval + threshold (FR-07)  -- Day 3
  6. grounded classification (FR-05/06)   -- Day 4
  7. verification pass (FR-06)            -- Day 4
  8. interview questions (FR-08)          -- Day 5
  9. structured report (FR-09)            -- Day 5
"""

from __future__ import annotations

import time

from ..config import get_settings
from ..schemas import Report
from .ingestion import ingest_resume
from .jd_extractor import extract_requirements


def run_analysis(content: bytes, filename: str, jd_text: str) -> Report:
    """Run the full analysis pipeline and return a Report."""
    settings = get_settings()
    started = time.perf_counter()
    warnings: list = []

    # Stage 1: parse resume into section-tagged chunks (FR-01)
    chunks = ingest_resume(
        content,
        filename,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
        max_pages=settings.max_resume_pages,
    )
    del chunks  # consumed by the Day 3 retrieval stage

    # Stage 2: structured JD requirements (FR-02)
    requirements = extract_requirements(jd_text)
    warnings.append(
        "Stages 3-8 (embeddings, retrieval, grounded analysis, questions) "
        "land on Days 3-5 of the build plan."
    )

    latency_ms = (time.perf_counter() - started) * 1000.0
    return Report(
        requirements=requirements,
        latency_ms=latency_ms,
        warnings=warnings,
    )
