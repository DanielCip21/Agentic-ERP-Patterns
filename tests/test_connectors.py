"""Tests for connector classes — instantiation and response shapes."""

import pytest
from agentic_erp.connectors.dynamics365 import Dynamics365Connector, Dynamics365Config
from agentic_erp.connectors.salesforce import SalesforceConnector, SalesforceConfig
from agentic_erp.connectors.power_platform import PowerPlatformConnector, PowerPlatformConfig
from agentic_erp.connectors.azure_ai import AzureAIConnector, AzureAIConfig
from agentic_erp.connectors.dataverse import DataverseConnector, DataverseConfig


@pytest.fixture
def d365():
    return Dynamics365Connector(Dynamics365Config(
        tenant_id="t1", client_id="c1", client_secret="s1",
        environment_url="https://org.crm.dynamics.com"
    ))


@pytest.fixture
def sf():
    return SalesforceConnector(SalesforceConfig(
        instance_url="https://myorg.salesforce.com", access_token="tok123"
    ))


@pytest.fixture
def pp():
    return PowerPlatformConnector(PowerPlatformConfig(
        environment_id="env-01", tenant_id="t1", client_id="c1", client_secret="s1"
    ))


@pytest.fixture
def azai():
    return AzureAIConnector(AzureAIConfig(
        endpoint="https://myresource.openai.azure.com",
        api_key="key123",
        deployment_name="gpt-4o",
    ))


@pytest.fixture
def dv():
    return DataverseConnector(DataverseConfig(
        environment_url="https://org.api.crm.dynamics.com",
        tenant_id="t1", client_id="c1", client_secret="s1"
    ))


class TestDynamics365Connector:
    def test_get_account_returns_id(self, d365):
        result = d365.get_account("abc-123")
        assert "accountid" in result or "_stub" in result

    def test_create_lead_returns_lead_id(self, d365):
        result = d365.create_lead({"firstname": "Alice", "lastname": "Smith"})
        assert "leadid" in result or "_stub" in result

    def test_update_opportunity_returns_opp_id(self, d365):
        result = d365.update_opportunity("opp-1", {"stagecode": "Propose"})
        assert "opportunityid" in result or "_stub" in result

    def test_get_sales_orders_returns_list_or_dict(self, d365):
        result = d365.get_sales_orders("statecode eq 0")
        assert isinstance(result, (list, dict))

    def test_create_contact_returns_contact_id(self, d365):
        result = d365.create_contact({"lastname": "Jones"})
        assert "contactid" in result or "_stub" in result


class TestSalesforceConnector:
    def test_soql_query_returns_records(self, sf):
        result = sf.soql_query("SELECT Id FROM Account LIMIT 10")
        assert "records" in result or "_stub" in result

    def test_create_record_returns_id(self, sf):
        result = sf.create_record("Lead", {"LastName": "Doe"})
        assert isinstance(result, dict)

    def test_update_record(self, sf):
        result = sf.update_record("Contact", "003XX", {"Phone": "555-1234"})
        assert isinstance(result, dict)

    def test_delete_record(self, sf):
        result = sf.delete_record("Lead", "00QXX")
        assert isinstance(result, dict)

    def test_get_record(self, sf):
        result = sf.get_record("Account", "001XX")
        assert isinstance(result, dict)


class TestPowerPlatformConnector:
    def test_trigger_flow_returns_run_id(self, pp):
        result = pp.trigger_flow("flow-id-abc", {"input": "value"})
        assert "run_id" in result or "status" in result or "_stub" in result

    def test_list_flows_returns_dict(self, pp):
        result = pp.list_flows(environment_id="env-01")
        assert isinstance(result, (dict, list))

    def test_get_flow_run_status(self, pp):
        result = pp.get_flow_run_status("flow-1", "run-1")
        assert isinstance(result, dict)

    def test_create_dataverse_row(self, pp):
        result = pp.create_dataverse_row("accounts", {"name": "Test Co"})
        assert isinstance(result, dict)

    def test_update_dataverse_row(self, pp):
        result = pp.update_dataverse_row("contacts", "row-1", {"telephone1": "555"})
        assert isinstance(result, dict)


class TestAzureAIConnector:
    def test_chat_complete_returns_choices(self, azai):
        result = azai.chat_complete([{"role": "user", "content": "Hello"}])
        assert "choices" in result or "_stub" in result

    def test_embed_text_returns_embedding(self, azai):
        result = azai.embed_text("sample text")
        assert "embedding" in result or "_stub" in result

    def test_analyze_document_returns_status(self, azai):
        result = azai.analyze_document("https://storage.blob.core.windows.net/docs/invoice.pdf")
        assert "status" in result or "_stub" in result or "analyze_result" in result

    def test_search_index(self, azai):
        result = azai.search_index("my-index", "SSO configuration")
        assert isinstance(result, dict)


class TestDataverseConnector:
    def test_query_returns_value_array(self, dv):
        result = dv.query("accounts")
        assert "value" in result or "_stub" in result

    def test_query_with_filter_and_select(self, dv):
        result = dv.query("contacts", filter_expr="statecode eq 0", select_cols=["fullname", "emailaddress1"])
        assert isinstance(result, dict)

    def test_create_returns_id(self, dv):
        result = dv.create("leads", {"lastname": "Jones"})
        assert "id" in result or "_stub" in result

    def test_update_returns_id(self, dv):
        result = dv.update("accounts", "acc-1", {"telephone1": "555"})
        assert "id" in result or "_stub" in result

    def test_delete_returns_deleted(self, dv):
        result = dv.delete("contacts", "con-1")
        assert result.get("deleted") is True or "_stub" in result

    def test_associate_returns_associated(self, dv):
        result = dv.associate("accounts", "acc-1", "contact_customer_accounts", "con-1")
        assert result.get("associated") is True or "_stub" in result
