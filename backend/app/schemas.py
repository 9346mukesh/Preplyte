"""Pydantic schemas mirroring the BRD section 10 data requirements.

These are pure data models (no I/O), shared across the ingestion, retrieval,
analysis, and report stages of the pipeline.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Section(str, Enum):
    """Resume sections preserved by section-aware extraction (FR-01)."""

    SKILLS = "skills"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    EDUCATION = "education"
    OTHER = "other"


class ResumeChunk(BaseModel):
    """A single retrievable unit of resume content (BRD section 10)."""

    chunk_id: str
    source_section: Section
    raw_text: str
    embedding: Optional[List[float]] = None


class RequirementCategory(str, Enum):
    MUST_HAVE = "must-have"
    NICE_TO_HAVE = "nice-to-have"


class JDRequirement(BaseModel):
    """A structured requirement extracted from the JD (BRD section 10)."""

    requirement_id: str
    requirement_text: str
    category: RequirementCategory = RequirementCategory.MUST_HAVE
    experience_years: Optional[float] = None
    embedding: Optional[List[float]] = None


class RetrievalResult(BaseModel):
    """Top-k retrieval output for one requirement (BRD FR-04 / FR-07)."""

    requirement_id: str
    retrieved_chunk_ids: List[str] = Field(default_factory=list)
    similarity_scores: List[float] = Field(default_factory=list)
    threshold_pass: bool = False


class Classification(str, Enum):
    PRESENT = "present"
    PARTIAL = "partial"
    MISSING = "missing"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class AnalysisResult(BaseModel):
    """Grounded gap classification with cited evidence (BRD FR-05 / FR-06)."""

    requirement_id: str
    classification: Classification
    evidence_citation: Optional[str] = None
    confidence_note: Optional[str] = None


class QuestionType(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"


class InterviewQuestion(BaseModel):
    """A generated interview question (BRD section 10 / FR-08)."""

    question_id: str
    related_requirement_id: Optional[str] = None
    question_text: str
    question_type: QuestionType


class Report(BaseModel):
    """The final analysis report surfaced in the web UI (BRD FR-09)."""

    job_title: Optional[str] = None
    requirements: List[JDRequirement] = Field(default_factory=list)
    retrieval: List[RetrievalResult] = Field(default_factory=list)
    analyses: List[AnalysisResult] = Field(default_factory=list)
    interview_questions: List[InterviewQuestion] = Field(default_factory=list)
    latency_ms: Optional[float] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: List[str] = Field(default_factory=list)
