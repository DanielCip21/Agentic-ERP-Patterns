"""Integration-style tests for all agents — Anthropic client is mocked."""

import json
import pytest
from unittest.mock import MagicMock
from agentic_erp.agents.order_agent import OrderProcessingAgent
from agentic_erp.agents.inventory_agent import InventoryAgent
from agentic_erp.agents.gl_agent import GLAutomationAgent
from agentic_erp.agents.ap_agent import APAutomationAgent
from agentic_erp.agents.ar_agent import ARCollectionsAgent
from agentic_erp.agents.treasury_agent import TreasuryManagementAgent
from agentic_erp.agents.supply_chain_agent import SupplyChainAgent
from agentic_erp.agents.hr_agent import HRPayrollAgent
from agentic_erp.agents.sales_agent import SalesPipelineAgent
from agentic_erp.agents.forecasting_agent import FinancialForecastingAgent
from agentic_erp.patterns.multi_agent import MultiAgentOrchestrator
from agentic_erp.patterns.human_in_loop import HumanInLoopAgent
from agentic_erp.patterns.erp_orchestrator import ERPOrchestrator


# ---------------------------------------------------------------------------
# Shared mock helpers
# ---------------------------------------------------------------------------

def _make_text_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _make_tool_then_text_response(tool_name: str, tool_inputs: dict, tool_use_id: str, final_text: str):
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


def _mock_client(final_text: str = "Done."):
    client = MagicMock()
    client.messages.create.return_value = _make_text_response(final_text)
    return client


# ---------------------------------------------------------------------------
# Original agents (regression guard)
# ---------------------------------------------------------------------------

class TestOrderProcessingAgent:
    def test_direct_text_response(self):
        client = _mock_client("Order ORD-001 is in pending status.")
        agent = OrderProcessingAgent(client=client)
        result = agent.run("What is the status of order ORD-001?")
        assert "pending" in result.lower() or "ORD-001" in result

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_order", {"order_id": "ORD-001"}, "tu_abc", "Order ORD-001 is pending."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = OrderProcessingAgent(client=client)
        result = agent.run("Get details for ORD-001")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_unknown_tool_returns_error(self):
        agent = OrderProcessingAgent(client=_mock_client())
        result = agent._dispatch_tool("nonexistent_tool", {})
        assert "error" in result


class TestInventoryAgent:
    def test_low_stock_scan(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "list_low_stock_items", {}, "tu_xyz", "SKU-B is below reorder point. PO created."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = InventoryAgent(client=client)
        result = agent.run("Check for low stock and replenish.")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# GL agent
# ---------------------------------------------------------------------------

class TestGLAutomationAgent:
    def test_direct_response(self):
        agent = GLAutomationAgent(client=_mock_client("GL reconciliation complete."))
        result = agent.run("Reconcile GL for 2025-01")
        assert isinstance(result, str)

    def test_reconcile_tool_dispatch(self):
        result = GLAutomationAgent(client=_mock_client())._dispatch_tool(
            "reconcile_gl_accounts", {"period": "2025-01"}
        )
        assert "balanced" in result

    def test_detect_anomalies_dispatch(self):
        result = GLAutomationAgent(client=_mock_client())._dispatch_tool(
            "detect_financial_anomalies", {}
        )
        assert isinstance(result, list)

    def test_categorize_expenses_dispatch(self):
        result = GLAutomationAgent(client=_mock_client())._dispatch_tool(
            "categorize_expenses", {"description": "Marketing spend", "amount": 1000.0}
        )
        assert "suggested_account" in result

    def test_post_journal_entry_dispatch(self):
        result = GLAutomationAgent(client=_mock_client())._dispatch_tool(
            "post_journal_entry", {"account": "6000", "debit": 100.0, "credit": 0.0, "description": "Test"}
        )
        assert result["status"] == "posted"

    def test_get_trial_balance_dispatch(self):
        result = GLAutomationAgent(client=_mock_client())._dispatch_tool(
            "get_trial_balance", {}
        )
        assert isinstance(result, list)

    def test_unknown_tool_returns_error(self):
        result = GLAutomationAgent(client=_mock_client())._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# AP agent
# ---------------------------------------------------------------------------

class TestAPAutomationAgent:
    def test_direct_response(self):
        agent = APAutomationAgent(client=_mock_client("Duplicate invoices detected."))
        result = agent.run("Check for duplicate invoices")
        assert isinstance(result, str)

    def test_detect_duplicates_dispatch(self):
        result = APAutomationAgent(client=_mock_client())._dispatch_tool(
            "detect_duplicate_invoices", {}
        )
        assert isinstance(result, list)

    def test_three_way_match_dispatch(self):
        result = APAutomationAgent(client=_mock_client())._dispatch_tool(
            "three_way_match", {"invoice_id": "INV-002"}
        )
        assert "match_result" in result

    def test_score_vendor_dispatch(self):
        result = APAutomationAgent(client=_mock_client())._dispatch_tool(
            "score_vendor", {"vendor_id": "VND-001"}
        )
        assert "composite_score" in result

    def test_list_invoices_due_dispatch(self):
        result = APAutomationAgent(client=_mock_client())._dispatch_tool(
            "list_invoices_due", {"days_ahead": 90}
        )
        assert isinstance(result, list)

    def test_approve_invoice_dispatch(self):
        result = APAutomationAgent(client=_mock_client())._dispatch_tool(
            "approve_invoice", {"invoice_id": "INV-001"}
        )
        assert result["status"] == "approved"

    def test_dynamic_discount_dispatch(self):
        result = APAutomationAgent(client=_mock_client())._dispatch_tool(
            "calculate_dynamic_discount", {"invoice_id": "INV-002", "pay_in_days": 10}
        )
        assert "net_payment" in result

    def test_unknown_tool_returns_error(self):
        result = APAutomationAgent(client=_mock_client())._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# AR agent
# ---------------------------------------------------------------------------

class TestARCollectionsAgent:
    def test_direct_response(self):
        agent = ARCollectionsAgent(client=_mock_client("Collections forecast ready."))
        result = agent.run("Forecast collections for next 30 days")
        assert isinstance(result, str)

    def test_forecast_collections_dispatch(self):
        result = ARCollectionsAgent(client=_mock_client())._dispatch_tool(
            "forecast_collections", {"days_ahead": 30}
        )
        assert "total_outstanding" in result

    def test_score_customer_credit_dispatch(self):
        result = ARCollectionsAgent(client=_mock_client())._dispatch_tool(
            "score_customer_credit", {"customer_id": "CUST-001"}
        )
        assert "risk_tier" in result

    def test_list_overdue_dispatch(self):
        result = ARCollectionsAgent(client=_mock_client())._dispatch_tool(
            "list_overdue_receivables", {"min_days_overdue": 10}
        )
        assert isinstance(result, list)

    def test_apply_cash_payment_dispatch(self):
        result = ARCollectionsAgent(client=_mock_client())._dispatch_tool(
            "apply_cash_payment", {"ar_id": "AR-001", "payment_amount": 500.0}
        )
        assert "payment_applied" in result

    def test_generate_reminder_dispatch(self):
        result = ARCollectionsAgent(client=_mock_client())._dispatch_tool(
            "generate_collection_reminder", {"customer_id": "CUST-003"}
        )
        assert "message" in result

    def test_unknown_tool_returns_error(self):
        result = ARCollectionsAgent(client=_mock_client())._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# Treasury agent
# ---------------------------------------------------------------------------

class TestTreasuryManagementAgent:
    def test_direct_response(self):
        agent = TreasuryManagementAgent(client=_mock_client("Cash position retrieved."))
        result = agent.run("Get current cash position")
        assert isinstance(result, str)

    def test_get_cash_position_dispatch(self):
        result = TreasuryManagementAgent(client=_mock_client())._dispatch_tool(
            "get_cash_position", {}
        )
        assert "total_usd_equivalent" in result

    def test_forecast_liquidity_dispatch(self):
        result = TreasuryManagementAgent(client=_mock_client())._dispatch_tool(
            "forecast_liquidity", {"weeks_ahead": 3}
        )
        assert "liquidity_risk" in result

    def test_convert_currency_dispatch(self):
        result = TreasuryManagementAgent(client=_mock_client())._dispatch_tool(
            "convert_currency", {"from_currency": "USD", "to_currency": "EUR", "amount": 5000.0}
        )
        assert "converted_amount" in result

    def test_execute_fx_hedge_dispatch(self):
        result = TreasuryManagementAgent(client=_mock_client())._dispatch_tool(
            "execute_fx_hedge", {"currency_pair": "USD/EUR", "notional_amount": 100000.0}
        )
        assert result["status"] == "active"

    def test_detect_payment_fraud_dispatch(self):
        result = TreasuryManagementAgent(client=_mock_client())._dispatch_tool(
            "detect_payment_fraud", {"transaction_amount": 60000.0, "vendor_id": "VND-001", "currency": "USD"}
        )
        assert "risk_score" in result

    def test_reconcile_bank_statement_dispatch(self):
        result = TreasuryManagementAgent(client=_mock_client())._dispatch_tool(
            "reconcile_bank_statement", {"account_id": "BA-USD-001", "statement_balance": 342000.0}
        )
        assert "status" in result

    def test_unknown_tool_returns_error(self):
        result = TreasuryManagementAgent(client=_mock_client())._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# Supply Chain agent
# ---------------------------------------------------------------------------

class TestSupplyChainAgent:
    def test_direct_response(self):
        agent = SupplyChainAgent(client=_mock_client("Supplier selected."))
        result = agent.run("Select the best supplier for SKU-A, quantity 200")
        assert isinstance(result, str)

    def test_select_supplier_dispatch(self):
        result = SupplyChainAgent(client=_mock_client())._dispatch_tool(
            "select_optimal_supplier", {"sku": "SKU-A", "quantity": 100}
        )
        assert "recommended_supplier" in result

    def test_forecast_demand_dispatch(self):
        result = SupplyChainAgent(client=_mock_client())._dispatch_tool(
            "forecast_demand", {"sku": "SKU-A", "months_ahead": 2}
        )
        assert "forecast" in result

    def test_track_shipment_dispatch(self):
        result = SupplyChainAgent(client=_mock_client())._dispatch_tool(
            "track_shipment", {"shipment_id": "SHIP-001"}
        )
        assert "status" in result

    def test_assess_risk_dispatch(self):
        result = SupplyChainAgent(client=_mock_client())._dispatch_tool(
            "assess_supply_chain_risk", {"supplier_id": "SUP-001"}
        )
        assert "overall_risk" in result

    def test_optimize_freight_dispatch(self):
        result = SupplyChainAgent(client=_mock_client())._dispatch_tool(
            "optimize_freight_cost", {"origin": "Chicago", "destination": "Miami", "weight_kg": 200.0}
        )
        assert "optimal_carrier" in result

    def test_unknown_tool_returns_error(self):
        result = SupplyChainAgent(client=_mock_client())._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# HR agent
# ---------------------------------------------------------------------------

class TestHRPayrollAgent:
    def test_direct_response(self):
        agent = HRPayrollAgent(client=_mock_client("Skills gap analysis complete."))
        result = agent.run("Analyze skills gap for EMP-001")
        assert isinstance(result, str)

    def test_skills_gap_dispatch(self):
        result = HRPayrollAgent(client=_mock_client())._dispatch_tool(
            "analyze_skills_gap", {"employee_id": "EMP-001"}
        )
        assert "missing_skills" in result

    def test_attrition_dispatch(self):
        result = HRPayrollAgent(client=_mock_client())._dispatch_tool(
            "predict_attrition_risk", {"employee_id": "EMP-002"}
        )
        assert "risk_level" in result

    def test_process_payroll_dispatch(self):
        result = HRPayrollAgent(client=_mock_client())._dispatch_tool(
            "process_payroll", {"employee_id": "EMP-003", "period": "2025-01"}
        )
        assert result["status"] == "processed"

    def test_labor_law_compliance_dispatch(self):
        result = HRPayrollAgent(client=_mock_client())._dispatch_tool(
            "check_labor_law_compliance", {"employee_id": "EMP-001"}
        )
        assert "compliant" in result

    def test_unknown_tool_returns_error(self):
        result = HRPayrollAgent(client=_mock_client())._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# Sales agent
# ---------------------------------------------------------------------------

class TestSalesPipelineAgent:
    def test_direct_response(self):
        agent = SalesPipelineAgent(client=_mock_client("Revenue forecast ready."))
        result = agent.run("Forecast revenue for next 3 months")
        assert isinstance(result, str)

    def test_forecast_pipeline_dispatch(self):
        result = SalesPipelineAgent(client=_mock_client())._dispatch_tool(
            "forecast_revenue_pipeline", {"months_ahead": 3}
        )
        assert "weighted_pipeline" in result

    def test_deal_risk_dispatch(self):
        result = SalesPipelineAgent(client=_mock_client())._dispatch_tool(
            "assess_deal_risk", {"opportunity_id": "OPP-002"}
        )
        assert "overall_risk" in result

    def test_customer_retention_dispatch(self):
        result = SalesPipelineAgent(client=_mock_client())._dispatch_tool(
            "analyze_customer_retention", {"customer_name": "Contoso Ltd"}
        )
        assert "churn_risk_score" in result

    def test_project_health_dispatch(self):
        result = SalesPipelineAgent(client=_mock_client())._dispatch_tool(
            "get_project_health", {"project_id": "PROJ-002"}
        )
        assert "budget_utilization_pct" in result

    def test_milestone_invoice_dispatch(self):
        result = SalesPipelineAgent(client=_mock_client())._dispatch_tool(
            "generate_invoice_from_milestone", {"project_id": "PROJ-001", "milestone": "Phase 2", "amount": 75000.0}
        )
        assert result["status"] == "issued"

    def test_unknown_tool_returns_error(self):
        result = SalesPipelineAgent(client=_mock_client())._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# Forecasting agent
# ---------------------------------------------------------------------------

class TestFinancialForecastingAgent:
    def test_direct_response(self):
        agent = FinancialForecastingAgent(client=_mock_client("Forecast generated."))
        result = agent.run("Generate a 3-year base case financial forecast")
        assert isinstance(result, str)

    def test_generate_forecast_dispatch(self):
        result = FinancialForecastingAgent(client=_mock_client())._dispatch_tool(
            "generate_financial_forecast", {"scenario": "bull", "years_ahead": 2}
        )
        assert len(result["projections"]) == 2

    def test_tax_liability_dispatch(self):
        result = FinancialForecastingAgent(client=_mock_client())._dispatch_tool(
            "calculate_tax_liability", {"revenue": 2_000_000.0, "jurisdiction": "DE"}
        )
        assert "total_tax_liability" in result

    def test_esg_report_dispatch(self):
        result = FinancialForecastingAgent(client=_mock_client())._dispatch_tool(
            "run_esg_report", {}
        )
        assert "esg_score" in result

    def test_fraud_pattern_dispatch(self):
        entries = [{"id": "JE-X", "amount": 9900.0, "vendor": "VND-A", "approver": "EMP-1"}]
        result = FinancialForecastingAgent(client=_mock_client())._dispatch_tool(
            "detect_fraud_pattern", {"gl_entries": entries}
        )
        assert "risk_level" in result

    def test_risk_scenario_dispatch(self):
        result = FinancialForecastingAgent(client=_mock_client())._dispatch_tool(
            "model_risk_scenario", {"shock_type": "cost_spike", "magnitude_pct": 15.0}
        )
        assert "stressed_ebitda" in result

    def test_unknown_tool_returns_error(self):
        result = FinancialForecastingAgent(client=_mock_client())._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# ERPOrchestrator routing
# ---------------------------------------------------------------------------

class TestERPOrchestrator:
    def test_routes_gl_task(self):
        client = _mock_client("GL reconciliation complete.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Reconcile the GL journal entries")
        assert "gl" in results

    def test_routes_ap_task(self):
        client = _mock_client("Duplicate invoices found.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Scan for duplicate invoices from vendors")
        assert "ap" in results

    def test_routes_ar_task(self):
        client = _mock_client("Overdue receivables listed.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("List all overdue receivables")
        assert "ar" in results

    def test_routes_treasury_task(self):
        client = _mock_client("Cash position retrieved.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Get current cash position and liquidity forecast")
        assert "treasury" in results

    def test_routes_supply_chain_task(self):
        client = _mock_client("Shipment tracked.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Track shipment SHIP-001 and check supply chain risk")
        assert "supply_chain" in results

    def test_routes_hr_task(self):
        client = _mock_client("Skills gap analysis done.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Analyze employee skills gap and run payroll")
        assert "hr" in results

    def test_routes_sales_task(self):
        client = _mock_client("Pipeline forecast ready.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Forecast the sales pipeline revenue")
        assert "sales" in results

    def test_routes_forecasting_task(self):
        client = _mock_client("Financial forecast ready.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Generate financial forecast and ESG compliance report")
        assert "forecasting" in results

    def test_ambiguous_task_routes_to_all(self):
        client = _mock_client("ERP summary done.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Run the complete daily ERP status report")
        assert len(results) == 8

    def test_run_domain_direct(self):
        client = _mock_client("Done.")
        orch = ERPOrchestrator(client=client)
        result = orch.run_domain("gl", "Check trial balance")
        assert isinstance(result, str)

    def test_run_domain_invalid_raises(self):
        orch = ERPOrchestrator(client=_mock_client())
        with pytest.raises(ValueError, match="Unknown domain"):
            orch.run_domain("payables_xyz", "task")


# ---------------------------------------------------------------------------
# Original patterns (regression guard)
# ---------------------------------------------------------------------------

class TestMultiAgentOrchestrator:
    def test_routes_order_task(self):
        client = _mock_client("Order processed.")
        orch = MultiAgentOrchestrator(client=client)
        results = orch.run("Process order ORD-002")
        assert "order_agent" in results
        assert "inventory_agent" not in results

    def test_routes_inventory_task(self):
        client = _mock_client("Stock replenished.")
        orch = MultiAgentOrchestrator(client=client)
        results = orch.run("Check stock levels and reorder if needed")
        assert "inventory_agent" in results
        assert "order_agent" not in results

    def test_routes_ambiguous_task_to_both(self):
        client = _mock_client("Done.")
        orch = MultiAgentOrchestrator(client=client)
        results = orch.run("Run the daily ERP summary")
        assert "order_agent" in results
        assert "inventory_agent" in results


class TestHumanInLoopAgent:
    def test_approved_action_proceeds(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "update_order_status",
            {"order_id": "ORD-001", "status": "shipped"},
            "tu_ship",
            "Order ORD-001 shipped.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = HumanInLoopAgent(approval_callback=lambda *_: True, client=client)
        result = agent.run("Ship order ORD-001")
        assert isinstance(result, str)

    def test_rejected_action_blocked(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "update_order_status",
            {"order_id": "ORD-001", "status": "cancelled"},
            "tu_cancel",
            "Action was rejected.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        rejected_calls: list = []

        def tracking_callback(name, inputs):
            rejected_calls.append((name, inputs))
            return False

        agent = HumanInLoopAgent(approval_callback=tracking_callback, client=client)
        result = agent.run("Cancel order ORD-001")
        assert len(rejected_calls) == 1
        assert rejected_calls[0][0] == "update_order_status"
        assert rejected_calls[0][1]["status"] == "cancelled"
        assert isinstance(result, str)
