# BUSINESS REQUIREMENTS DOCUMENT

## AI Placement Readiness Analyzer

**Resume-to-JD Grounded Gap Analysis & Interview Preparation System**

- **Prepared by:** Musturu Mukesh Kumar Reddy — GITAM University, Bengaluru, Final Year, Computer Science & Engineering
- **Contact:** mukeshredddy0109@gmail.com · github.com/9346mukesh
- **Document Version:** 1.0
- **Date:** August 12, 2026
- **Status:** Draft for Development

---

## Document Control

| Field | Value |
| --- | --- |
| Document Title | Business Requirements Document – AI Placement Readiness Analyzer |
| Version | 1.0 |
| Author | Musturu Mukesh Kumar Reddy |
| Date | August 12, 2026 |
| Status | Draft for Development |
| Classification | Portfolio / Academic Project |

---

## 1. Executive Summary

The AI Placement Readiness Analyzer is a Retrieval-Augmented Generation (RAG)
web application that automates the comparison of a candidate's resume against a
target job description (JD). It identifies skill gaps, classifies each JD
requirement as **Present, Partial, or Missing**, and generates tailored
interview preparation questions.

The system is built for final-year engineering students and active job seekers
who currently perform resume-to-JD comparison manually — a process that is slow,
inconsistent, and difficult to scale. The central technical differentiator of
this project is **grounding**: every claim the system makes about a matched or
partially matched skill must be traceable to a specific excerpt retrieved from
the candidate's resume. Where evidence is insufficient, the system is designed
to explicitly abstain rather than guess, directly addressing the hallucination
problem common in generic AI resume tools.

## 2. Business Problem Statement

Students and job seekers currently face the following challenges when preparing
applications for specific roles:

- Manually cross-referencing a resume against a JD is time-consuming (typically
  20–30 minutes per application) and inconsistent across attempts.
- Feedback from career counselors, seniors, or placement cells is valuable but
  not scalable to every student and every application.
- Generic resume-scoring tools (e.g., keyword-density checkers) do not tie their
  recommendations to the specific requirements of a given JD.
- Existing AI-based resume tools frequently hallucinate skills the candidate
  does not have, or provide generic advice that is not grounded in the resume's
  actual content — eroding user trust.

## 3. Business Objectives

| ID | Objective | Target |
| --- | --- | --- |
| BO-1 | Reduce time to perform a resume-JD skill gap assessment | From ~30 minutes (manual) to under 2 minutes (automated) |
| BO-2 | Ensure all reported skill matches are evidence-based | 100% of "Present/Partial" claims traceable to a cited resume excerpt in evaluation set |
| BO-3 | Support interview preparation | Generate a minimum of 5 role-specific interview questions per analysis |
| BO-4 | Provide actionable, complete gap classification | ≥ 90% of extracted JD requirements classified as Present / Partial / Missing |

## 4. Project Scope

### 4.1 In Scope (Version 1)

- Resume upload and parsing (PDF / DOCX) with section-aware text extraction.
- JD input via paste or file upload, parsed into structured requirements
  (must-have, nice-to-have, experience level).
- Embedding generation and vector storage for resume content and JD requirements.
- Per-requirement grounded retrieval and gap classification with evidence citation.
- Interview question generation tailored to the JD and identified gaps.
- Single-session web-based analysis workflow (upload → paste JD → view report).

### 4.2 Out of Scope (Version 1)

- Multi-resume comparison, ranking, or applicant tracking system (ATS) integration.
- Real-time job board scraping or automated JD sourcing.
- Automated resume rewriting or in-place editing.
- Multi-language support (English only in V1).
- Persistent user accounts / authentication (V1 assumes single active session).
- Native mobile application.

## 5. Stakeholders

| Role | Stakeholder | Interest / Involvement |
| --- | --- | --- |
| Product Owner / Developer | Musturu Mukesh Kumar Reddy | End-to-end design, build, and delivery; portfolio and interview asset |
| End User | Final-year CS / engineering students, active job seekers | Primary consumers of the resume-JD gap analysis and interview prep output |
| Technical Reviewer | Recruiters, interviewers, technical panels | Evaluate technical depth, RAG grounding rigor, and system design decisions |
| Academic Mentor | Faculty / mentor (where applicable) | Guidance on documentation quality and evaluation rigor |

## 6. Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-01 | System shall accept PDF/DOCX resume upload and extract text while preserving section boundaries (skills, experience, projects, education). | Must |
| FR-02 | System shall accept pasted or uploaded JD text and parse it into structured requirements (must-have skills, nice-to-have skills, experience years). | Must |
| FR-03 | System shall generate vector embeddings for resume chunks and JD requirements using a configured embedding model. | Must |
| FR-04 | System shall store resume embeddings in a vector database and retrieve the top-k most relevant chunks per JD requirement. | Must |
| FR-05 | System shall classify each JD requirement as Present, Partial, or Missing with cited evidence, or explicitly state "insufficient evidence." | Must |
| FR-06 | System shall not output a Present or Partial classification without an associated evidence citation traceable to a resume chunk. | Must |
| FR-07 | System shall apply a minimum similarity threshold below which retrieval is treated as no match, with optional keyword/BM25 fallback for exact technical terms. | Should |
| FR-08 | System shall generate a minimum of 5 tailored interview questions based on the JD and identified gaps. | Must |
| FR-09 | System shall present a structured report (matched skills, gap list, interview questions) via the web UI. | Must |
| FR-10 | System shall allow exporting the analysis report as PDF or JSON. | Could |

## 7. Non-Functional Requirements

| Category | Requirement |
| --- | --- |
| Performance | End-to-end analysis for a standard 1–2 page resume should complete in under 15 seconds. |
| Reliability | System should degrade gracefully on parse failures or malformed JD/resume input, returning a clear error rather than a silent wrong answer. |
| Scalability | System should reliably handle resumes up to ~5 pages and JDs up to ~1,500 words. |
| Usability | Workflow should be completable in a single linear flow: upload resume → paste JD → view report. |
| Security / Privacy | Resume and JD content should not be persisted beyond the active session unless the user explicitly opts in. |
| Maintainability | Retrieval and generation components should be modular so the embedding model or vector store can be swapped independently. |
| Portability | System should be containerized (Docker) for consistent local and deployed environments. |
| Observability | System should log per-requirement similarity scores to support debugging of retrieval quality. |

## 8. User Stories

| ID | User Story |
| --- | --- |
| US-1 | As a job seeker, I want to upload my resume and a JD so that I can see which required skills I'm missing, so I can prioritize what to learn before applying. |
| US-2 | As a job seeker, I want each identified gap to reference the specific JD requirement it maps to, so I trust the analysis is accurate and not generic. |
| US-3 | As a job seeker, I want the system to tell me when it isn't confident rather than guess, so I don't get misleading feedback. |
| US-4 | As a job seeker, I want tailored interview questions generated from the JD and my gaps, so I can prepare more effectively. |
| US-5 | As a job seeker, I want to see exactly which line of my resume supports a "matched skill" claim, so I can verify accuracy myself. |

## 9. System Architecture Overview

End-to-end data flow: resume and JD ingestion → grounded retrieval → LLM
analysis with a verification pass → final report generation.

```
Resume (PDF/DOCX) ──► Section-aware extraction ──► Chunking ──► Embeddings ──► Vector Store
                                                                                ▲
JD (paste/upload) ─► Structured requirements ──► Embeddings ────────────────────┘
                                                                                │ top-k retrieval
                                                    ┌───────────────────────────┘
                                                    ▼
                                     LLM: grounded classification (Present/Partial/Missing)
                                                    │ evidence citation
                                                    ▼
                                     Verification pass ──► Interview questions ──► Report (web UI)
```

## 10. Data Requirements

| Entity | Key Attributes |
| --- | --- |
| Resume Chunk | chunk_id, source_section (skills/experience/projects/education), raw_text, embedding_vector |
| JD Requirement | requirement_id, requirement_text, category (must-have/nice-to-have), embedding_vector |
| Retrieval Result | requirement_id, retrieved_chunk_ids, similarity_scores, threshold_pass (boolean) |
| Analysis Result | requirement_id, classification (Present/Partial/Missing), evidence_citation, confidence_note |
| Interview Question | question_id, related_requirement_id or gap_id, question_text, question_type (technical/behavioral) |

## 11. Process Workflow (End-to-End User Journey)

1. User uploads a resume (PDF or DOCX) via the web UI.
2. User pastes or uploads the target job description.
3. System extracts and section-tags resume text; system extracts structured
   requirements from the JD.
4. System generates embeddings for resume chunks and JD requirements and stores
   resume embeddings in the vector store.
5. For each JD requirement, the system retrieves the top-k most similar resume
   chunks, applying a similarity threshold.
6. The LLM classifies each requirement as Present, Partial, or Missing, citing
   the specific resume evidence used — or states insufficient evidence.
7. A verification pass re-checks each "Present/Partial" claim against its cited
   evidence before finalizing the report.
8. The system generates tailored interview questions based on the JD and the
   identified gaps.
9. The user reviews the structured report (matches, gaps, interview questions)
   and may export it.

## 12. Assumptions & Constraints

### 12.1 Assumptions

- The user provides the job description in English text (not an image or scanned document).
- The resume is primarily text-based rather than a scanned image (OCR is out of scope for V1).
- A single JD is analyzed at a time in V1; batch analysis is a future enhancement.
- Third-party LLM and embedding APIs (e.g., Groq) are assumed to be available with reasonable uptime.

### 12.2 Constraints

- Extraction accuracy cannot be guaranteed for unusually formatted resumes
  (e.g., heavy graphics, tables, multi-column layouts).
- Grounding reduces but does not fully eliminate the possibility of model error;
  the verification pass is a mitigation, not a guarantee.
- Vector database and LLM API usage may be constrained by free-tier rate limits and cost.
- Embedding model context length limits the maximum chunk size used during retrieval.

## 13. Risks & Mitigation

| ID | Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- | --- |
| R-1 | Hallucinated skill match despite grounding | High | Medium | Mandatory evidence field; verification pass; abstain below similarity threshold |
| R-2 | Poor resume parsing on unusual formatting | Medium | Medium | Section-aware chunking with fallback plain-text parsing; manual QA on sample resumes |
| R-3 | JD requirement extraction misses nuanced requirements | Medium | Medium | Structured JSON extraction prompt with few-shot examples; allow manual requirement edit |
| R-4 | Semantic retrieval misses exact keyword matches (tool/tech names) | Medium | Medium | Hybrid retrieval: semantic search plus keyword/BM25 fallback |
| R-5 | LLM API latency or cost overruns | Low | Medium | Cache embeddings, batch calls, use a smaller/faster model for latency-sensitive steps |
| R-6 | Resume data privacy concerns | Medium | Low | No persistent storage by default; clear data-retention notice shown in the UI |

## 14. Success Metrics / KPIs

| Metric | Definition | Target |
| --- | --- | --- |
| Grounding accuracy | % of Present/Partial claims with a valid, verifiable evidence citation | 100% on evaluation set |
| Retrieval precision | Manual spot-check precision@k across a sample set of resumes and JDs | > 85% |
| Analysis latency | End-to-end time from submission to report for a standard resume | < 15 seconds |
| Requirement coverage | % of JD requirements successfully classified vs. unparseable | > 90% |
| Perceived usefulness | Qualitative feedback from peer testers | Positive feedback from ≥ 5 peer testers |

## 15. Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | React |
| Backend / API | FastAPI (Python) |
| LLM | Groq – Llama 3.3 70B, via LangChain |
| Embeddings | HuggingFace sentence-transformers (e.g., bge-small-en-v1.5 / all-MiniLM-L6-v2) |
| Vector Store | FAISS (local) with pgvector / Pinecone as a cloud-scale option |
| Document Parsing | pdfplumber / PyPDF2, python-docx |
| Deployment | Docker / Docker Compose |
| Version Control | Git / GitHub |

## 16. Project Timeline & Milestones

Proposed 4-week solo development plan (compressed to 1 week in this repo —
see the README build plan):

| Phase | Focus | Key Deliverable |
| --- | --- | --- |
| Week 1 | Requirements finalization; resume/JD parsing pipeline; section-aware chunking | Working ingestion module |
| Week 2 | Embedding pipeline, vector store integration, structured JD requirement extraction | End-to-end retrieval pipeline |
| Week 3 | Grounded gap-analysis LLM pipeline; hallucination guardrails (evidence citation, verification pass, similarity threshold) | Evidence-backed gap report |
| Week 4 | Interview question generation, React UI integration, accuracy testing, Docker deployment, documentation | Deployed demo + this BRD |

## 17. Glossary

| Term | Definition |
| --- | --- |
| RAG (Retrieval-Augmented Generation) | A technique combining vector-based retrieval of relevant context with LLM generation to ground responses in factual source material. |
| Embedding | A numerical vector representation of text capturing semantic meaning, used for similarity search. |
| Vector Database | A database (e.g., FAISS, pgvector, Pinecone) optimized for storing and querying high-dimensional embedding vectors. |
| Grounding | Constraining an LLM's output to be based only on retrieved or provided evidence rather than the model's general knowledge, to prevent hallucination. |
| Hallucination | A generated output that states something false or unsupported by the given source, presented as if factual. |
| Chunking | Splitting a document into smaller segments for embedding and retrieval. |
| Similarity Threshold | A minimum similarity score below which a retrieved chunk is treated as not relevant. |
| BM25 | A classic keyword-based ranking algorithm used as a complementary/fallback retrieval method to semantic search. |
