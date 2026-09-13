"""IP-SAKTI Sahayak FastAPI Application Entry Point."""

import sys
from pathlib import Path

# Ensure both repo root and backend directory are in sys.path
_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent
_repo_root = _backend_dir.parent
for _p in (str(_repo_root), str(_backend_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.classify import router as classify_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.investigate import router as investigate_router
from backend.app.api.routes.query import router as query_router
from backend.app.config import settings


from backend.app.ingestion.chunker import LegalDocumentChunker
from backend.app.ingestion.sample_seed import SAMPLE_DOCUMENTS
from backend.app.retrieval.service import retrieval_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup log
    print(f"IP-SAKTI Sahayak Backend starting up [env={settings.app_env}]...")
    retriever = retrieval_service.retriever
    if not retriever._in_memory_corpus:
        chunker = LegalDocumentChunker()
        for doc in SAMPLE_DOCUMENTS:
            chunks = chunker.chunk_document(doc)
            retriever.bm25.add_chunks(chunks)
            for c in chunks:
                retriever.register_in_memory_chunk(c.model_dump())
        print(f"Loaded {len(retriever._in_memory_corpus)} statutory chunks into in-memory retriever.")
    yield
    print("IP-SAKTI Sahayak Backend shutting down...")


app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="RAG-based AI assistant for Ayurveda IP/regulatory guidance (Hackathon MVP)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def normalize_slashes(request, call_next):
    """Normalize duplicate slashes in request paths (e.g., //health -> /health)."""
    if "//" in request.scope.get("path", ""):
        import re
        request.scope["path"] = re.sub(r"/+", "/", request.scope["path"])
    return await call_next(request)

# Include API routers
app.include_router(classify_router)
app.include_router(health_router)
app.include_router(investigate_router)
app.include_router(query_router)


@app.get("/")
async def root():
    return {
        "service": "IP-SAKTI Sahayak API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "classify": "/classify",
            "query": "/query",
            "investigate": "/investigate",
            "health": "/health",
        },
    }
