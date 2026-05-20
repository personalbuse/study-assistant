import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import settings
from app.services.embeddings import generate_embedding


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.embedding_dim = None
        self._ensure_collection()

    def _get_embedding_dim(self) -> int:
        if self.embedding_dim is None:
            try:
                test = generate_embedding("test")
                self.embedding_dim = len(test)
            except Exception:
                self.embedding_dim = 384
        return self.embedding_dim

    def _ensure_collection(self):
        dim = self._get_embedding_dim()
        collections = self.client.get_collections().collections
        exists = any(c.name == settings.collection_name for c in collections)

        if exists:
            info = self.client.get_collection(settings.collection_name)
            if info.config.params.vectors.size != dim:
                self.client.delete_collection(settings.collection_name)
                exists = False

        if not exists:
            self.client.create_collection(
                collection_name=settings.collection_name,
                vectors_config=models.VectorParams(
                    size=dim,
                    distance=models.Distance.COSINE,
                ),
            )

    def store_chunks(self, chunks: list, document_id: int):
        points = []
        for i, chunk in enumerate(chunks):
            vector = generate_embedding(chunk["text"])
            point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "document_id": document_id,
                    "filename": chunk["filename"],
                    "chunk_number": chunk["chunk_number"],
                    "page_number": chunk.get("page_number", 0),
                    "text": chunk["text"],
                },
            )
            points.append(point)

        self.client.upsert(
            collection_name=settings.collection_name,
            points=points,
        )

    def search(self, query: str, top_k: int = None) -> list:
        if top_k is None:
            top_k = settings.retrieval_top_k
        query_vector = generate_embedding(query)
        results = self.client.search(
            collection_name=settings.collection_name,
            query_vector=query_vector,
            limit=top_k,
        )
        return [
            {
                "text": hit.payload["text"],
                "filename": hit.payload["filename"],
                "page": hit.payload["page_number"],
                "score": hit.score,
            }
            for hit in results
        ]

    def delete_document_chunks(self, document_id: int):
        from qdrant_client.http import models as qmodels

        self.client.delete(
            collection_name=settings.collection_name,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )

    def delete_all(self):
        self.client.delete_collection(settings.collection_name)
        self.embedding_dim = None
        self._ensure_collection()


vector_store = VectorStore()
