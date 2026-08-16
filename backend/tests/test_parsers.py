from app.services.ingestion.parsers import detect_section, extract_sections
from app.schemas import Section

SAMPLE_RESUME = """John Doe
john@example.com | Bengaluru, India

SKILLS
Python, FastAPI, React, PostgreSQL

EXPERIENCE
Software Engineer Intern at Acme Corp
Built a REST API with FastAPI

PROJECTS
Resume Analyzer - RAG app comparing resumes to JDs

EDUCATION
B.Tech CSE, GITAM University, 2023-2027
"""


def test_detect_section():
    assert detect_section("SKILLS") == Section.SKILLS
    assert detect_section("Work Experience") == Section.EXPERIENCE
    assert detect_section("Projects") == Section.PROJECTS
    assert detect_section("EDUCATION") == Section.EDUCATION
    assert detect_section("John Doe") is None


def test_extract_sections_buckets_content():
    sections = extract_sections(SAMPLE_RESUME)
    assert "Python, FastAPI, React, PostgreSQL" in sections[Section.SKILLS]
    assert any("REST API with FastAPI" in line for line in sections[Section.EXPERIENCE])
    assert any("RAG app" in line for line in sections[Section.PROJECTS])
    assert any("GITAM University" in line for line in sections[Section.EDUCATION])
    # Contact header lines fall into OTHER.
    assert "john@example.com | Bengaluru, India" in sections[Section.OTHER]
