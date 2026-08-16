from app.services.jd_extractor import extract_requirements
from app.schemas import RequirementCategory

SAMPLE_JD = """We are looking for a backend engineer.

Responsibilities:
- Build scalable APIs with Python and FastAPI
- Work with PostgreSQL and Redis

Requirements:
- 3+ years of experience with Python (must have)
- Strong knowledge of FastAPI
- Familiarity with Docker
- Nice to have: experience with Kubernetes
- Excellent communication skills
"""


def test_extract_requirements_splits_bullets():
    requirements = extract_requirements(SAMPLE_JD)
    assert len(requirements) >= 5
    assert any("FastAPI" in r.requirement_text for r in requirements)
    assert all(r.requirement_id.startswith("req-") for r in requirements)


def test_extract_requirements_categorizes():
    requirements = extract_requirements(SAMPLE_JD)
    nice = [r for r in requirements if r.category == RequirementCategory.NICE_TO_HAVE]
    must = [r for r in requirements if r.category == RequirementCategory.MUST_HAVE]
    assert nice, "expected at least one nice-to-have requirement"
    assert must, "expected at least one must-have requirement"


def test_extract_requirements_single_sentence_fallback():
    requirements = extract_requirements("Proficiency in Python is required.")
    assert len(requirements) == 1
    assert "Python" in requirements[0].requirement_text
