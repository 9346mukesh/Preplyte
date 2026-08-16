"""API routes (BRD FR-09, workflow section 11)."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..schemas import Report
from ..services.ingestion.parsers import ParseError
from ..services.pipeline import run_analysis

router = APIRouter(prefix="/api", tags=["analysis"])

SUPPORTED_RESUME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "ai-placement-readiness-analyzer"}


@router.post("/analyze", response_model=Report)
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
) -> Report:
    """Run resume-to-JD grounded gap analysis (BRD workflow step 1-8)."""
    if resume.content_type not in SUPPORTED_RESUME_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only PDF or DOCX resumes are supported (FR-01)",
        )

    content = await resume.read()
    try:
        return run_analysis(
            content=content,
            filename=resume.filename or "resume",
            jd_text=job_description,
        )
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
