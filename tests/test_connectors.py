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
_AAD_TOKEN_URL = "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token"

_D365_BASE = "https://testorg.crm.dynamics.com/api/data/v9.2"
_SF_BASE = "https://testorg.my.salesforce.com/services/data/v60.0"
_PP_FLOW_BASE = "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/env-12345"
_PP_DV_BASE = "https://orgtest.crm.dynamics.com/api/data/v9.2"
_AI_BASE = "https://myresource.openai.azure.com"
_AI_SEARCH_BASE = "https://mysearch.search.windows.net"
_DV_BASE = "https://myorg.crm.dynamics.com/api/data/v9.2"
_DV_TOKEN_URL = "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token"


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
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_D365_BASE}/accounts(ACC-001)").mock(
            return_value=httpx.Response(200, json={"accountid": "ACC-001", "name": "Contoso"}))
        result = self._make_connector().get_account("ACC-001")
        assert isinstance(result, dict) and "accountid" in result

    @respx.mock
    def test_create_lead_returns_dict(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.post(f"{_D365_BASE}/leads").mock(
            return_value=httpx.Response(201, json={"leadid": "LEAD-001", "lastname": "Lead"}))
        result = self._make_connector().create_lead({"firstname": "Test", "lastname": "Lead"})
        assert isinstance(result, dict) and "leadid" in result

    @respx.mock
    def test_update_opportunity_returns_dict(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.patch(f"{_D365_BASE}/opportunities(OPP-001)").mock(
            return_value=httpx.Response(204))
        result = self._make_connector().update_opportunity("OPP-001", {"estimatedvalue": 50000})
        assert isinstance(result, dict)

    @respx.mock
    def test_get_sales_orders_returns_list(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_D365_BASE}/salesorders").mock(
            return_value=httpx.Response(200, json={"value": [{"salesorderid": "SO-1"}]}))
        result = self._make_connector().get_sales_orders("statuscode eq 1")
        assert isinstance(result, list) and len(result) > 0

    @respx.mock
    def test_create_contact_returns_dict(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.post(f"{_D365_BASE}/contacts").mock(
            return_value=httpx.Response(201, json={"contactid": "CON-001", "firstname": "Jane"}))
        result = self._make_connector().create_contact({"firstname": "Jane", "lastname": "Doe"})
        assert isinstance(result, dict) and "contactid" in result


# ---------------------------------------------------------------------------
# SalesforceConnector  (pre-fetched access_token — no OAuth2 round-trip)
# ---------------------------------------------------------------------------

class TestSalesforceConnector:
    def _make_connector(self) -> SalesforceConnector:
        return SalesforceConnector(SalesforceConfig(
            instance_url="https://testorg.my.salesforce.com",
            access_token="test-access-token",
        ))

    def test_instantiation(self):
        assert self._make_connector().config.instance_url == "https://testorg.my.salesforce.com"

    def test_config_requires_auth(self):
        with pytest.raises(Exception):
            SalesforceConfig(instance_url="https://testorg.my.salesforce.com")

    @respx.mock
    def test_soql_query_returns_dict(self):
        respx.get(f"{_SF_BASE}/query").mock(return_value=httpx.Response(
            200, json={"totalSize": 1, "done": True, "records": [{"Id": "001", "Name": "Acme"}]}))
        result = self._make_connector().soql_query("SELECT Id, Name FROM Account LIMIT 10")
        assert isinstance(result, dict) and "records" in result

    @respx.mock
    def test_get_record_returns_dict(self):
        respx.get(f"{_SF_BASE}/sobjects/Lead/00Q0000001").mock(
            return_value=httpx.Response(200, json={"Id": "00Q0000001", "LastName": "Smith"}))
        result = self._make_connector().get_record("Lead", "00Q0000001")
        assert isinstance(result, dict) and "Id" in result

    @respx.mock
    def test_create_record_returns_success(self):
        respx.post(f"{_SF_BASE}/sobjects/Account").mock(
            return_value=httpx.Response(201, json={"id": "001", "success": True, "errors": []}))
        result = self._make_connector().create_record("Account", {"Name": "Test Account"})
        assert isinstance(result, dict) and result.get("success") is True

    @respx.mock
    def test_update_record_returns_no_content(self):
        respx.patch(f"{_SF_BASE}/sobjects/Account/0010000001").mock(
            return_value=httpx.Response(204))
        result = self._make_connector().update_record("Account", "0010000001", {"Industry": "Technology"})
        assert result.get("status") == "no_content"

    @respx.mock
    def test_delete_record_returns_no_content(self):
        respx.delete(f"{_SF_BASE}/sobjects/Contact/0030000001").mock(
            return_value=httpx.Response(204))
        result = self._make_connector().delete_record("Contact", "0030000001")
        assert result.get("status") == "no_content"

    @respx.mock
    def test_upsert_record_returns_dict(self):
        respx.patch(f"{_SF_BASE}/sobjects/Account/External_Id__c/EXT-001").mock(
            return_value=httpx.Response(200, json={"id": "001", "success": True}))
        result = self._make_connector().upsert_record("Account", "External_Id__c", "EXT-001", {"Name": "Upserted"})
        assert isinstance(result, dict)

    @respx.mock
    def test_describe_sobject_returns_dict(self):
        respx.get(f"{_SF_BASE}/sobjects/Account/describe").mock(
            return_value=httpx.Response(200, json={"name": "Account", "fields": []}))
        result = self._make_connector().describe_sobject("Account")
        assert isinstance(result, dict) and result.get("name") == "Account"


# ---------------------------------------------------------------------------
# PowerPlatformConnector  (flow + Dataverse — both mocked with respx)
# ---------------------------------------------------------------------------

class TestPowerPlatformConnector:
    def _make_connector(self) -> PowerPlatformConnector:
        return PowerPlatformConnector(PowerPlatformConfig(
            environment_id="env-12345",
            environment_url="https://orgtest.crm.dynamics.com",
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
        ))

    def test_instantiation(self):
        assert self._make_connector().config.environment_id == "env-12345"

    @respx.mock
    def test_list_flows_returns_list(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_PP_FLOW_BASE}/flows").mock(return_value=httpx.Response(
            200, json={"value": [{"name": "flow-001", "id": "guid-001"}]}))
        result = self._make_connector().list_flows()
        assert isinstance(result, list) and len(result) > 0

    @respx.mock
    def test_trigger_flow_returns_dict(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.post(f"{_PP_FLOW_BASE}/flows/flow-001/triggers/manual/run").mock(
            return_value=httpx.Response(200, json={"run_id": "run-001"}))
        result = self._make_connector().trigger_flow("flow-001", {"order_id": "ORD-001"})
        assert isinstance(result, dict) and "run_id" in result

    @respx.mock
    def test_get_flow_run_status_returns_dict(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_PP_FLOW_BASE}/flows/flow-001/runs/run-001").mock(
            return_value=httpx.Response(200, json={"name": "run-001", "status": {"code": "Running"}}))
        result = self._make_connector().get_flow_run_status("flow-001", "run-001")
        assert isinstance(result, dict) and "status" in result

    @respx.mock
    def test_list_flow_runs_returns_list(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_PP_FLOW_BASE}/flows/flow-001/runs").mock(return_value=httpx.Response(
            200, json={"value": [{"name": "run-001"}, {"name": "run-002"}]}))
        result = self._make_connector().list_flow_runs("flow-001")
        assert isinstance(result, list) and len(result) == 2

    @respx.mock
    def test_create_dataverse_row_returns_dict(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.post(f"{_PP_DV_BASE}/cr123_orders").mock(return_value=httpx.Response(
            201, json={"cr123_ordersid": "row-001", "cr123_name": "Test"}))
        result = self._make_connector().create_dataverse_row("cr123_orders", {"cr123_name": "Test Order"})
        assert isinstance(result, dict) and "cr123_ordersid" in result

    @respx.mock
    def test_update_dataverse_row_returns_no_content(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.patch(f"{_PP_DV_BASE}/cr123_orders(row-001)").mock(return_value=httpx.Response(204))
        result = self._make_connector().update_dataverse_row("cr123_orders", "row-001", {"cr123_status": "shipped"})
        assert result.get("status") == "no_content"

    @respx.mock
    def test_query_dataverse_returns_list(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_PP_DV_BASE}/cr123_orders").mock(return_value=httpx.Response(
            200, json={"value": [{"cr123_ordersid": "row-001"}]}))
        result = self._make_connector().query_dataverse("cr123_orders")
        assert isinstance(result, list)

    @respx.mock
    def test_delete_dataverse_row_returns_no_content(self):
        respx.post(_AAD_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.delete(f"{_PP_DV_BASE}/cr123_orders(row-001)").mock(return_value=httpx.Response(204))
        result = self._make_connector().delete_dataverse_row("cr123_orders", "row-001")
        assert result.get("status") == "no_content"


# ---------------------------------------------------------------------------
# AzureAIConnector  (api-key auth — no OAuth2 token fetch)
# ---------------------------------------------------------------------------

class TestAzureAIConnector:
    def _make_connector(self, with_search: bool = False) -> AzureAIConnector:
        extra = {"search_endpoint": _AI_SEARCH_BASE, "search_api_key": "search-key"} if with_search else {}
        return AzureAIConnector(AzureAIConfig(
            endpoint=_AI_BASE,
            api_key="test-api-key",
            deployment_name="gpt-4o",
            **extra,
        ))

    def test_instantiation(self):
        assert self._make_connector().config.deployment_name == "gpt-4o"

    def test_search_index_raises_without_endpoint(self):
        with pytest.raises(ValueError, match="search_endpoint"):
            self._make_connector().search_index("kb", "query")

    @respx.mock
    def test_chat_complete_returns_dict(self):
        respx.post(f"{_AI_BASE}/openai/deployments/gpt-4o/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Hello"}}]}))
        result = self._make_connector().chat_complete([{"role": "user", "content": "Hello"}])
        assert isinstance(result, dict) and "choices" in result

    @respx.mock
    def test_embed_text_returns_dict(self):
        respx.post(f"{_AI_BASE}/openai/deployments/gpt-4o/embeddings").mock(
            return_value=httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2, 0.3]}]}))
        result = self._make_connector().embed_text("Sample text to embed")
        assert isinstance(result, dict) and "data" in result

    @respx.mock
    def test_embed_batch_returns_dict(self):
        respx.post(f"{_AI_BASE}/openai/deployments/gpt-4o/embeddings").mock(
            return_value=httpx.Response(200, json={"data": [{"embedding": [0.1]}, {"embedding": [0.2]}]}))
        result = self._make_connector().embed_batch(["text one", "text two"])
        assert isinstance(result, dict) and len(result["data"]) == 2

    @respx.mock
    def test_analyze_document_returns_dict(self):
        respx.post(f"{_AI_BASE}/documentintelligence/documentModels/prebuilt-invoice:analyze").mock(
            return_value=httpx.Response(202, json={"operationId": "op-001"}))
        result = self._make_connector().analyze_document("https://example.com/invoice.pdf")
        assert isinstance(result, dict) and "operationId" in result

    @respx.mock
    def test_get_supported_models_returns_dict(self):
        respx.get(f"{_AI_BASE}/documentintelligence/documentModels").mock(
            return_value=httpx.Response(200, json={"value": [{"modelId": "prebuilt-invoice"}]}))
        result = self._make_connector().get_supported_models()
        assert isinstance(result, dict) and "value" in result

    @respx.mock
    def test_search_index_returns_dict(self):
        respx.post(f"{_AI_SEARCH_BASE}/indexes/knowledge-base/docs/search").mock(
            return_value=httpx.Response(200, json={"value": [{"id": "doc-1", "content": "reset guide"}]}))
        result = self._make_connector(with_search=True).search_index("knowledge-base", "password reset")
        assert isinstance(result, dict) and "value" in result

    @respx.mock
    def test_vector_search_returns_dict(self):
        respx.post(f"{_AI_SEARCH_BASE}/indexes/kb-index/docs/search").mock(
            return_value=httpx.Response(200, json={"value": [{"id": "doc-2"}]}))
        result = self._make_connector(with_search=True).vector_search("kb-index", [0.1, 0.2, 0.3])
        assert isinstance(result, dict) and "value" in result

    @respx.mock
    def test_upload_documents_returns_dict(self):
        respx.post(f"{_AI_SEARCH_BASE}/indexes/kb-index/docs/index").mock(
            return_value=httpx.Response(200, json={"value": [{"key": "doc-1", "status": True}]}))
        result = self._make_connector(with_search=True).upload_documents(
            "kb-index", [{"id": "doc-1", "content": "hello"}])
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# DataverseConnector  (live HTTP — mocked with respx)
# ---------------------------------------------------------------------------

class TestDataverseConnector:
    def _make_connector(self) -> DataverseConnector:
        return DataverseConnector(DataverseConfig(
            environment_url="https://myorg.crm.dynamics.com",
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
        ))

    def test_instantiation(self):
        assert self._make_connector().config.environment_url == "https://myorg.crm.dynamics.com"

    @respx.mock
    def test_query_returns_dict(self):
        respx.post(_DV_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_DV_BASE}/accounts").mock(return_value=httpx.Response(
            200, json={"value": [{"accountid": "A1", "name": "Contoso"}]}))
        result = self._make_connector().query("accounts", filter_expr="statuscode eq 1")
        assert isinstance(result, dict) and "value" in result

    @respx.mock
    def test_get_record_returns_dict(self):
        respx.post(_DV_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.get(f"{_DV_BASE}/accounts(A1)").mock(return_value=httpx.Response(
            200, json={"accountid": "A1", "name": "Contoso"}))
        result = self._make_connector().get("accounts", "A1")
        assert isinstance(result, dict) and result.get("accountid") == "A1"

    @respx.mock
    def test_create_returns_dict(self):
        respx.post(_DV_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.post(f"{_DV_BASE}/leads").mock(return_value=httpx.Response(
            201, json={"leadid": "L1", "subject": "Test Lead"}))
        result = self._make_connector().create("leads", {"subject": "Test Lead", "firstname": "Test"})
        assert isinstance(result, dict) and "leadid" in result

    @respx.mock
    def test_update_returns_no_content(self):
        respx.post(_DV_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.patch(f"{_DV_BASE}/accounts(row-001)").mock(return_value=httpx.Response(204))
        result = self._make_connector().update("accounts", "row-001", {"revenue": 1000000})
        assert result.get("status") == "no_content"

    @respx.mock
    def test_upsert_returns_no_content(self):
        respx.post(_DV_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.patch(f"{_DV_BASE}/accounts(cr_externalid='EXT-001')").mock(
            return_value=httpx.Response(204))
        result = self._make_connector().upsert("accounts", "cr_externalid", "EXT-001", {"name": "Upserted"})
        assert result.get("status") == "no_content"

    @respx.mock
    def test_delete_returns_no_content(self):
        respx.post(_DV_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.delete(f"{_DV_BASE}/contacts(contact-001)").mock(return_value=httpx.Response(204))
        result = self._make_connector().delete("contacts", "contact-001")
        assert result.get("status") == "no_content"

    @respx.mock
    def test_associate_returns_no_content(self):
        respx.post(_DV_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.post(f"{_DV_BASE}/accounts(acc-001)/account_contacts/$ref").mock(
            return_value=httpx.Response(204))
        result = self._make_connector().associate(
            "accounts", "acc-001", "account_contacts", "contacts", "contact-001")
        assert result.get("status") == "no_content"

    @respx.mock
    def test_disassociate_returns_no_content(self):
        respx.post(_DV_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.delete(f"{_DV_BASE}/accounts(acc-001)/account_contacts(contact-001)/$ref").mock(
            return_value=httpx.Response(204))
        result = self._make_connector().disassociate("accounts", "acc-001", "account_contacts", "contact-001")
        assert result.get("status") == "no_content"

    @respx.mock
    def test_batch_returns_dict(self):
        respx.post(_DV_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN))
        respx.post(f"{_DV_BASE}/$batch").mock(return_value=httpx.Response(
            200, json={"responses": [{"id": "1", "status": 200}]}))
        result = self._make_connector().batch([
            {"method": "GET", "url": "accounts", "id": "1"}
        ])
        assert isinstance(result, dict) and "responses" in result
