"""Tests for live Salesforce connector and CRM agent — HTTP calls intercepted with respx."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
import respx

from agentic_erp.connectors.base import ConnectorError, NotFoundError, RateLimitError
from agentic_erp.connectors.salesforce import SalesforceConfig, SalesforceConnector
from agentic_erp.crm.salesforce_crm_agent import SalesforceCRMAgent


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SF_BASE = "https://testorg.my.salesforce.com/services/data/v60.0"
TOKEN_RESPONSE = {"access_token": "sf-fake-token", "expires_in": 7200}
LEAD_RESPONSE = {
    "Id": "00Q000001",
    "FirstName": "Alice",
    "LastName": "Smith",
    "Company": "Acme",
    "Status": "New",
}
ACCOUNT_RESPONSE = {
    "Id": "001000001",
    "Name": "Acme Corp",
    "Industry": "Technology",
    "AnnualRevenue": 5000000,
}
OPP_RESPONSE = {
    "Id": "006000001",
    "Name": "Acme Deal Q1",
    "StageName": "Prospecting",
    "Amount": 25000.0,
}
SOQL_RESPONSE = {
    "totalSize": 1,
    "done": True,
    "records": [LEAD_RESPONSE],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config():
    return SalesforceConfig(
        instance_url="https://testorg.my.salesforce.com",
        access_token="sf-fake-token",
    )


@pytest.fixture
def connector(config):
    return SalesforceConnector(config)


# ---------------------------------------------------------------------------
# TestSalesforceConnectorHappyPath
# ---------------------------------------------------------------------------


class TestSalesforceConnectorHappyPath:
    @respx.mock
    def test_soql_query(self, connector):
        respx.get(f"{SF_BASE}/query").mock(
            return_value=httpx.Response(200, json=SOQL_RESPONSE)
        )
        result = connector.soql_query("SELECT Id FROM Lead LIMIT 5")
        assert result["totalSize"] == 1
        assert result["done"] is True
        assert result["records"][0]["Id"] == "00Q000001"

    @respx.mock
    def test_get_lead(self, connector):
        respx.get(f"{SF_BASE}/sobjects/Lead/00Q000001").mock(
            return_value=httpx.Response(200, json=LEAD_RESPONSE)
        )
        result = connector.get_record(
            "Lead",
            "00Q000001",
            fields=["Id", "FirstName", "LastName", "Company", "Status", "Email"],
        )
        assert result["Id"] == "00Q000001"
        assert result["LastName"] == "Smith"
        assert result["Company"] == "Acme"

    @respx.mock
    def test_get_account(self, connector):
        respx.get(f"{SF_BASE}/sobjects/Account/001000001").mock(
            return_value=httpx.Response(200, json=ACCOUNT_RESPONSE)
        )
        result = connector.get_record(
            "Account",
            "001000001",
            fields=["Id", "Name", "Industry", "AnnualRevenue", "BillingCity"],
        )
        assert result["Id"] == "001000001"
        assert result["Name"] == "Acme Corp"
        assert result["Industry"] == "Technology"

    @respx.mock
    def test_create_lead(self, connector):
        create_response = {"id": "00Q000002", "success": True, "errors": []}
        respx.post(f"{SF_BASE}/sobjects/Lead").mock(
            return_value=httpx.Response(201, json=create_response)
        )
        result = connector.create_record(
            "Lead", {"LastName": "Jones", "Company": "Beta Inc"}
        )
        assert result["id"] == "00Q000002"
        assert result["success"] is True

    @respx.mock
    def test_update_lead_returns_no_content(self, connector):
        respx.patch(f"{SF_BASE}/sobjects/Lead/00Q000001").mock(
            return_value=httpx.Response(204)
        )
        result = connector.update_record("Lead", "00Q000001", {"Status": "Working"})
        assert result == {"status": "no_content"}

    @respx.mock
    def test_delete_lead_returns_no_content(self, connector):
        respx.delete(f"{SF_BASE}/sobjects/Lead/00Q000001").mock(
            return_value=httpx.Response(204)
        )
        result = connector.delete_record("Lead", "00Q000001")
        assert result == {"status": "no_content"}

    @respx.mock
    def test_upsert_by_external_id(self, connector):
        upsert_response = {
            "id": "00Q000003",
            "success": True,
            "errors": [],
            "created": True,
        }
        respx.patch(f"{SF_BASE}/sobjects/Lead/External_Id__c/EXT-001").mock(
            return_value=httpx.Response(201, json=upsert_response)
        )
        result = connector.upsert_record(
            "Lead",
            "External_Id__c",
            "EXT-001",
            {"LastName": "Brown", "Company": "Gamma LLC"},
        )
        assert result["id"] == "00Q000003"
        assert result["created"] is True

    @respx.mock
    def test_describe_sobject(self, connector):
        describe_response = {"name": "Lead", "label": "Lead", "fields": []}
        respx.get(f"{SF_BASE}/sobjects/Lead/describe").mock(
            return_value=httpx.Response(200, json=describe_response)
        )
        result = connector.describe_sobject("Lead")
        assert result["name"] == "Lead"
        assert isinstance(result["fields"], list)


# ---------------------------------------------------------------------------
# TestSalesforceConnectorErrors
# ---------------------------------------------------------------------------


class TestSalesforceConnectorErrors:
    @respx.mock
    def test_404_raises_not_found(self, connector):
        respx.get(f"{SF_BASE}/sobjects/Lead/MISSING").mock(
            return_value=httpx.Response(
                404,
                json=[
                    {
                        "message": "The requested resource does not exist",
                        "errorCode": "NOT_FOUND",
                    }
                ],
            )
        )
        with pytest.raises(NotFoundError):
            connector.get_record("Lead", "MISSING")

    @respx.mock
    def test_401_raises_connector_error(self, connector):
        respx.get(f"{SF_BASE}/sobjects/Lead/00Q000001").mock(
            return_value=httpx.Response(
                401,
                json=[
                    {
                        "message": "Session expired or invalid",
                        "errorCode": "INVALID_SESSION_ID",
                    }
                ],
            )
        )
        with pytest.raises(ConnectorError) as exc_info:
            connector.get_record("Lead", "00Q000001")
        assert exc_info.value.status_code == 401

    @respx.mock
    def test_429_raises_rate_limit(self, connector):
        respx.get(f"{SF_BASE}/sobjects/Lead/00Q000001").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "10"})
        )
        with pytest.raises(RateLimitError):
            connector.get_record("Lead", "00Q000001")


# ---------------------------------------------------------------------------
# TestSalesforceCRMAgent
# ---------------------------------------------------------------------------


class TestSalesforceCRMAgent:
    @respx.mock
    def test_agent_calls_soql_tool(self):
        # Mock the SOQL HTTP call
        respx.get(f"{SF_BASE}/query").mock(
            return_value=httpx.Response(200, json=SOQL_RESPONSE)
        )

        # Build mock Anthropic client responses
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "soql_query"
        tool_block.input = {"query": "SELECT Id FROM Lead LIMIT 5"}
        tool_block.id = "tu_sf_001"

        tool_resp = MagicMock()
        tool_resp.stop_reason = "tool_use"
        tool_resp.content = [tool_block]

        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Found 1 lead: Alice Smith at Acme."

        text_resp = MagicMock()
        text_resp.stop_reason = "end_turn"
        text_resp.content = [text_block]

        anthropic_client = MagicMock()
        anthropic_client.messages.create.side_effect = [tool_resp, text_resp]

        agent = SalesforceCRMAgent(
            config=SalesforceConfig(
                instance_url="https://testorg.my.salesforce.com",
                access_token="sf-fake-token",
            ),
            client=anthropic_client,
        )
        result = agent.run("How many new leads do we have?")

        assert isinstance(result, str)
        assert anthropic_client.messages.create.call_count == 2
