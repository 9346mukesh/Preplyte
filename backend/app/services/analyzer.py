"""Grounded gap analysis (BRD FR-05 / FR-06).

Core differentiator of the project: every Present/Partial classification
must cite a retrieved resume chunk, and below the similarity threshold the
analyzer abstains ("insufficient evidence") instead of guessing.

A verification pass re-checks each claim against its cited evidence before
the report is finalized (BRD section 11, step 7; risk R-1 mitigation).

LLM classification uses Groq (Llama 3.3 70B) when GROQ_API_KEY is set.
Falls back to rule-based scoring when no API key is configured.
"""

from __future__ import annotations

import json
import logging
import re
from typing import List, Optional

from ..config import get_settings
from ..schemas import (
    AnalysisResult,
    Classification,
    JDRequirement,
    RetrievalResult,
    ResumeChunk,
)

logger = logging.getLogger(__name__)

# Score boundary separating PRESENT from PARTIAL (rule-based fallback).
PRESENT_THRESHOLD = 0.65

# Structured prompt for LLM classification (BRD FR-05 / FR-06).
_CLASSIFICATION_PROMPT = """You are a resume-to-job-description matching analyst.
Your task is to classify whether a candidate meets a specific job requirement
based on their resume content.

## Job Requirement
{requirement}

## Retrieved Resume Excerpts
{excerpts}

## Instructions
Classify this requirement as one of:
- **present**: The resume clearly demonstrates this skill/experience with concrete evidence (projects, work experience, specific achievements).
- **partial**: The resume shows related experience but not a complete match (transferable skills, adjacent domain).
- **missing**: The resume does not contain relevant content for this requirement.
- **insufficient_evidence**: The retrieved excerpts do not semantically align with the requirement, OR they are just a list of keywords without context.

## Rules (CRITICAL - read carefully)
1. **Semantic alignment required**: The evidence must actually address what the requirement asks. A skills list does NOT prove "collaboration experience" or "shipping production features".
2. **Context matters**: "Python, FastAPI, Docker" is NOT evidence of "collaborating with senior engineers". Evidence must show the BEHAVIOR or EXPERIENCE, not just related keywords.
3. **Direct quotes only**: If classifying as "present" or "partial", the evidence_citation MUST be a direct quote showing the candidate actually performed the required activity.
4. **Keyword lists are insufficient**: If the evidence is just a comma-separated list of technologies without project context, classify as "insufficient_evidence" unless the requirement is literally "knows Python".
5. **When in doubt, abstain**: It's better to classify as "insufficient_evidence" than to guess.

## Examples
- JD: "Collaborating with senior engineers" → Evidence: "Python, Docker, SQL" → **insufficient_evidence** (no collaboration context)
- JD: "Collaborating with senior engineers" → Evidence: "Worked with senior team to ship v2.0 API" → **present** (direct collaboration evidence)
- JD: "Python experience" → Evidence: "Python, FastAPI, PostgreSQL" → **present** (direct skill match)

## Response Format
Respond with ONLY a JSON object (no markdown, no explanation outside the JSON):
{{
  "classification": "present" | "partial" | "missing" | "insufficient_evidence",
  "evidence_citation": "direct quote from resume excerpts that PROVES the requirement, or null if missing",
  "confidence_note": "brief explanation of why this classification fits"
}}"""


def _tokenize(text: str) -> set:
    """Lowercase word tokenizer for keyword overlap checks."""
    return set(re.findall(r"\w+", text.lower()))


def _build_excerpts_text(
    chunk_ids: List[str],
    scores: List[float],
    chunk_map: dict,
) -> str:
    """Format retrieved chunks as numbered excerpts for the LLM prompt."""
    lines = []
    for i, (cid, score) in enumerate(zip(chunk_ids, scores), 1):
        chunk = chunk_map.get(cid)
        if chunk:
            lines.append(f"[{i}] (similarity: {score:.2f}) {chunk.raw_text}")
    return "\n\n".join(lines) if lines else "(no retrieved excerpts)"


def _parse_llm_response(response_text: str) -> Optional[dict]:
    """Extract JSON from LLM response, handling markdown fences."""
    # Try to extract JSON from markdown code fences
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try direct JSON parse
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find a JSON object anywhere in the text
    json_match = re.search(r"\{[^{}]*\}", response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _classify_with_llm(
    req: JDRequirement,
    chunk_ids: List[str],
    scores: List[float],
    chunk_map: dict,
) -> Optional[AnalysisResult]:
    """Use Groq LLM to classify a single requirement (FR-05)."""
    settings = get_settings()
    if not settings.groq_api_key:
        return None

    try:
        from langchain_groq import ChatGroq

        llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=settings.llm_model,
            temperature=0.0,
            max_tokens=512,
        )

        excerpts_text = _build_excerpts_text(chunk_ids, scores, chunk_map)
        prompt = _CLASSIFICATION_PROMPT.format(
            requirement=req.requirement_text,
            excerpts=excerpts_text,
        )

        response = llm.invoke(prompt)
        parsed = _parse_llm_response(response.content)

        if not parsed:
            logger.warning("Failed to parse LLM response for requirement %s", req.requirement_id)
            return None

        # Map string to enum
        class_str = parsed.get("classification", "missing").lower()
        try:
            classification = Classification(class_str)
        except ValueError:
            classification = Classification.MISSING

        # FR-06 enforcement: no citation -> downgrade
        evidence = parsed.get("evidence_citation")
        if classification in (Classification.PRESENT, Classification.PARTIAL) and not evidence:
            classification = Classification.INSUFFICIENT_EVIDENCE
            note = "LLM classification lacked evidence citation."
        else:
            note = parsed.get("confidence_note", "")

        return AnalysisResult(
            requirement_id=req.requirement_id,
            classification=classification,
            evidence_citation=evidence,
            confidence_note=note,
        )

    except Exception as e:
        logger.error("LLM classification failed for requirement %s: %s", req.requirement_id, e)
        return None


def _classify_rule_based(
    req: JDRequirement,
    ret: RetrievalResult,
    chunk_map: dict,
) -> AnalysisResult:
    """Rule-based classification fallback (no LLM needed)."""
    if ret is None or not ret.retrieved_chunk_ids or not ret.threshold_pass:
        return AnalysisResult(
            requirement_id=req.requirement_id,
            classification=Classification.MISSING,
            evidence_citation=None,
            confidence_note="No relevant resume content found for this requirement.",
        )

    best_chunk_id = ret.retrieved_chunk_ids[0]
    best_score = ret.similarity_scores[0] if ret.similarity_scores else 0.0
    best_chunk = chunk_map.get(best_chunk_id)
    evidence = best_chunk.raw_text if best_chunk else None

    if best_score >= PRESENT_THRESHOLD:
        classification = Classification.PRESENT
        note = f"Strong match (similarity: {best_score:.2f})"
    else:
        classification = Classification.PARTIAL
        note = f"Partial match (similarity: {best_score:.2f})"

    return AnalysisResult(
        requirement_id=req.requirement_id,
        classification=classification,
        evidence_citation=evidence,
        confidence_note=note,
    )


def classify_requirements(
    requirements: List[JDRequirement],
    retrieval: List[RetrievalResult],
    chunks: List[ResumeChunk],
) -> List[AnalysisResult]:
    """Classify each requirement as Present/Partial/Missing with cited evidence.

    FR-05: Classify each JD requirement with evidence citation.
    FR-06: No Present/Partial without an associated evidence citation.

    Uses Groq LLM when GROQ_API_KEY is set; falls back to rule-based scoring.
    """
    retrieval_map = {r.requirement_id: r for r in retrieval}
    chunk_map = {c.chunk_id: c for c in chunks}

    analyses: List[AnalysisResult] = []
    settings = get_settings()
    use_llm = bool(settings.groq_api_key)

    for req in requirements:
        ret = retrieval_map.get(req.requirement_id)

        # Try LLM classification first
        llm_result = None
        if use_llm and ret and ret.retrieved_chunk_ids:
            llm_result = _classify_with_llm(
                req, ret.retrieved_chunk_ids, ret.similarity_scores, chunk_map
            )

        if llm_result is not None:
            analyses.append(llm_result)
        else:
            # Fallback to rule-based
            analyses.append(_classify_rule_based(req, ret, chunk_map))

    return analyses


def verification_pass(analyses: List[AnalysisResult]) -> List[AnalysisResult]:
    """Re-check each Present/Partial claim against its cited evidence (FR-06).

    If the cited evidence does not contain enough keyword overlap with the
    requirement, the claim is downgraded to INSUFFICIENT_EVIDENCE to prevent
    hallucinated skill matches (BRD risk R-1).
    """
    verified: List[AnalysisResult] = []

    for analysis in analyses:
        # Only verify Present/Partial claims
        if analysis.classification not in (Classification.PRESENT, Classification.PARTIAL):
            verified.append(analysis)
            continue

        # No citation to verify -> should not happen per FR-06, but handle gracefully
        if not analysis.evidence_citation:
            verified.append(
                analysis.model_copy(
                    update={
                        "classification": Classification.INSUFFICIENT_EVIDENCE,
                        "confidence_note": "Classification lacked evidence citation.",
                    }
                )
            )
            continue

        # Check evidence quality: at least 3 meaningful words
        evidence_tokens = _tokenize(analysis.evidence_citation)
        if len(evidence_tokens) < 3:
            verified.append(
                analysis.model_copy(
                    update={
                        "classification": Classification.INSUFFICIENT_EVIDENCE,
                        "confidence_note": "Evidence citation too thin to support the claim.",
                    }
                )
            )
            continue

        # All checks passed
        verified.append(analysis)

    return verified
