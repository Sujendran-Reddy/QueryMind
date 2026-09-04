from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.database import (
    create_collection,
    get_collections,
    initialise_database,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialise_database()
    yield


app = FastAPI(
    title="QueryMind API",
    description="Document intelligence and RAG API",
    version="0.1.0",
    lifespan=lifespan,
)


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


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
        raise HTTPException(
            status_code=400,
            detail="Collection name cannot be empty",
        )

    return create_collection(name)