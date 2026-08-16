"""Structured JD requirement extraction (BRD FR-02).

V1 uses deterministic heuristics (bullet splitting + must/nice-to-have cues)
so the pipeline runs without an LLM. An LLM-backed extractor (BRD risk R-3,
few-shot structured JSON) can be swapped in without changing callers.
"""

from __future__ import annotations

import re
from typing import List

from ..schemas import JDRequirement, RequirementCategory


def _split_requirements(jd_text: str) -> List[str]:
    """Split JD text into candidate requirement strings."""
    lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
    joined = " ".join(lines)
    # Bullet-style separators first.
    parts = re.split(r"(?:^|\s)[\u2022*\-]\s+", joined)
    parts = [part.strip(" ,;") for part in parts if part.strip(" ,;")]
    if len(parts) <= 1:
        # Fall back to sentence splitting on periods/semicolons.
        parts = [s.strip() for s in re.split(r"[.;]\s+", jd_text) if s.strip()]
    return parts


_MUST_CUES = [
    "must",
    "required",
    "proficiency in",
    "experience with",
    "experience in",
    "expert",
    "strong",
    "solid",
    "hands-on",
]
_NICE_CUES = [
    "nice to have",
    "preferred",
    "plus",
    "bonus",
    "advantageous",
    "desirable",
    "a plus",
]


def _categorize(requirement_text: str) -> RequirementCategory:
    lower = requirement_text.lower()
    if any(cue in lower for cue in _NICE_CUES):
        return RequirementCategory.NICE_TO_HAVE
    return RequirementCategory.MUST_HAVE


def extract_requirements(jd_text: str) -> List[JDRequirement]:
    """Extract structured requirements from JD text (FR-02)."""
    raw = _split_requirements(jd_text)
    requirements: List[JDRequirement] = []
    for index, text in enumerate(raw):
        if len(text) < 3:
            continue
        requirements.append(
            JDRequirement(
                requirement_id=f"req-{index}",
                requirement_text=text,
                category=_categorize(text),
            )
        )
    return requirements
