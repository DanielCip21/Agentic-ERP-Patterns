"""Live AI agent backed by real Azure AI service calls."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.connectors.azure_ai import AzureAIConfig, AzureAIConnector

_TOOLS = [
    {
        "name": "chat_complete",
        "description": "Chat with Azure OpenAI to generate a completion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "messages": {
                    "type": "array",
                    "description": "Array of message objects with role and content fields.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["role", "content"],
                    },
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens to generate (default 1024).",
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature (default 0.0).",
                },
            },
            "required": ["messages"],
        },
    },
    {
        "name": "embed_text",
        "description": "Get a vector embedding for a single string.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to embed."},
            },
            "required": ["text"],
        },
    },
    {
        "name": "analyze_document",
        "description": "Analyze a document with Azure Document Intelligence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_url": {
                    "type": "string",
                    "description": "Publicly accessible URL of the document to analyze.",
                },
                "model_id": {
                    "type": "string",
                    "description": "Document Intelligence model ID (default prebuilt-invoice).",
                },
            },
            "required": ["document_url"],
        },
    },
    {
        "name": "search_index",
        "description": "Semantic or keyword search over an Azure AI Search index.",
        "input_schema": {
            "type": "object",
            "properties": {
                "index_name": {
                    "type": "string",
                    "description": "Name of the AI Search index to query.",
                },
                "query": {"type": "string", "description": "Search query string."},
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default 5).",
                },
                "query_type": {
                    "type": "string",
                    "description": "Query type: semantic or simple (default semantic).",
                },
            },
            "required": ["index_name", "query"],
        },
    },
    {
        "name": "upload_documents",
        "description": "Batch upload documents to an Azure AI Search index.",
        "input_schema": {
            "type": "object",
            "properties": {
                "index_name": {
                    "type": "string",
                    "description": "Name of the AI Search index to upload to.",
                },
                "documents": {
                    "type": "array",
                    "description": "Array of document objects to upload.",
                    "items": {"type": "object"},
                },
            },
            "required": ["index_name", "documents"],
        },
    },
]

_SYSTEM_PROMPT = (
    "You are an Azure AI Agent with access to Azure OpenAI, Document Intelligence, and AI Search. "
    "Analyze documents with analyze_document (supports invoices, receipts, contracts), "
    "search knowledge bases with search_index, generate completions with chat_complete, "
    "and build embeddings with embed_text. "
    "Always cite the document or search result that informs your answer."
)


class AzureAIAgent(BaseERPAgent):
    """AI services agent wired to live Azure OpenAI, Document Intelligence, and AI Search.

    Usage::

        from agentic_erp.ai.azure_ai_agent import AzureAIAgent
        from agentic_erp.connectors.azure_ai import AzureAIConfig

        agent = AzureAIAgent(
            config=AzureAIConfig(
                endpoint="https://myresource.openai.azure.com",
                api_key="your-api-key",
                deployment_name="gpt-4o",
                search_endpoint="https://mysearch.search.windows.net",
                search_api_key="your-search-key",
            )
        )
        result = agent.run("Analyze the invoice at https://example.com/invoice.pdf and extract the total amount.")
        print(result)
    """

    def __init__(self, config: AzureAIConfig, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)
        self._ai = AzureAIConnector(config)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "chat_complete":
                return self._ai.chat_complete(
                    inputs["messages"],
                    max_tokens=inputs.get("max_tokens", 1024),
                    temperature=inputs.get("temperature", 0.0),
                )
            case "embed_text":
                return self._ai.embed_text(inputs["text"])
            case "analyze_document":
                return self._ai.analyze_document(
                    inputs["document_url"],
                    model_id=inputs.get("model_id", "prebuilt-invoice"),
                )
            case "search_index":
                try:
                    return self._ai.search_index(
                        inputs["index_name"],
                        inputs["query"],
                        top_k=inputs.get("top_k", 5),
                        query_type=inputs.get("query_type", "semantic"),
                    )
                except ValueError as e:
                    return {"error": str(e)}
            case "upload_documents":
                return self._ai.upload_documents(
                    inputs["index_name"],
                    inputs["documents"],
                )
            case _:
                return {"error": f"Unknown tool: {name}"}
