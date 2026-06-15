"""Tests for live Power Platform connector — HTTP calls intercepted with respx."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
import respx

from agentic_erp.connectors.auth import AzureADTokenManager, AuthenticationError
from agentic_erp.connectors.base import ConnectorError, NotFoundError
from agentic_erp.connectors.power_platform import (
    PowerPlatformConfig,
    PowerPlatformConnector,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AAD_TOKEN_URL = "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token"
FLOW_BASE = "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/env-12345"
DV_BASE = "https://orgtest.crm.dynamics.com/api/data/v9.2"

TOKEN_RESPONSE = {"access_token": "pp-fake-token", "expires_in": 3600}
FLOW_LIST_RESPONSE = {
    "value": [
        {
            "name": "order-approval",
            "id": "flow-guid-001",
            "properties": {"displayName": "Order Approval"},
        }
    ]
}
FLOW_RUN_RESPONSE = {
    "name": "run-001",
    "properties": {"status": "Running", "startTime": "2024-01-01T00:00:00Z"},
}
RUNS_LIST_RESPONSE = {"value": [FLOW_RUN_RESPONSE]}
DV_ROW = {
    "cr123_ordersid": "row-001",
    "cr123_name": "Test Order",
    "cr123_status": "pending",
}
DV_LIST_RESPONSE = {"value": [DV_ROW]}


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
    return PowerPlatformConfig(
        environment_id="env-12345",
        environment_url="https://orgtest.crm.dynamics.com",
        tenant_id="test-tenant",
        client_id="test-client",
        client_secret="test-secret",
    )


@pytest.fixture
def connector(config):
    return PowerPlatformConnector(config)


def _mock_token(router: respx.MockRouter) -> None:
    """Add a mock AAD token endpoint to the respx router."""
    router.post(AAD_TOKEN_URL).mock(
        return_value=httpx.Response(200, json=TOKEN_RESPONSE)
    )


# ---------------------------------------------------------------------------
# PowerPlatformConnector — happy path
# ---------------------------------------------------------------------------


class TestPowerPlatformConnectorHappyPath:
    @respx.mock
    def test_list_flows(self, connector):
        _mock_token(respx)
        respx.get(f"{FLOW_BASE}/flows").mock(
            return_value=httpx.Response(200, json=FLOW_LIST_RESPONSE)
        )
        result = connector.list_flows()
        assert isinstance(result, list)
        assert result[0]["id"] == "flow-guid-001"
        assert result[0]["properties"]["displayName"] == "Order Approval"

    @respx.mock
    def test_trigger_flow(self, connector):
        _mock_token(respx)
        respx.post(f"{FLOW_BASE}/flows/flow-guid-001/triggers/manual/run").mock(
            return_value=httpx.Response(200, json={"run_id": "run-001"})
        )
        result = connector.trigger_flow("flow-guid-001", {"order_id": "ORD-001"})
        assert result["run_id"] == "run-001"

    @respx.mock
    def test_get_flow_run_status(self, connector):
        _mock_token(respx)
        respx.get(f"{FLOW_BASE}/flows/flow-guid-001/runs/run-001").mock(
            return_value=httpx.Response(200, json=FLOW_RUN_RESPONSE)
        )
        result = connector.get_flow_run_status("flow-guid-001", "run-001")
        assert result["name"] == "run-001"
        assert result["properties"]["status"] == "Running"

    @respx.mock
    def test_list_flow_runs(self, connector):
        _mock_token(respx)
        respx.get(f"{FLOW_BASE}/flows/flow-guid-001/runs").mock(
            return_value=httpx.Response(200, json=RUNS_LIST_RESPONSE)
        )
        result = connector.list_flow_runs("flow-guid-001")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "run-001"

    @respx.mock
    def test_create_dataverse_row(self, connector):
        _mock_token(respx)
        respx.post(f"{DV_BASE}/cr123_orders").mock(
            return_value=httpx.Response(201, json=DV_ROW)
        )
        result = connector.create_dataverse_row(
            "cr123_orders", {"cr123_name": "Test Order"}
        )
        assert result["cr123_ordersid"] == "row-001"

    @respx.mock
    def test_update_dataverse_row_returns_no_content(self, connector):
        _mock_token(respx)
        respx.patch(f"{DV_BASE}/cr123_orders(row-001)").mock(
            return_value=httpx.Response(204)
        )
        result = connector.update_dataverse_row(
            "cr123_orders", "row-001", {"cr123_status": "approved"}
        )
        assert result == {"status": "no_content"}

    @respx.mock
    def test_query_dataverse(self, connector):
        _mock_token(respx)
        respx.get(f"{DV_BASE}/cr123_orders").mock(
            return_value=httpx.Response(200, json=DV_LIST_RESPONSE)
        )
        result = connector.query_dataverse(
            "cr123_orders", filter_expr="cr123_status eq 'pending'"
        )
        assert isinstance(result, list)
        assert result[0]["cr123_ordersid"] == "row-001"

    @respx.mock
    def test_delete_dataverse_row_returns_no_content(self, connector):
        _mock_token(respx)
        respx.delete(f"{DV_BASE}/cr123_orders(row-001)").mock(
            return_value=httpx.Response(204)
        )
        result = connector.delete_dataverse_row("cr123_orders", "row-001")
        assert result == {"status": "no_content"}


# ---------------------------------------------------------------------------
# PowerPlatformConnector — error handling
# ---------------------------------------------------------------------------


class TestPowerPlatformConnectorErrors:
    @respx.mock
    def test_flow_404_raises_not_found(self, connector):
        _mock_token(respx)
        respx.get(f"{FLOW_BASE}/flows/missing-flow/runs/run-001").mock(
            return_value=httpx.Response(
                404, json={"error": {"code": "FlowNotFound", "message": "Not found"}}
            )
        )
        with pytest.raises(NotFoundError):
            connector.get_flow_run_status("missing-flow", "run-001")

    @respx.mock
    def test_dv_500_raises_connector_error(self, connector):
        _mock_token(respx)
        respx.get(f"{DV_BASE}/cr123_orders").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(ConnectorError) as exc_info:
            connector.query_dataverse("cr123_orders")
        assert exc_info.value.status_code == 500

    @respx.mock
    def test_auth_error_propagates(self, connector):
        respx.post(AAD_TOKEN_URL).mock(
            return_value=httpx.Response(401, json={"error": "invalid_client"})
        )
        with pytest.raises(AuthenticationError):
            connector.list_flows()


# ---------------------------------------------------------------------------
# PowerPlatformAgent integration test
# ---------------------------------------------------------------------------


class TestPowerPlatformAgent:
    @respx.mock
    def test_agent_triggers_flow_tool(self, config):
        from agentic_erp.api.power_platform_agent import PowerPlatformAgent

        # Mock token + flow trigger API
        respx.post(AAD_TOKEN_URL).mock(
            return_value=httpx.Response(200, json=TOKEN_RESPONSE)
        )
        respx.post(f"{FLOW_BASE}/flows/flow-guid-001/triggers/manual/run").mock(
            return_value=httpx.Response(200, json={"run_id": "run-001"})
        )

        # Mock Claude client — first call returns tool_use
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "trigger_flow"
        tool_block.input = {
            "flow_id": "flow-guid-001",
            "payload": {"order_id": "ORD-001"},
        }
        tool_block.id = "tu_pp_001"

        tool_resp = MagicMock()
        tool_resp.stop_reason = "tool_use"
        tool_resp.content = [tool_block]

        # Second call returns end_turn text
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Flow triggered successfully. Run ID: run-001."

        text_resp = MagicMock()
        text_resp.stop_reason = "end_turn"
        text_resp.content = [text_block]

        anthropic_client = MagicMock()
        anthropic_client.messages.create.side_effect = [tool_resp, text_resp]

        agent = PowerPlatformAgent(config=config, client=anthropic_client)
        result = agent.run("Trigger the order approval flow for ORD-001")

        assert isinstance(result, str)
        assert anthropic_client.messages.create.call_count == 2
