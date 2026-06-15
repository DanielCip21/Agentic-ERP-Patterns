"""Unit tests for ERP agents: ProcurementAgent, FinanceAgent, HRAgent, ManufacturingAgent."""

from __future__ import annotations

from unittest.mock import MagicMock


from agentic_erp.erp.procurement_agent import ProcurementAgent
from agentic_erp.erp.finance_agent import FinanceAgent
from agentic_erp.erp.hr_agent import HRAgent
from agentic_erp.erp.manufacturing_agent import ManufacturingAgent


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_text_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _make_tool_then_text_response(
    tool_name: str, tool_inputs: dict, tool_use_id: str, final_text: str
):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_inputs
    tool_block.id = tool_use_id

    tool_response = MagicMock()
    tool_response.stop_reason = "tool_use"
    tool_response.content = [tool_block]

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = final_text

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_response.content = [text_block]

    return tool_response, text_response


# ---------------------------------------------------------------------------
# ProcurementAgent
# ---------------------------------------------------------------------------


class TestProcurementAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response(
            "Found 2 vendors in raw_materials category."
        )
        agent = ProcurementAgent(client=client)
        result = agent.run("Find raw materials vendors with rating >= 4.0")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "search_vendors",
            {"category": "raw_materials", "min_rating": 4.0},
            "tu_proc_001",
            "Vendors VND-001 and VND-004 qualify.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = ProcurementAgent(client=client)
        result = agent.run("Search for raw materials vendors")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_search_vendors(self):
        agent = ProcurementAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "search_vendors", {"category": "raw_materials", "min_rating": 4.0}
        )
        assert isinstance(result, list)

    def test_dispatch_create_rfq(self):
        agent = ProcurementAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "create_rfq",
            {"vendor_ids": ["VND-001"], "items": [{"sku": "SKU-A", "quantity": 100}]},
        )
        assert "rfq_id" in result or "error" in result

    def test_dispatch_create_purchase_order(self):
        agent = ProcurementAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "create_purchase_order",
            {
                "vendor_id": "VND-001",
                "items": [{"sku": "SKU-A", "quantity": 10, "unit_price": 5.0}],
                "total": 50.0,
            },
        )
        assert isinstance(result, dict)

    def test_dispatch_match_invoice_to_po(self):
        agent = ProcurementAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "match_invoice_to_po", {"invoice_id": "INV-001", "po_id": "PO-1001"}
        )
        assert isinstance(result, dict)

    def test_dispatch_unknown_tool(self):
        agent = ProcurementAgent(client=MagicMock())
        result = agent._dispatch_tool("nonexistent_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# FinanceAgent
# ---------------------------------------------------------------------------


class TestFinanceAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response(
            "There are 2 overdue invoices totalling $16,800."
        )
        agent = FinanceAgent(client=client)
        result = agent.run("List all overdue invoices")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "list_outstanding_invoices",
            {"days_overdue": 30},
            "tu_fin_001",
            "INV-2001 is 29 days overdue for $12,500.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FinanceAgent(client=client)
        result = agent.run("Show invoices overdue > 30 days")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_list_outstanding_invoices(self):
        agent = FinanceAgent(client=MagicMock())
        result = agent._dispatch_tool("list_outstanding_invoices", {})
        assert isinstance(result, list)

    def test_dispatch_list_outstanding_invoices_with_filter(self):
        agent = FinanceAgent(client=MagicMock())
        result = agent._dispatch_tool("list_outstanding_invoices", {"days_overdue": 20})
        assert isinstance(result, list)

    def test_dispatch_categorize_expense(self):
        agent = FinanceAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "categorize_expense",
            {"description": "AWS cloud services", "amount": 1200.0},
        )
        assert "category" in result

    def test_dispatch_schedule_payment(self):
        agent = FinanceAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "schedule_payment", {"invoice_id": "INV-2001", "date": "2026-07-01"}
        )
        assert isinstance(result, dict)

    def test_dispatch_reconcile_account(self):
        agent = FinanceAgent(client=MagicMock())
        result = agent._dispatch_tool("reconcile_account", {"account_id": "ACC-1001"})
        assert isinstance(result, dict)

    def test_dispatch_unknown_tool(self):
        agent = FinanceAgent(client=MagicMock())
        result = agent._dispatch_tool("fake_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# HRAgent
# ---------------------------------------------------------------------------


class TestHRAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response(
            "New employee record created for Jane Doe."
        )
        agent = HRAgent(client=client)
        result = agent.run("Onboard Jane Doe to the Engineering department")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "create_employee_record",
            {
                "name": "Jane Doe",
                "department": "Engineering",
                "start_date": "2026-07-01",
            },
            "tu_hr_001",
            "Employee record EMP-123 created successfully.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = HRAgent(client=client)
        result = agent.run("Create a record for Jane Doe")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_create_employee_record(self):
        agent = HRAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "create_employee_record",
            {
                "name": "Test Employee",
                "department": "Sales",
                "start_date": "2026-08-01",
            },
        )
        assert "id" in result or "error" in result

    def test_dispatch_provision_system_access(self):
        agent = HRAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "provision_system_access",
            {"employee_id": "EMP-001", "systems": ["ERP", "CRM", "Slack"]},
        )
        assert isinstance(result, dict)

    def test_dispatch_assign_training(self):
        agent = HRAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "assign_training", {"employee_id": "EMP-001", "role": "engineer"}
        )
        assert isinstance(result, dict)

    def test_dispatch_check_compliance_status(self):
        agent = HRAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "check_compliance_status", {"employee_id": "EMP-001"}
        )
        assert isinstance(result, dict)

    def test_dispatch_unknown_tool(self):
        agent = HRAgent(client=MagicMock())
        result = agent._dispatch_tool("not_a_real_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# ManufacturingAgent
# ---------------------------------------------------------------------------


class TestManufacturingAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response(
            "Current production schedule has 3 active work orders."
        )
        agent = ManufacturingAgent(client=client)
        result = agent.run("What is the current production schedule?")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_production_schedule",
            {},
            "tu_mfg_001",
            "Production schedule retrieved: 3 work orders in progress.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = ManufacturingAgent(client=client)
        result = agent.run("Get the production schedule")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_get_production_schedule(self):
        agent = ManufacturingAgent(client=MagicMock())
        result = agent._dispatch_tool("get_production_schedule", {})
        assert isinstance(result, (dict, list))

    def test_dispatch_explode_bom(self):
        agent = ManufacturingAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "explode_bom", {"product_id": "PROD-001", "quantity": 50}
        )
        assert isinstance(result, dict)

    def test_dispatch_create_work_order(self):
        agent = ManufacturingAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "create_work_order",
            {"product_id": "PROD-001", "quantity": 100, "due_date": "2026-07-31"},
        )
        assert isinstance(result, dict)

    def test_dispatch_check_capacity(self):
        agent = ManufacturingAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "check_capacity", {"workcenter_id": "WC-001", "date": "2026-07-15"}
        )
        assert isinstance(result, dict)

    def test_dispatch_unknown_tool(self):
        agent = ManufacturingAgent(client=MagicMock())
        result = agent._dispatch_tool("unknown_operation", {})
        assert "error" in result
