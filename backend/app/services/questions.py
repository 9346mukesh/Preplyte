"""Interview question generation (BRD FR-08 / US-4).

Generates a minimum of 5 role-specific questions (technical/behavioral)
tailored to the JD and the candidate's identified gaps.
"""

from __future__ import annotations

from typing import List

from ..schemas import AnalysisResult, InterviewQuestion, JDRequirement


def generate_questions(
    requirements: List[JDRequirement],
    analyses: List[AnalysisResult],
    minimum: int = 5,
) -> List[InterviewQuestion]:
    """Generate interview questions from the JD and identified gaps."""
    raise NotImplementedError(
        "Question generation lands on Day 5 (report milestone)"
    )
