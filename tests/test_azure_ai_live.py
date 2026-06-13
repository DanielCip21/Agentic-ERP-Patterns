"""Tests for live Azure AI connector and agent — HTTP calls intercepted with respx."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
import respx

from agentic_erp.connectors.azure_ai import AzureAIConfig, AzureAIConnector
from agentic_erp.connectors.base import ConnectorError, NotFoundError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AI_BASE = "https://myresource.openai.azure.com"
AI_SEARCH_BASE = "https://mysearch.search.windows.net"
DEPLOYMENT = "gpt-4o"

CHAT_RESPONSE = {
    "choices": [
        {
            "message": {"role": "assistant", "content": "Invoice total is $1,250."},
            "finish_reason": "stop",
        }
    ],
    "usage": {"total_tokens": 42},
}

EMBED_RESPONSE = {
    "data": [{"embedding": [0.1, 0.2, 0.3], "index": 0}],
    "model": "text-embedding-3-large",
}

ANALYZE_RESPONSE = {"operationId": "op-001", "status": "running"}

SEARCH_RESPONSE = {
    "value": [
        {
            "id": "doc-1",
            "content": "Invoice terms are net-30.",
            "@search.score": 0.95,
        }
    ]
}

UPLOAD_RESPONSE = {
    "value": [
        {
            "key": "doc-1",
            "status": True,
            "errorMessage": None,
            "statusCode": 201,
        }
    ]
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config():
    return AzureAIConfig(
        endpoint=AI_BASE,
        api_key="test-key",
        deployment_name=DEPLOYMENT,
        search_endpoint=AI_SEARCH_BASE,
        search_api_key="search-key",
    )


@pytest.fixture
def connector(config):
    return AzureAIConnector(config)


# ---------------------------------------------------------------------------
# AzureAIConnector — happy path
# ---------------------------------------------------------------------------


class TestAzureAIConnectorHappyPath:
    @respx.mock
    def test_chat_complete(self, connector):
        respx.post(
            f"{AI_BASE}/openai/deployments/{DEPLOYMENT}/chat/completions"
        ).mock(return_value=httpx.Response(200, json=CHAT_RESPONSE))

        result = connector.chat_complete([{"role": "user", "content": "What is the invoice total?"}])
        assert result["choices"][0]["message"]["content"] == "Invoice total is $1,250."
        assert result["usage"]["total_tokens"] == 42

    @respx.mock
    def test_embed_text(self, connector):
        respx.post(
            f"{AI_BASE}/openai/deployments/{DEPLOYMENT}/embeddings"
        ).mock(return_value=httpx.Response(200, json=EMBED_RESPONSE))

        result = connector.embed_text("invoice vendor name")
        assert result["data"][0]["embedding"] == [0.1, 0.2, 0.3]
        assert result["model"] == "text-embedding-3-large"

    @respx.mock
    def test_embed_batch(self, connector):
        batch_response = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3], "index": 0},
                {"embedding": [0.4, 0.5, 0.6], "index": 1},
            ],
            "model": "text-embedding-3-large",
        }
        respx.post(
            f"{AI_BASE}/openai/deployments/{DEPLOYMENT}/embeddings"
        ).mock(return_value=httpx.Response(200, json=batch_response))

        result = connector.embed_batch(["invoice vendor name", "payment terms"])
        assert len(result["data"]) == 2
        assert result["data"][0]["embedding"] == [0.1, 0.2, 0.3]
        assert result["data"][1]["embedding"] == [0.4, 0.5, 0.6]

    @respx.mock
    def test_analyze_document(self, connector):
        respx.post(
            f"{AI_BASE}/documentintelligence/documentModels/prebuilt-invoice:analyze"
        ).mock(return_value=httpx.Response(202, json=ANALYZE_RESPONSE))

        result = connector.analyze_document("https://example.com/invoice.pdf")
        assert result["operationId"] == "op-001"
        assert result["status"] == "running"

    @respx.mock
    def test_analyze_document_custom_model(self, connector):
        respx.post(
            f"{AI_BASE}/documentintelligence/documentModels/prebuilt-receipt:analyze"
        ).mock(return_value=httpx.Response(202, json=ANALYZE_RESPONSE))

        result = connector.analyze_document(
            "https://example.com/receipt.pdf", model_id="prebuilt-receipt"
        )
        assert result["operationId"] == "op-001"

    @respx.mock
    def test_search_index(self, connector):
        respx.post(
            f"{AI_SEARCH_BASE}/indexes/kb-index/docs/search"
        ).mock(return_value=httpx.Response(200, json=SEARCH_RESPONSE))

        result = connector.search_index("kb-index", "invoice payment terms")
        assert result["value"][0]["id"] == "doc-1"
        assert result["value"][0]["@search.score"] == 0.95

    @respx.mock
    def test_vector_search(self, connector):
        respx.post(
            f"{AI_SEARCH_BASE}/indexes/kb-index/docs/search"
        ).mock(return_value=httpx.Response(200, json=SEARCH_RESPONSE))

        result = connector.vector_search(
            "kb-index",
            vector=[0.1, 0.2, 0.3],
            vector_field="content_vector",
            top_k=3,
        )
        assert result["value"][0]["id"] == "doc-1"

    @respx.mock
    def test_upload_documents(self, connector):
        respx.post(
            f"{AI_SEARCH_BASE}/indexes/kb-index/docs/index"
        ).mock(return_value=httpx.Response(200, json=UPLOAD_RESPONSE))

        docs = [{"id": "doc-1", "content": "Invoice terms are net-30."}]
        result = connector.upload_documents("kb-index", docs)
        assert result["value"][0]["key"] == "doc-1"
        assert result["value"][0]["status"] is True
        assert result["value"][0]["statusCode"] == 201


# ---------------------------------------------------------------------------
# AzureAIConnector — error handling
# ---------------------------------------------------------------------------


class TestAzureAIConnectorErrors:
    @respx.mock
    def test_chat_500_raises_connector_error(self, connector):
        respx.post(
            f"{AI_BASE}/openai/deployments/{DEPLOYMENT}/chat/completions"
        ).mock(return_value=httpx.Response(500, text="Internal Server Error"))

        with pytest.raises(ConnectorError) as exc_info:
            connector.chat_complete([{"role": "user", "content": "Hello"}])
        assert exc_info.value.status_code == 500

    def test_search_raises_without_endpoint(self):
        cfg = AzureAIConfig(
            endpoint=AI_BASE,
            api_key="test-key",
            deployment_name=DEPLOYMENT,
        )
        conn = AzureAIConnector(cfg)
        with pytest.raises(ValueError, match="search_endpoint not configured"):
            conn.search_index("kb-index", "test query")

    @respx.mock
    def test_doc_intel_404_raises_not_found(self, connector):
        respx.post(
            f"{AI_BASE}/documentintelligence/documentModels/prebuilt-invoice:analyze"
        ).mock(
            return_value=httpx.Response(
                404, json={"error": {"code": "ModelNotFound", "message": "Model not found"}}
            )
        )

        with pytest.raises(NotFoundError):
            connector.analyze_document("https://example.com/invoice.pdf")


# ---------------------------------------------------------------------------
# AzureAIAgent integration test
# ---------------------------------------------------------------------------


class TestAzureAIAgent:
    @respx.mock
    def test_agent_calls_analyze_document_tool(self):
        from agentic_erp.ai.azure_ai_agent import AzureAIAgent

        # respx: mock the Document Intelligence endpoint
        respx.post(
            f"{AI_BASE}/documentintelligence/documentModels/prebuilt-invoice:analyze"
        ).mock(return_value=httpx.Response(202, json=ANALYZE_RESPONSE))

        # Mock Anthropic client — first response triggers tool_use
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "analyze_document"
        tool_block.input = {"document_url": "https://example.com/inv.pdf"}
        tool_block.id = "tu_ai_001"

        tool_resp = MagicMock()
        tool_resp.stop_reason = "tool_use"
        tool_resp.content = [tool_block]

        # Second response is the final text answer
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Document analyzed. Operation ID: op-001."

        text_resp = MagicMock()
        text_resp.stop_reason = "end_turn"
        text_resp.content = [text_block]

        anthropic_client = MagicMock()
        anthropic_client.messages.create.side_effect = [tool_resp, text_resp]

        config = AzureAIConfig(
            endpoint=AI_BASE,
            api_key="test-key",
            deployment_name=DEPLOYMENT,
            search_endpoint=AI_SEARCH_BASE,
            search_api_key="search-key",
        )
        agent = AzureAIAgent(config=config, client=anthropic_client)
        result = agent.run("Analyze the invoice at https://example.com/inv.pdf")

        assert isinstance(result, str)
        assert anthropic_client.messages.create.call_count == 2
