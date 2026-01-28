"""
RAG-Based Question Answering System
Main FastAPI application with document upload and query endpoints
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List

import uvicorn
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator

from src.answer_generator import AnswerGenerator
from src.document_processor import DocumentProcessor
from src.embedding_service import EmbeddingService
from src.metrics_tracker import MetricsTracker
from src.rate_limiter import RateLimiter
from src.retrieval_service import RetrievalService
from src.vector_store import VectorStore

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# -------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------
app = FastAPI(
    title="RAG Question Answering System",
    version="1.0.0",
)

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Static frontend (optional)
# -------------------------------------------------------------------
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def serve_frontend():
        index_path = STATIC_DIR / "index.html"
        if not index_path.exists():
            raise HTTPException(500, "index.html not found")
        return FileResponse(index_path)

# -------------------------------------------------------------------
# Services (single initialization)
# -------------------------------------------------------------------
document_processor = DocumentProcessor()
embedding_service = EmbeddingService()
vector_store = VectorStore()
retrieval_service = RetrievalService(vector_store, embedding_service)
answer_generator = AnswerGenerator()
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
metrics_tracker = MetricsTracker()

# -------------------------------------------------------------------
# Pydantic Models
# -------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)

    @validator("question")
    def clean_question(cls, v):
        return v.strip()


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    confidence_score: float
    retrieval_time_ms: float
    generation_time_ms: float
    chunks_retrieved: int


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    documents_indexed: int
    total_chunks: int


# -------------------------------------------------------------------
# Rate limiting dependency
# -------------------------------------------------------------------
async def check_rate_limit(user_id: str = "anonymous"):
    if not rate_limiter.allow_request(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return user_id


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health():
    stats = vector_store.get_stats()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        documents_indexed=stats["documents"],
        total_chunks=stats["chunks"],
    )


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(check_rate_limit),
):
    ext = "." + file.filename.split(".")[-1].lower()
    if ext not in [".pdf", ".txt"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()
    document_id = f"doc_{int(time.time())}_{file.filename}"

    background_tasks.add_task(
        process_document,
        document_id,
        file.filename,
        content,
        ext,
    )

    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        status="processing",
        message="Document is being processed in the background",
    )


async def process_document(document_id: str, filename: str, content: bytes, ext: str):
    text = document_processor.extract_text(content, ext)
    chunks = document_processor.chunk_text(text, document_id, filename)

    if not chunks:
        logger.warning(f"No chunks created for {document_id}")
        return

    embeddings = embedding_service.embed_chunks([c["text"] for c in chunks])
    vector_store.add_documents(chunks, embeddings, document_id)

    logger.info(f"Indexed document {document_id} with {len(chunks)} chunks")


@app.post("/query", response_model=QueryResponse)
async def query_documents(
    req: QueryRequest,
    user_id: str = Depends(check_rate_limit),
):
    start_retrieval = time.time()
    retrieved_chunks = retrieval_service.retrieve(req.question, req.top_k)
    retrieval_time_ms = (time.time() - start_retrieval) * 1000

    if not retrieved_chunks:
        return QueryResponse(
            answer="No relevant information found.",
            sources=[],
            confidence_score=0.0,
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=0.0,
            chunks_retrieved=0,
        )

    start_generation = time.time()
    answer, confidence = answer_generator.generate_answer(
        req.question, retrieved_chunks
    )
    generation_time_ms = (time.time() - start_generation) * 1000

    sources = [
        {
            "document": c["metadata"]["filename"],
            "chunk_id": c["metadata"]["chunk_id"],
            "similarity": round(c["score"], 4),
        }
        for c in retrieved_chunks
    ]

    return QueryResponse(
        answer=answer,
        sources=sources,
        confidence_score=confidence,
        retrieval_time_ms=retrieval_time_ms,
        generation_time_ms=generation_time_ms,
        chunks_retrieved=len(retrieved_chunks),
    )


# -------------------------------------------------------------------
# Run
# -------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
