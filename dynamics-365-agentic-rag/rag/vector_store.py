from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import settings


class VectorStore:
    """ChromaDB-backed persistent vector store for CRM intelligence."""

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        return self._client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        col = self.get_or_create_collection(collection_name)
        col.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int | None = None,
    ) -> list[dict]:
        col = self.get_or_create_collection(collection_name)
        if col.count() == 0:
            return []
        results = col.query(
            query_texts=[query_text],
            n_results=min(n_results or settings.rag_top_k, col.count()),
            include=["documents", "metadatas", "distances"],
        )
        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({"document": doc, "metadata": meta, "similarity": round(1 - dist, 4)})
        return output

    def collection_count(self, collection_name: str) -> int:
        try:
            return self.get_or_create_collection(collection_name).count()
        except Exception:
            return 0


vector_store = VectorStore()
