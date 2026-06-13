"""Unit tests for connectors: Dynamics365, Salesforce, PowerPlatform, AzureAI, Dataverse."""

from __future__ import annotations

import httpx
import pytest
import respx

from agentic_erp.connectors.auth import AzureADTokenManager
from agentic_erp.connectors.dynamics365 import Dynamics365Config, Dynamics365Connector
from agentic_erp.connectors.salesforce import SalesforceConfig, SalesforceConnector
from agentic_erp.connectors.power_platform import PowerPlatformConfig, PowerPlatformConnector
from agentic_erp.connectors.azure_ai import AzureAIConfig, AzureAIConnector
from agentic_erp.connectors.dataverse import DataverseConfig, DataverseConnector

_TOKEN = {"access_token": "fake-token", "expires_in": 3600}
_D365_BASE = "https://testorg.crm.dynamics.com/api/data/v9.2"
_TOKEN_URL = "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token"


@pytest.fixture(autouse=True)
def _clear_token_cache():
    AzureADTokenManager.clear_cache()
    yield
    AzureADTokenManager.clear_cache()


# ---------------------------------------------------------------------------
# Dynamics365Connector  (live HTTP — mocked with respx)
# ---------------------------------------------------------------------------

class TestDynamics365Connector:
    def _make_connector(self) -> Dynamics365Connector:
        return Dynamics365Connector(Dynamics365Config(
            tenant_id="test-tenant", client_id="test-client",
            client_secret="test-secret", environment_url="https://testorg.crm.dynamics.com",
        ))

    def test_instantiation(self):
        assert self._make_connector().config.tenant_id == "test-tenant"

    @respx.mock
    def test_get_account_returns_dict(self):
        respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_D365_BASE}/accounts(ACC-001)").mock(
            return_value=httpx.Response(200, json={"accountid": "ACC-001", "name": "Contoso"}))
        result = self._make_connector().get_account("ACC-001")
        assert isinstance(result, dict) and "accountid" in result

    @respx.mock
    def test_create_lead_returns_dict(self):
        respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.post(f"{_D365_BASE}/leads").mock(
            return_value=httpx.Response(201, json={"leadid": "LEAD-001", "lastname": "Lead"}))
        result = self._make_connector().create_lead({"firstname": "Test", "lastname": "Lead"})
        assert isinstance(result, dict) and "leadid" in result

    @respx.mock
    def test_update_opportunity_returns_dict(self):
        respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.patch(f"{_D365_BASE}/opportunities(OPP-001)").mock(
            return_value=httpx.Response(204))
        result = self._make_connector().update_opportunity("OPP-001", {"estimatedvalue": 50000})
        assert isinstance(result, dict)

    @respx.mock
    def test_get_sales_orders_returns_list(self):
        respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_D365_BASE}/salesorders").mock(
            return_value=httpx.Response(200, json={"value": [{"salesorderid": "SO-1"}]}))
        result = self._make_connector().get_sales_orders("statuscode eq 1")
        assert isinstance(result, list) and len(result) > 0

    @respx.mock
    def test_create_contact_returns_dict(self):
        respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.post(f"{_D365_BASE}/contacts").mock(
            return_value=httpx.Response(201, json={"contactid": "CON-001", "firstname": "Jane"}))
        result = self._make_connector().create_contact({"firstname": "Jane", "lastname": "Doe"})
        assert isinstance(result, dict) and "contactid" in result


# ---------------------------------------------------------------------------
# SalesforceConnector
# ---------------------------------------------------------------------------

class TestSalesforceConnector:
    def _make_connector(self) -> SalesforceConnector:
        config = SalesforceConfig(
            instance_url="https://testorg.my.salesforce.com",
            access_token="test-access-token",
        )
        return SalesforceConnector(config)

    def test_instantiation(self):
        connector = self._make_connector()
        assert connector.config.instance_url == "https://testorg.my.salesforce.com"

    def test_soql_query_returns_dict(self):
        connector = self._make_connector()
        result = connector.soql_query("SELECT Id, Name FROM Account LIMIT 10")
        assert isinstance(result, dict)
        assert "records" in result

    def test_create_record_returns_dict(self):
        connector = self._make_connector()
        result = connector.create_record("Account", {"Name": "Test Account"})
        assert isinstance(result, dict)
        assert result["success"] is True

    def test_update_record_returns_dict(self):
        connector = self._make_connector()
        result = connector.update_record("Account", "0010000001", {"Industry": "Technology"})
        assert isinstance(result, dict)
        assert result["success"] is True

    def test_delete_record_returns_dict(self):
        connector = self._make_connector()
        result = connector.delete_record("Contact", "0030000001")
        assert isinstance(result, dict)
        assert result["success"] is True

    def test_get_record_returns_dict(self):
        connector = self._make_connector()
        result = connector.get_record("Lead", "00Q0000001")
        assert isinstance(result, dict)
        assert "Id" in result


# ---------------------------------------------------------------------------
# PowerPlatformConnector
# ---------------------------------------------------------------------------

class TestPowerPlatformConnector:
    def _make_connector(self) -> PowerPlatformConnector:
        config = PowerPlatformConfig(
            environment_id="env-12345",
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
        )
        return PowerPlatformConnector(config)

    def test_instantiation(self):
        connector = self._make_connector()
        assert connector.config.environment_id == "env-12345"

    def test_trigger_flow_returns_dict(self):
        connector = self._make_connector()
        result = connector.trigger_flow("flow-001", {"order_id": "ORD-001"})
        assert isinstance(result, dict)
        assert "run_id" in result

    def test_list_flows_returns_list(self):
        connector = self._make_connector()
        result = connector.list_flows("env-12345")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_flow_run_status_returns_dict(self):
        connector = self._make_connector()
        result = connector.get_flow_run_status("flow-001", "run-001")
        assert isinstance(result, dict)
        assert "status" in result

    def test_create_dataverse_row_returns_dict(self):
        connector = self._make_connector()
        result = connector.create_dataverse_row("cr123_orders", {"cr123_name": "Test Order"})
        assert isinstance(result, dict)

    def test_update_dataverse_row_returns_dict(self):
        connector = self._make_connector()
        result = connector.update_dataverse_row("cr123_orders", "row-001", {"cr123_status": "shipped"})
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# AzureAIConnector
# ---------------------------------------------------------------------------

class TestAzureAIConnector:
    def _make_connector(self) -> AzureAIConnector:
        config = AzureAIConfig(
            endpoint="https://myresource.openai.azure.com",
            api_key="test-api-key",
            deployment_name="gpt-4o",
        )
        return AzureAIConnector(config)

    def test_instantiation(self):
        connector = self._make_connector()
        assert connector.config.deployment_name == "gpt-4o"

    def test_chat_complete_returns_dict(self):
        connector = self._make_connector()
        messages = [{"role": "user", "content": "Hello"}]
        result = connector.chat_complete(messages)
        assert isinstance(result, dict)
        assert "choices" in result

    def test_embed_text_returns_dict(self):
        connector = self._make_connector()
        result = connector.embed_text("Sample text to embed")
        assert isinstance(result, dict)
        assert "embedding" in result
        assert isinstance(result["embedding"], list)

    def test_analyze_document_returns_dict(self):
        connector = self._make_connector()
        result = connector.analyze_document("https://example.com/invoice.pdf")
        assert isinstance(result, dict)
        assert "analyze_result" in result

    def test_search_index_returns_dict(self):
        connector = self._make_connector()
        result = connector.search_index("knowledge-base", "password reset", top_k=5)
        assert isinstance(result, dict)
        assert "value" in result


# ---------------------------------------------------------------------------
# DataverseConnector
# ---------------------------------------------------------------------------

class TestDataverseConnector:
    def _make_connector(self) -> DataverseConnector:
        config = DataverseConfig(
            environment_url="https://myorg.crm.dynamics.com",
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
        )
        return DataverseConnector(config)

    def test_instantiation(self):
        connector = self._make_connector()
        assert connector.config.environment_url == "https://myorg.crm.dynamics.com"

    def test_query_returns_dict(self):
        connector = self._make_connector()
        result = connector.query("accounts", filter_expr="statuscode eq 1")
        assert isinstance(result, dict)
        assert "value" in result

    def test_query_with_select_cols(self):
        connector = self._make_connector()
        result = connector.query("contacts", select_cols=["name", "emailaddress1"])
        assert isinstance(result, dict)

    def test_create_returns_dict(self):
        connector = self._make_connector()
        result = connector.create("leads", {"subject": "Test Lead", "firstname": "Test"})
        assert isinstance(result, dict)
        assert "id" in result

    def test_update_returns_dict(self):
        connector = self._make_connector()
        result = connector.update("accounts", "row-001", {"revenue": 1000000})
        assert isinstance(result, dict)
        assert result["id"] == "row-001"

    def test_delete_returns_dict(self):
        connector = self._make_connector()
        result = connector.delete("contacts", "contact-001")
        assert isinstance(result, dict)
        assert result["deleted"] is True

    def test_associate_returns_dict(self):
        connector = self._make_connector()
        result = connector.associate("accounts", "acc-001", "account_contacts", "contact-001")
        assert isinstance(result, dict)
        assert result["associated"] is True
