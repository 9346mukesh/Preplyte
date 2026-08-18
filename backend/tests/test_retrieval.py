"""Day 3 tests: embeddings, FAISS vector store, retrieval pipeline.

Tests:
- EmbeddingService encodes texts into normalized vectors
- FAISSVectorStore add/search returns top-k results with scores
- retrieve_per_requirement wires embeddings + vector store + BM25 fallback
- Pipeline wires Day 3 stages end-to-end
"""

import numpy as np

from app.services.embeddings import EmbeddingService
from app.services.vectorstore import FAISSVectorStore, build_vector_store
from app.schemas import JDRequirement, RequirementCategory, ResumeChunk, Section
from app.services.retrieval import retrieve_per_requirement


class TestEmbeddingService:
    """Tests for FR-03: generate vector embeddings for resume chunks and JD requirements."""

    def test_encode_returns_normalized_vectors(self):
        """Embedding vectors should be L2-normalized (for cosine via inner product)."""
        service = EmbeddingService()
        vectors = service.encode(["Python developer", "FastAPI backend"])
        assert len(vectors) == 2
        assert len(vectors[0]) > 0
        # Check normalization: L2 norm should be ~1.0
        norm = np.linalg.norm(vectors[0])
        assert 0.99 <= norm <= 1.01

    def test_encode_single_text(self):
        """Encoding a single text should return a list with one vector."""
        service = EmbeddingService()
        vectors = service.encode(["React frontend"])
        assert len(vectors) == 1
        assert len(vectors[0]) == 384  # bge-small-en-v1.5 dimension


class TestFAISSVectorStore:
    """Tests for FR-04: store resume embeddings and retrieve top-k."""

    def test_add_and_search(self):
        """Adding embeddings and searching should return top-k results."""
        store = FAISSVectorStore(dimension=384)
        # Create mock normalized embeddings
        embeddings = np.random.randn(5, 384).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        ids = ["chunk:0", "chunk:1", "chunk:2", "chunk:3", "chunk:4"]
        store.add(ids, embeddings.tolist())
        assert store._index.ntotal == 5
        # Search with first embedding as query
        query = embeddings[0].tolist()
        matched_ids, scores = store.search(query, top_k=3)
        assert len(matched_ids) == 3
        assert len(scores) == 3
        # First result should be itself with score ~1.0
        assert matched_ids[0] == "chunk:0"
        assert scores[0] >= 0.99

    def test_search_empty_store(self):
        """Searching an empty store should return empty lists."""
        store = FAISSVectorStore(dimension=384)
        ids, scores = store.search([0.0] * 384, top_k=3)
        assert ids == []
        assert scores == []

    def test_top_k_limit(self):
        """Should return at most top_k results."""
        store = FAISSVectorStore(dimension=384)
        embeddings = np.random.randn(10, 384).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        ids = [f"chunk:{i}" for i in range(10)]
        store.add(ids, embeddings.tolist())
        matched_ids, scores = store.search(embeddings[0].tolist(), top_k=3)
        assert len(matched_ids) == 3


class TestRetrievePerRequirement:
    """Tests for FR-04/FR-07: retrieve top-k with threshold and BM25 fallback."""

    def test_retrieve_returns_results(self):
        """Should return a RetrievalResult per requirement."""
        chunks = [
            ResumeChunk(chunk_id="skills:0", source_section=Section.SKILLS, raw_text="Python, FastAPI, PostgreSQL"),
            ResumeChunk(chunk_id="exp:0", source_section=Section.EXPERIENCE, raw_text="Built a REST API with FastAPI"),
        ]
        requirements = [
            JDRequirement(requirement_id="req:0", requirement_text="Python developer", category=RequirementCategory.MUST_HAVE),
        ]
        embeddings = EmbeddingService()
        store = build_vector_store()
        results = retrieve_per_requirement(
            requirements=requirements,
            chunks=chunks,
            embeddings=embeddings,
            vector_store=store,
            top_k=2,
            threshold=0.3,
        )
        assert len(results) == 1
        assert results[0].requirement_id == "req:0"
        assert len(results[0].retrieved_chunk_ids) > 0

    def test_threshold_filters_irrelevant(self):
        """Below threshold should set threshold_pass=False."""
        chunks = [
            ResumeChunk(chunk_id="edu:0", source_section=Section.EDUCATION, raw_text="B.Tech CSE, GITAM University"),
        ]
        # Query is completely unrelated to education
        requirements = [
            JDRequirement(requirement_id="req:0", requirement_text="Kubernetes container orchestration expert", category=RequirementCategory.MUST_HAVE),
        ]
        embeddings = EmbeddingService()
        store = build_vector_store()
        results = retrieve_per_requirement(
            requirements=requirements,
            chunks=chunks,
            embeddings=embeddings,
            vector_store=store,
            top_k=1,
            threshold=0.8,  # high threshold
        )
        assert len(results) == 1
        # Should not pass threshold for unrelated content
        assert results[0].threshold_pass is False

    def test_bm25_fallback_catches_exact_keywords(self):
        """BM25 fallback should catch exact technical terms (BRD risk R-4)."""
        chunks = [
            ResumeChunk(chunk_id="skills:0", source_section=Section.SKILLS, raw_text="Kubernetes, Docker, Helm"),
        ]
        requirements = [
            JDRequirement(requirement_id="req:0", requirement_text="Kubernetes experience required", category=RequirementCategory.MUST_HAVE),
        ]
        embeddings = EmbeddingService()
        store = build_vector_store()
        # With keyword fallback
        results = retrieve_per_requirement(
            requirements=requirements,
            chunks=chunks,
            embeddings=embeddings,
            vector_store=store,
            top_k=1,
            threshold=0.8,
            use_keyword_fallback=True,
        )
        assert results[0].threshold_pass is True  # keyword match counts

    def test_empty_inputs(self):
        """Empty requirements or chunks should return empty list."""
        embeddings = EmbeddingService()
        store = build_vector_store()
        assert retrieve_per_requirement([], [], embeddings, store, 3, 0.45) == []
