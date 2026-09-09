from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.chunking import chunk_document
from app.database import (
    collection_exists,
    create_collection,
    create_document,
    get_collections,
    get_documents,
    initialise_database,
)
from app.documents import SUPPORTED_EXTENSIONS, extract_document
from app.rag import generate_answer
from app.vector_store import get_vector_store


UPLOAD_DIRECTORY = Path("uploads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialise_database()
    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="QueryMind API",
    description="Document intelligence and RAG API",
    version="0.1.0",
    lifespan=lifespan,
)


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class SearchRequest(BaseModel):
    collection_id: str
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatRequest(BaseModel):
    collection_id: str
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "QueryMind API",
    }


@app.get("/collections")
def list_collections():
    return get_collections()


@app.post("/collections", status_code=201)
def add_collection(collection: CollectionCreate):
    name = collection.name.strip()

    if not name:
        raise HTTPException(400, "Collection name cannot be empty")

    return create_collection(name)


@app.get("/collections/{collection_id}/documents")
def list_documents(collection_id: str):
    if not collection_exists(collection_id):
        raise HTTPException(404, "Collection not found")

    return get_documents(collection_id)


@app.post("/collections/{collection_id}/documents", status_code=201)
async def upload_document(
    collection_id: str,
    file: UploadFile = File(...),
):
    if not collection_exists(collection_id):
        raise HTTPException(404, "Collection not found")

    original_name = file.filename or "document"
    extension = Path(original_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            415,
            "Supported formats are PDF, DOCX, TXT, and Markdown",
        )

    stored_path = UPLOAD_DIRECTORY / f"{uuid4()}{extension}"
    stored_path.write_bytes(await file.read())

    try:
        pages = extract_document(stored_path)
        chunks = chunk_document(pages)
        character_count = sum(len(page.text) for page in pages)

        if character_count == 0:
            raise ValueError("Document contains no extractable text")

        document = create_document(
            collection_id=collection_id,
            name=original_name,
            page_count=len(pages),
            character_count=character_count,
        )

        get_vector_store().index_chunks(
            collection_id=collection_id,
            document_id=document["id"],
            document_name=original_name,
            chunks=chunks,
        )

        return {
            **document,
            "chunk_count": len(chunks),
        }

    except Exception as error:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(422, str(error)) from error


@app.post("/search")
def search_documents(request: SearchRequest):
    if not collection_exists(request.collection_id):
        raise HTTPException(404, "Collection not found")

    results = get_vector_store().search(
        collection_id=request.collection_id,
        question=request.question,
        top_k=request.top_k,
    )

    return {
        "question": request.question,
        "results": results,
        "result_count": len(results),
    }


@app.post("/chat")
def chat_with_documents(request: ChatRequest):
    if not collection_exists(request.collection_id):
        raise HTTPException(404, "Collection not found")

    sources = get_vector_store().search(
        collection_id=request.collection_id,
        question=request.question,
        top_k=request.top_k,
    )

    try:
        answer = generate_answer(
            question=request.question,
            retrieved_chunks=sources,
        )
    except httpx.HTTPError as error:
        raise HTTPException(
            503,
            "Ollama is unavailable. Ensure it is running.",
        ) from error

    return {
        "question": request.question,
        "answer": answer,
        "sources": sources,
        "model": "qwen2.5:1.5b",
    }