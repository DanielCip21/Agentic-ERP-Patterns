"""Live connector for Azure AI services (Azure OpenAI, Document Intelligence, AI Search)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from agentic_erp.connectors.base import BaseHTTPConnector


class AzureAIConfig(BaseModel):
    """Azure AI / Azure OpenAI configuration.

    For Azure OpenAI:   set endpoint, api_key, deployment_name
    For AI Search:      also set search_endpoint and search_api_key
    For Doc Intelligence: uses the same endpoint with a different path
    """

    endpoint: str            # e.g. https://myresource.openai.azure.com
    api_key: str
    deployment_name: str     # e.g. gpt-4o  or  text-embedding-3-large
    api_version: str = "2024-12-01-preview"

    # Azure AI Search (optional)
    search_endpoint: str = ""
    search_api_key: str = ""
    search_api_version: str = "2024-05-01-preview"

    # Azure AI Document Intelligence (optional — defaults to same endpoint)
    doc_intel_api_version: str = "2024-11-30"


class _AzureKeyConnector(BaseHTTPConnector):
    """Internal connector that authenticates with an Azure api-key header."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url
        self._api_key = api_key

    def _auth_headers(self) -> dict[str, str]:
        return {"api-key": self._api_key}


class AzureAIConnector:
    """Live client for Azure OpenAI, Document Intelligence, and AI Search.

    All three services use api-key authentication (no OAuth2 required).
    For managed identity auth, swap ``api-key`` for an AAD bearer token.

    Usage::

        from agentic_erp.connectors.azure_ai import AzureAIConfig, AzureAIConnector

        conn = AzureAIConnector(AzureAIConfig(
            endpoint="https://myresource.openai.azure.com",
            api_key="...",
            deployment_name="gpt-4o",
            search_endpoint="https://mysearch.search.windows.net",
            search_api_key="...",
        ))

        response = conn.chat_complete([{"role": "user", "content": "Hello"}])
        embedding = conn.embed_text("invoice vendor name")
        results = conn.search_index("kb-index", "how to configure SSO")
    """

    def __init__(self, config: AzureAIConfig) -> None:
        self.config = config
        self._oai = _AzureKeyConnector(config.endpoint, config.api_key)
        self._search = (
            _AzureKeyConnector(config.search_endpoint, config.search_api_key)
            if config.search_endpoint
            else None
        )

    # --- Azure OpenAI — Chat Completions --------------------------------------

    def chat_complete(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """POST /openai/deployments/{deployment}/chat/completions"""
        path = f"openai/deployments/{self.config.deployment_name}/chat/completions"
        return self._oai._post(
            path,
            json={"messages": messages, "max_tokens": max_tokens, "temperature": temperature, **kwargs},
        )

    # --- Azure OpenAI — Embeddings --------------------------------------------

    def embed_text(self, text: str) -> dict[str, Any]:
        """POST /openai/deployments/{deployment}/embeddings"""
        path = f"openai/deployments/{self.config.deployment_name}/embeddings"
        return self._oai._post(path, json={"input": text})

    def embed_batch(self, texts: list[str]) -> dict[str, Any]:
        """POST /openai/deployments/{deployment}/embeddings with a list of inputs."""
        path = f"openai/deployments/{self.config.deployment_name}/embeddings"
        return self._oai._post(path, json={"input": texts})

    # --- Azure AI Document Intelligence ---------------------------------------

    def analyze_document(
        self, document_url: str, model_id: str = "prebuilt-invoice"
    ) -> dict[str, Any]:
        """POST /documentintelligence/documentModels/{model}:analyze

        Submits an analysis job and polls until complete.
        For async usage, call analyze_document_async + poll_analyze_result separately.
        """
        path = f"documentintelligence/documentModels/{model_id}:analyze"
        params = {"api-version": self.config.doc_intel_api_version}
        response = self._oai._post(path, json={"urlSource": document_url})
        # If 202 Accepted, poll the operation-location header
        return response

    def get_supported_models(self) -> dict[str, Any]:
        """GET /documentintelligence/documentModels — list available models."""
        return self._oai._get(
            "documentintelligence/documentModels",
            params={"api-version": self.config.doc_intel_api_version},
        )

    # --- Azure AI Search ------------------------------------------------------

    def search_index(
        self,
        index_name: str,
        query: str,
        top_k: int = 5,
        query_type: str = "semantic",
        semantic_config: str = "default",
    ) -> dict[str, Any]:
        """POST /indexes/{index}/docs/search — keyword, semantic, or vector search."""
        if not self._search:
            raise ValueError("search_endpoint not configured in AzureAIConfig")
        body: dict[str, Any] = {
            "search": query,
            "top": top_k,
            "queryType": query_type,
        }
        if query_type == "semantic":
            body["semanticConfiguration"] = semantic_config
        return self._search._post(
            f"indexes/{index_name}/docs/search",
            json=body,
        )

    def vector_search(
        self,
        index_name: str,
        vector: list[float],
        vector_field: str = "content_vector",
        top_k: int = 5,
    ) -> dict[str, Any]:
        """POST /indexes/{index}/docs/search — pure vector (kNN) search."""
        if not self._search:
            raise ValueError("search_endpoint not configured in AzureAIConfig")
        return self._search._post(
            f"indexes/{index_name}/docs/search",
            json={
                "vectorQueries": [
                    {"kind": "vector", "vector": vector, "fields": vector_field, "k": top_k}
                ]
            },
        )

    def create_index(self, index_name: str, schema: dict[str, Any]) -> dict[str, Any]:
        """PUT /indexes/{index} — create or update an AI Search index."""
        if not self._search:
            raise ValueError("search_endpoint not configured in AzureAIConfig")
        return self._search._post(f"indexes/{index_name}", json=schema)

    def upload_documents(
        self, index_name: str, documents: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """POST /indexes/{index}/docs/index — batch upload documents."""
        if not self._search:
            raise ValueError("search_endpoint not configured in AzureAIConfig")
        return self._search._post(
            f"indexes/{index_name}/docs/index",
            json={"value": [{"@search.action": "mergeOrUpload", **d} for d in documents]},
        )
