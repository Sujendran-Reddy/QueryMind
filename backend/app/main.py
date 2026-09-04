from fastapi import FastAPI

app = FastAPI(
    title="QueryMind API",
    description="Document intelligence and RAG API",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "QueryMind API",
    }