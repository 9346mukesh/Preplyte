# AI Placement Readiness Analyzer

Resume-to-JD **grounded** gap analysis & interview preparation system.

A Retrieval-Augmented Generation (RAG) web app that compares a candidate's
resume against a target job description, classifies each JD requirement as
**Present / Partial / Missing**, cites the resume excerpt behind every claim —
and explicitly abstains ("insufficient evidence") when there isn't enough
support, instead of hallucinating.

> Spec: [`docs/BRD.md`](docs/BRD.md) — Business Requirements Document v1.0
> (source: `docs/AI_Placement_Readiness_Analyzer_BRD.docx`)

## Features (per BRD)

- PDF/DOCX resume upload with **section-aware extraction** (skills, experience, projects, education)
- JD paste/upload parsed into structured requirements (must-have / nice-to-have)
- Embeddings + vector retrieval (top-k, similarity threshold, keyword/BM25 fallback)
- **Grounded classification** with cited evidence + verification pass
- Interview question generation tailored to JD and gaps
- Structured report with PDF/JSON export (planned)
- Dockerized, swappable embedding model / vector store

## Tech stack

| Layer       | Technology                                                     |
| ----------- | -------------------------------------------------------------- |
| Frontend    | React + Vite (JavaScript)                                     |
| Backend     | FastAPI (Python)                                               |
| LLM         | Groq – Llama 3.3 70B via LangChain                             |
| Embeddings  | HuggingFace sentence-transformers (bge-small-en-v1.5)          |
| Vector store| FAISS (local), pgvector/Pinecone as scale-out option           |
| Parsing     | pdfplumber, python-docx                                        |
| Deployment  | Docker / Docker Compose                                        |

## Repository layout

```
.
├── backend/                # FastAPI app
│   ├── app/
│   │   ├── api/            # HTTP routes (/api/analyze, /api/health)
│   │   ├── services/
│   │   │   ├── ingestion/  # ingest_resume: PDF/DOCX → section-tagged chunks (Day 1-2)
│   │   │   ├── jd_extractor.py   # structured JD requirements   (Day 2)
│   │   │   ├── embeddings.py     # embedding model wrapper      (Day 3)
│   │   │   ├── vectorstore.py    # FAISS abstraction            (Day 3)
│   │   │   ├── retrieval.py      # top-k + threshold + BM25     (Day 3)
│   │   │   ├── analyzer.py       # grounded classification      (Day 4)
│   │   │   ├── questions.py      # interview questions          (Day 5)
│   │   │   └── pipeline.py       # orchestrator (BRD §11)
│   │   ├── config.py       # env-driven settings (swappable components)
│   │   └── schemas.py      # data models (BRD §10)
│   └── tests/
├── frontend/               # React + Vite app
│   └── src/
│       ├── api/client.js   # client for /api/analyze
│       └── App.jsx         # upload → paste JD → report workflow
├── docs/                   # BRD (markdown + original docx)
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Quickstart (Docker)

```bash
cp .env.example .env        # add your GROQ_API_KEY
docker compose up --build
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/docs
```

## Local development

Backend:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173 (proxies /api -> :8000)
```

## Tests

```bash
cd backend && pytest -q
cd frontend && npm run build
```

## 1-Week build plan

| Day | Milestone (BRD mapping)                    | Push goal                                |
| --- | ------------------------------------------ | ---------------------------------------- |
| 1   | Repo setup, scaffold, ingestion start      | Project skeleton + working tests         |
| 2   | Ingestion complete: parsing + chunking     | PDF/DOCX → section-tagged chunks         |
| 3   | Retrieval: embeddings, FAISS, threshold    | End-to-end retrieval pipeline            |
| 4   | Grounded analysis + verification pass      | Evidence-backed gap report               |
| 5   | Interview questions + report assembly      | Full Report API response                 |
| 6   | React UI wiring + export                   | Live end-to-end demo in browser          |
| 7   | Docker deploy, accuracy checks, README     | `docker compose up` demo + final push    |

## Privacy (BRD NFR)

Resume and JD content are **not persisted** by default; everything lives in
memory for the active session. Set `PERSIST_SESSION_DATA=true` to opt in.

## License

Portfolio / academic project — see author details in [`docs/BRD.md`](docs/BRD.md).
