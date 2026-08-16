"""FastAPI application entry point for the AI Placement Readiness Analyzer."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

app = FastAPI(
    title="AI Placement Readiness Analyzer",
    description="Resume-to-JD grounded gap analysis & interview preparation (BRD v1.0)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict:
    return {"service": "AI Placement Readiness Analyzer", "docs": "/docs"}
