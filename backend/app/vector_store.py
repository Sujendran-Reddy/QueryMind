from functools import lru_cache
from uuid import uuid4

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

from app.chunking import TextChunk


QDRANT_COLLECTION = "querymind_chunks"
VECTOR_SIZE = 384


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(path="data/qdrant")
        self.embedding_model = TextEmbedding(
            model_name="BAAI/bge-small-en-v1.5"
        )
        self._create_collection()

    def _create_collection(self):
        if not self.client.collection_exists(QDRANT_COLLECTION):
            self.client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )

    def index_chunks(
        self,
        collection_id: str,
        document_id: str,
        document_name: str,
        chunks: list[TextChunk],
    ):
        texts = [chunk.text for chunk in chunks]
        embeddings = list(self.embedding_model.embed(texts))

        points = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = str(uuid4())

            points.append(
                models.PointStruct(
                    id=chunk_id,
                    vector=embedding.tolist(),
                    payload={
                        "chunk_id": chunk_id,
                        "collection_id": collection_id,
                        "document_id": document_id,
                        "document_name": document_name,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                    },
                )
            )

        if points:
            self.client.upsert(
                collection_name=QDRANT_COLLECTION,
                points=points,
                wait=True,
            )


@lru_cache
def get_vector_store():
    return VectorStore()