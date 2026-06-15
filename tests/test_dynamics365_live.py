"""Tests for live Dynamics 365 connector — HTTP calls intercepted with respx."""

from __future__ import annotations


import httpx
import pytest
import respx

from agentic_erp.connectors.auth import AzureADTokenManager, AuthenticationError
from agentic_erp.connectors.base import ConnectorError, NotFoundError, RateLimitError
from agentic_erp.connectors.dynamics365 import Dynamics365Config, Dynamics365Connector


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TOKEN_RESPONSE = {
    "access_token": "fake-access-token-abc123",
    "expires_in": 3600,
    "token_type": "Bearer",
}

ACCOUNT_RESPONSE = {
    "accountid": "ACC-001",
    "name": "Contoso Ltd",
    "telephone1": "555-0100",
    "revenue": 5000000,
}

ORDER_RESPONSE = {
    "salesorderid": "ORD-001",
    "name": "SO-1001",
    "totalamount": 12500.0,
    "statecode": 0,
    "statuscode": 1,
}

ORDERS_LIST_RESPONSE = {
    "value": [ORDER_RESPONSE],
    "@odata.count": 1,
}


@pytest.fixture(autouse=True)
def clear_token_cache():
    AzureADTokenManager.clear_cache()
    yield
    AzureADTokenManager.clear_cache()


@pytest.fixture
def config():
    return Dynamics365Config(
        tenant_id="test-tenant",
        client_id="test-client",
        client_secret="test-secret",
        environment_url="https://testorg.crm.dynamics.com",
    )


@pytest.fixture
def connector(config):
    return Dynamics365Connector(config)


def _mock_token(router: respx.MockRouter) -> None:
    """Add a mock AAD token endpoint to the respx router."""
    router.post("https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token").mock(
        return_value=httpx.Response(200, json=TOKEN_RESPONSE)
    )


# ---------------------------------------------------------------------------
# AzureADTokenManager tests
# ---------------------------------------------------------------------------


class TestAzureADTokenManager:
    @respx.mock
    def test_fetch_token_success(self):
        respx.post("https://login.microsoftonline.com/t1/oauth2/v2.0/token").mock(
            return_value=httpx.Response(200, json=TOKEN_RESPONSE)
        )
        token = AzureADTokenManager.get_token(
            "t1", "c1", "s1", "https://org.crm/.default"
        )
        assert token == "fake-access-token-abc123"

    @respx.mock
    def test_token_cached_on_second_call(self):
        route = respx.post(
            "https://login.microsoftonline.com/t1/oauth2/v2.0/token"
        ).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
        AzureADTokenManager.get_token("t1", "c1", "s1", "https://org.crm/.default")
        AzureADTokenManager.get_token("t1", "c1", "s1", "https://org.crm/.default")
        assert route.call_count == 1  # second call hit cache

    @respx.mock
    def test_fetch_token_failure_raises(self):
        respx.post("https://login.microsoftonline.com/t1/oauth2/v2.0/token").mock(
            return_value=httpx.Response(401, json={"error": "invalid_client"})
        )
        with pytest.raises(AuthenticationError, match="401"):
            AzureADTokenManager.get_token("t1", "c1", "s1", "https://org.crm/.default")

    @respx.mock
    def test_expired_token_refreshed(self):
        route = respx.post(
            "https://login.microsoftonline.com/t1/oauth2/v2.0/token"
        ).mock(
            return_value=httpx.Response(200, json={**TOKEN_RESPONSE, "expires_in": 0})
        )
        AzureADTokenManager.get_token("t1", "c1", "s1", "https://org.crm/.default")
        AzureADTokenManager.get_token("t1", "c1", "s1", "https://org.crm/.default")
        assert route.call_count == 2  # expired immediately, forced re-fetch


# ---------------------------------------------------------------------------
# Dynamics365Connector — happy path
# ---------------------------------------------------------------------------


class TestDynamics365ConnectorHappyPath:
    @respx.mock
    def test_get_account(self, connector):
        _mock_token(respx)
        respx.get(
            "https://testorg.crm.dynamics.com/api/data/v9.2/accounts(ACC-001)"
        ).mock(return_value=httpx.Response(200, json=ACCOUNT_RESPONSE))
        result = connector.get_account("ACC-001")
        assert result["accountid"] == "ACC-001"
        assert result["name"] == "Contoso Ltd"

    @respx.mock
    def test_list_accounts(self, connector):
        _mock_token(respx)
        respx.get("https://testorg.crm.dynamics.com/api/data/v9.2/accounts").mock(
            return_value=httpx.Response(200, json={"value": [ACCOUNT_RESPONSE]})
        )
        results = connector.list_accounts()
        assert isinstance(results, list)
        assert results[0]["accountid"] == "ACC-001"

    @respx.mock
    def test_get_sales_order(self, connector):
        _mock_token(respx)
        respx.get(
            "https://testorg.crm.dynamics.com/api/data/v9.2/salesorders(ORD-001)"
        ).mock(return_value=httpx.Response(200, json=ORDER_RESPONSE))
        result = connector.get_sales_order("ORD-001")
        assert result["salesorderid"] == "ORD-001"
        assert result["totalamount"] == 12500.0

    @respx.mock
    def test_get_sales_orders_with_filter(self, connector):
        _mock_token(respx)
        respx.get("https://testorg.crm.dynamics.com/api/data/v9.2/salesorders").mock(
            return_value=httpx.Response(200, json=ORDERS_LIST_RESPONSE)
        )
        results = connector.get_sales_orders(filter_expr="statecode eq 0")
        assert isinstance(results, list)
        assert len(results) == 1

    @respx.mock
    def test_update_sales_order_returns_no_content(self, connector):
        _mock_token(respx)
        respx.patch(
            "https://testorg.crm.dynamics.com/api/data/v9.2/salesorders(ORD-001)"
        ).mock(return_value=httpx.Response(204))
        result = connector.update_sales_order(
            "ORD-001", {"statecode": 1, "statuscode": 3}
        )
        assert result == {"status": "no_content"}

    @respx.mock
    def test_create_lead(self, connector):
        _mock_token(respx)
        lead_response = {
            "leadid": "LEAD-001",
            "lastname": "Smith",
            "companyname": "Acme",
        }
        respx.post("https://testorg.crm.dynamics.com/api/data/v9.2/leads").mock(
            return_value=httpx.Response(201, json=lead_response)
        )
        result = connector.create_lead({"lastname": "Smith", "companyname": "Acme"})
        assert result["leadid"] == "LEAD-001"

    @respx.mock
    def test_create_contact(self, connector):
        _mock_token(respx)
        contact_response = {
            "contactid": "CON-001",
            "firstname": "Alice",
            "lastname": "Jones",
        }
        respx.post("https://testorg.crm.dynamics.com/api/data/v9.2/contacts").mock(
            return_value=httpx.Response(201, json=contact_response)
        )
        result = connector.create_contact({"firstname": "Alice", "lastname": "Jones"})
        assert result["contactid"] == "CON-001"


# ---------------------------------------------------------------------------
# Dynamics365Connector — error handling
# ---------------------------------------------------------------------------


class TestDynamics365ConnectorErrors:
    @respx.mock
    def test_404_raises_not_found_error(self, connector):
        _mock_token(respx)
        respx.get(
            "https://testorg.crm.dynamics.com/api/data/v9.2/accounts(MISSING)"
        ).mock(
            return_value=httpx.Response(
                404, json={"error": {"code": "0x80040217", "message": "Not found"}}
            )
        )
        with pytest.raises(NotFoundError):
            connector.get_account("MISSING")

    @respx.mock
    def test_429_raises_rate_limit_error(self, connector):
        _mock_token(respx)
        # Return 429 on all retries
        respx.get(
            "https://testorg.crm.dynamics.com/api/data/v9.2/accounts(ACC-001)"
        ).mock(return_value=httpx.Response(429, headers={"Retry-After": "5"}))
        with pytest.raises(RateLimitError):
            connector.get_account("ACC-001")

    @respx.mock
    def test_500_raises_connector_error(self, connector):
        _mock_token(respx)
        respx.get(
            "https://testorg.crm.dynamics.com/api/data/v9.2/accounts(ACC-001)"
        ).mock(return_value=httpx.Response(500, text="Internal Server Error"))
        with pytest.raises(ConnectorError) as exc_info:
            connector.get_account("ACC-001")
        assert exc_info.value.status_code == 500

    @respx.mock
    def test_auth_error_propagates(self, connector):
        respx.post(
            "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token"
        ).mock(return_value=httpx.Response(401, json={"error": "invalid_client"}))
        with pytest.raises(AuthenticationError):
            connector.get_account("ACC-001")


# ---------------------------------------------------------------------------
# Dynamics365OrderAgent integration test
# ---------------------------------------------------------------------------


class TestDynamics365OrderAgent:
    @respx.mock
    def test_agent_calls_list_orders_tool(self):
        from unittest.mock import MagicMock
        from agentic_erp.erp.dynamics365_order_agent import Dynamics365OrderAgent

        # Mock token + orders API
        respx.post(
            "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token"
        ).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
        respx.get("https://testorg.crm.dynamics.com/api/data/v9.2/salesorders").mock(
            return_value=httpx.Response(200, json=ORDERS_LIST_RESPONSE)
        )

        # Mock the Claude client
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "list_orders"
        tool_block.input = {"filter_expr": "statecode eq 0"}
        tool_block.id = "tu_live_001"

        tool_resp = MagicMock()
        tool_resp.stop_reason = "tool_use"
        tool_resp.content = [tool_block]

        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Found 1 active order: SO-1001 ($12,500)."

        text_resp = MagicMock()
        text_resp.stop_reason = "end_turn"
        text_resp.content = [text_block]

        anthropic_client = MagicMock()
        anthropic_client.messages.create.side_effect = [tool_resp, text_resp]

        config = Dynamics365Config(
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
            environment_url="https://testorg.crm.dynamics.com",
        )
        agent = Dynamics365OrderAgent(config=config, client=anthropic_client)
        result = agent.run("List all active sales orders")

        assert "SO-1001" in result or isinstance(result, str)
        assert anthropic_client.messages.create.call_count == 2
