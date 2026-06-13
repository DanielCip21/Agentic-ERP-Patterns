"""Tests for live Dataverse connector — HTTP calls intercepted with respx."""

from __future__ import annotations

import httpx
import pytest
import respx

from agentic_erp.connectors.auth import AzureADTokenManager, AuthenticationError
from agentic_erp.connectors.base import ConnectorError, NotFoundError
from agentic_erp.connectors.dataverse import DataverseConfig, DataverseConnector


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOKEN_URL = "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token"
DV_BASE = "https://myorg.crm.dynamics.com/api/data/v9.2"

TOKEN_RESPONSE = {"access_token": "dv-fake-token", "expires_in": 3600}

ACCOUNT = {"accountid": "acc-001", "name": "Contoso", "revenue": 5000000}
ACCOUNTS_LIST = {"value": [ACCOUNT], "@odata.count": 1}

LEAD = {"leadid": "lead-001", "subject": "Test Lead", "firstname": "Bob", "lastname": "Smith"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_token_cache():
    AzureADTokenManager.clear_cache()
    yield
    AzureADTokenManager.clear_cache()


@pytest.fixture
def config():
    return DataverseConfig(
        environment_url="https://myorg.crm.dynamics.com",
        tenant_id="test-tenant",
        client_id="test-client",
        client_secret="test-secret",
    )


@pytest.fixture
def connector(config):
    return DataverseConnector(config)


def _mock_token(router: respx.MockRouter) -> None:
    """Add a mock AAD token endpoint to the respx router."""
    router.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json=TOKEN_RESPONSE)
    )


# ---------------------------------------------------------------------------
# DataverseConnector — happy path
# ---------------------------------------------------------------------------


class TestDataverseConnectorHappyPath:
    @respx.mock
    def test_query_table(self, connector):
        _mock_token(respx)
        respx.get(f"{DV_BASE}/accounts").mock(
            return_value=httpx.Response(200, json=ACCOUNTS_LIST)
        )
        result = connector.query("accounts")
        assert result["value"][0]["accountid"] == "acc-001"

    @respx.mock
    def test_query_with_select_and_filter(self, connector):
        _mock_token(respx)
        respx.get(f"{DV_BASE}/accounts").mock(
            return_value=httpx.Response(200, json=ACCOUNTS_LIST)
        )
        result = connector.query(
            "accounts",
            filter_expr="statecode eq 0",
            select_cols=["accountid", "name"],
        )
        assert isinstance(result, dict)
        assert "value" in result

    @respx.mock
    def test_get_record(self, connector):
        _mock_token(respx)
        respx.get(f"{DV_BASE}/accounts(acc-001)").mock(
            return_value=httpx.Response(200, json=ACCOUNT)
        )
        result = connector.get("accounts", "acc-001")
        assert result["accountid"] == "acc-001"
        assert result["name"] == "Contoso"

    @respx.mock
    def test_create_record(self, connector):
        _mock_token(respx)
        respx.post(f"{DV_BASE}/leads").mock(
            return_value=httpx.Response(201, json=LEAD)
        )
        result = connector.create("leads", {"subject": "Test Lead", "firstname": "Bob", "lastname": "Smith"})
        assert result["leadid"] == "lead-001"

    @respx.mock
    def test_update_record_returns_no_content(self, connector):
        _mock_token(respx)
        respx.patch(f"{DV_BASE}/accounts(acc-001)").mock(
            return_value=httpx.Response(204)
        )
        result = connector.update("accounts", "acc-001", {"revenue": 6000000})
        assert result == {"status": "no_content"}

    @respx.mock
    def test_upsert_record_returns_no_content(self, connector):
        _mock_token(respx)
        respx.patch(f"{DV_BASE}/accounts(cr_extid='EXT-001')").mock(
            return_value=httpx.Response(204)
        )
        result = connector.upsert("accounts", "cr_extid", "EXT-001", {"name": "Contoso"})
        assert result == {"status": "no_content"}

    @respx.mock
    def test_delete_record_returns_no_content(self, connector):
        _mock_token(respx)
        respx.delete(f"{DV_BASE}/leads(lead-001)").mock(
            return_value=httpx.Response(204)
        )
        result = connector.delete("leads", "lead-001")
        assert result == {"status": "no_content"}

    @respx.mock
    def test_associate_records_returns_no_content(self, connector):
        _mock_token(respx)
        respx.post(f"{DV_BASE}/accounts(acc-001)/account_contacts/$ref").mock(
            return_value=httpx.Response(204)
        )
        result = connector.associate("accounts", "acc-001", "account_contacts", "contacts", "con-001")
        assert result == {"status": "no_content"}

    @respx.mock
    def test_execute_fetch_xml(self, connector):
        _mock_token(respx)
        respx.get(f"{DV_BASE}/accounts").mock(
            return_value=httpx.Response(200, json=ACCOUNTS_LIST)
        )
        fetch_xml = "<fetch><entity name='account'><attribute name='accountid'/></entity></fetch>"
        result = connector.execute_fetch_xml("accounts", fetch_xml)
        assert isinstance(result, list)
        assert result[0]["accountid"] == "acc-001"


# ---------------------------------------------------------------------------
# DataverseConnector — error handling
# ---------------------------------------------------------------------------


class TestDataverseConnectorErrors:
    @respx.mock
    def test_404_raises_not_found(self, connector):
        _mock_token(respx)
        respx.get(f"{DV_BASE}/accounts(missing-id)").mock(
            return_value=httpx.Response(404, json={"error": {"code": "0x80040217", "message": "Not found"}})
        )
        with pytest.raises(NotFoundError):
            connector.get("accounts", "missing-id")

    @respx.mock
    def test_500_raises_connector_error(self, connector):
        _mock_token(respx)
        respx.get(f"{DV_BASE}/accounts(acc-001)").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(ConnectorError) as exc_info:
            connector.get("accounts", "acc-001")
        assert exc_info.value.status_code == 500

    @respx.mock
    def test_auth_failure_raises(self, connector):
        respx.post(TOKEN_URL).mock(
            return_value=httpx.Response(401, json={"error": "invalid_client"})
        )
        with pytest.raises(AuthenticationError):
            connector.get("accounts", "acc-001")


# ---------------------------------------------------------------------------
# DataverseAgent integration test
# ---------------------------------------------------------------------------


class TestDataverseAgent:
    @respx.mock
    def test_agent_calls_query_table_tool(self):
        from unittest.mock import MagicMock
        from agentic_erp.erp.dataverse_agent import DataverseAgent

        # Mock token + Dataverse API
        respx.post(TOKEN_URL).mock(
            return_value=httpx.Response(200, json=TOKEN_RESPONSE)
        )
        respx.get(f"{DV_BASE}/accounts").mock(
            return_value=httpx.Response(200, json=ACCOUNTS_LIST)
        )

        # First Claude response: tool call
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "query_table"
        tool_block.input = {"table": "accounts", "filter_expr": "statecode eq 0"}
        tool_block.id = "tu_dv_001"

        tool_resp = MagicMock()
        tool_resp.stop_reason = "tool_use"
        tool_resp.content = [tool_block]

        # Second Claude response: final text
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Found 1 active account: Contoso."

        text_resp = MagicMock()
        text_resp.stop_reason = "end_turn"
        text_resp.content = [text_block]

        anthropic_client = MagicMock()
        anthropic_client.messages.create.side_effect = [tool_resp, text_resp]

        config = DataverseConfig(
            environment_url="https://myorg.crm.dynamics.com",
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
        )
        agent = DataverseAgent(config=config, client=anthropic_client)
        result = agent.run("List all active accounts")

        assert isinstance(result, str)
        assert anthropic_client.messages.create.call_count == 2
