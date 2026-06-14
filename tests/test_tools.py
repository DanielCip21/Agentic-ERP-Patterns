"""Unit tests for all ERP tool modules — no API calls required."""

import pytest
from agentic_erp.tools import erp_tools
from agentic_erp.tools import gl_tools, ap_tools, ar_tools, treasury_tools
from agentic_erp.tools import supply_chain_tools, hr_tools, sales_tools, forecasting_tools


# ---------------------------------------------------------------------------
# Original ERP tools (regression guard)
# ---------------------------------------------------------------------------

def test_get_order_found():
    order = erp_tools.get_order("ORD-001")
    assert order["id"] == "ORD-001"
    assert order["customer"] == "Contoso Ltd"


def test_get_order_not_found():
    result = erp_tools.get_order("ORD-999")
    assert "error" in result


def test_update_order_status_valid():
    result = erp_tools.update_order_status("ORD-001", "processing")
    assert result["status"] == "processing"
    assert result["order_id"] == "ORD-001"


def test_update_order_status_invalid():
    result = erp_tools.update_order_status("ORD-001", "flying")
    assert "error" in result


def test_check_inventory_found():
    item = erp_tools.check_inventory("SKU-A")
    assert item["sku"] == "SKU-A"
    assert "on_hand" in item
    assert "below_reorder_point" in item


def test_check_inventory_not_found():
    result = erp_tools.check_inventory("SKU-UNKNOWN")
    assert "error" in result


def test_list_low_stock_items():
    items = erp_tools.list_low_stock_items()
    assert isinstance(items, list)
    for item in items:
        assert item["on_hand"] < item["reorder_point"]
        assert "shortage" in item


def test_create_purchase_order():
    before = erp_tools._INVENTORY["SKU-B"]["on_hand"]
    result = erp_tools.create_purchase_order("SKU-B", 50, "Acme Supplies")
    assert "po_id" in result
    assert result["sku"] == "SKU-B"
    assert result["quantity"] == 50
    assert result["status"] == "submitted"
    assert erp_tools._INVENTORY["SKU-B"]["on_hand"] == before + 50


def test_create_purchase_order_unknown_sku():
    result = erp_tools.create_purchase_order("SKU-FAKE", 10)
    assert "error" in result


# ---------------------------------------------------------------------------
# GL tools
# ---------------------------------------------------------------------------

class TestGLTools:
    def test_reconcile_returns_balanced_flag(self):
        result = gl_tools.reconcile_gl_accounts("2025-01")
        assert "balanced" in result
        assert "period" in result
        assert "total_debits" in result
        assert "total_credits" in result

    def test_reconcile_unknown_period_returns_empty(self):
        result = gl_tools.reconcile_gl_accounts("1900-01")
        assert result["total_debits"] == 0.0
        assert result["total_credits"] == 0.0
        assert result["balanced"] is True

    def test_detect_anomalies_returns_list(self):
        result = gl_tools.detect_financial_anomalies()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_categorize_expense_marketing(self):
        result = gl_tools.categorize_expenses("Online marketing campaign", 500.00)
        assert result["suggested_account"] == "6000"
        assert result["confidence"] > 0.5

    def test_categorize_expense_unknown(self):
        result = gl_tools.categorize_expenses("Miscellaneous item", 100.00)
        assert result["suggested_account"] == "6999"

    def test_get_budget_vs_actual_found(self):
        result = gl_tools.get_budget_vs_actual("2025-Q1")
        assert "revenue" in result
        assert "variance" in result["revenue"]

    def test_get_budget_vs_actual_not_found(self):
        result = gl_tools.get_budget_vs_actual("2099-Q4")
        assert "error" in result

    def test_post_journal_entry(self):
        result = gl_tools.post_journal_entry("6000", 250.0, 0.0, "Test posting")
        assert result["status"] == "posted"
        assert result["debit"] == 250.0
        assert "id" in result

    def test_get_trial_balance(self):
        result = gl_tools.get_trial_balance()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("account" in r and "balance" in r for r in result)


# ---------------------------------------------------------------------------
# AP tools
# ---------------------------------------------------------------------------

class TestAPTools:
    def test_detect_duplicate_invoices_finds_duplicates(self):
        result = ap_tools.detect_duplicate_invoices()
        # INV-001 and INV-003 are duplicates (same vendor + amount)
        assert isinstance(result, list)
        duplicate = result[0]
        assert "invoice_ids" in duplicate
        assert len(duplicate["invoice_ids"]) >= 2

    def test_three_way_match_matched(self):
        result = ap_tools.three_way_match("INV-001")
        assert result["invoice_id"] == "INV-001"
        assert "match_result" in result
        assert "approved_for_payment" in result

    def test_three_way_match_not_found(self):
        result = ap_tools.three_way_match("INV-999")
        assert "error" in result

    def test_score_vendor_returns_composite(self):
        result = ap_tools.score_vendor("VND-001")
        assert "composite_score" in result
        assert result["composite_score"] > 0
        assert result["risk_rating"] in ("low", "medium", "high")
        assert result["recommendation"] in ("preferred", "review", "watchlist")

    def test_score_vendor_not_found(self):
        result = ap_tools.score_vendor("VND-999")
        assert "error" in result

    def test_list_invoices_due(self):
        result = ap_tools.list_invoices_due(days_ahead=365)
        assert isinstance(result, list)

    def test_approve_invoice(self):
        result = ap_tools.approve_invoice("INV-001")
        assert result["status"] == "approved"

    def test_approve_invoice_not_found(self):
        result = ap_tools.approve_invoice("INV-999")
        assert "error" in result

    def test_dynamic_discount_reduces_payment(self):
        result = ap_tools.calculate_dynamic_discount("INV-002", 5)
        assert result["net_payment"] <= result["original_amount"]
        assert result["discount_rate"] >= 0

    def test_dynamic_discount_not_found(self):
        result = ap_tools.calculate_dynamic_discount("INV-999", 5)
        assert "error" in result


# ---------------------------------------------------------------------------
# AR tools
# ---------------------------------------------------------------------------

class TestARTools:
    def test_forecast_collections(self):
        result = ar_tools.forecast_collections(30)
        assert "total_outstanding" in result
        assert "collection_rate_forecast" in result
        assert 0 <= result["collection_rate_forecast"] <= 100

    def test_score_customer_credit_found(self):
        result = ar_tools.score_customer_credit("CUST-001")
        assert "adjusted_score" in result
        assert result["risk_tier"] in ("A", "B", "C")
        assert result["recommended_action"] in ("increase_limit", "maintain", "reduce_limit")

    def test_score_customer_credit_not_found(self):
        result = ar_tools.score_customer_credit("CUST-999")
        assert "error" in result

    def test_list_overdue_receivables(self):
        result = ar_tools.list_overdue_receivables(min_days_overdue=0)
        assert isinstance(result, list)
        assert all(r["days_overdue"] >= 0 for r in result)

    def test_apply_cash_payment_full(self):
        # Use a fresh approach: check that a full payment clears the balance
        result = ar_tools.apply_cash_payment("AR-003", 10000.00)
        assert result["status"] == "paid"
        assert result["remaining_balance"] == 0.0
        assert result["overpayment"] > 0

    def test_apply_cash_payment_partial(self):
        ar_tools._RECEIVABLES["AR-002"]["amount"] = 8700.00
        ar_tools._RECEIVABLES["AR-002"]["status"] = "overdue"
        result = ar_tools.apply_cash_payment("AR-002", 1000.00)
        assert result["remaining_balance"] == pytest.approx(7700.00)
        assert result["status"] != "paid"

    def test_apply_cash_payment_not_found(self):
        result = ar_tools.apply_cash_payment("AR-999", 500.00)
        assert "error" in result

    def test_generate_collection_reminder(self):
        result = ar_tools.generate_collection_reminder("CUST-002")
        assert "message" in result
        assert result["urgency"] in ("URGENT", "STANDARD")

    def test_generate_collection_reminder_not_found(self):
        result = ar_tools.generate_collection_reminder("CUST-999")
        assert "error" in result


# ---------------------------------------------------------------------------
# Treasury tools
# ---------------------------------------------------------------------------

class TestTreasuryTools:
    def test_get_cash_position(self):
        result = treasury_tools.get_cash_position()
        assert "total_usd_equivalent" in result
        assert result["total_usd_equivalent"] > 0
        assert isinstance(result["accounts"], list)

    def test_forecast_liquidity(self):
        result = treasury_tools.forecast_liquidity(weeks_ahead=4)
        assert "cumulative_net_cashflow" in result
        assert result["liquidity_risk"] in ("HIGH", "LOW")
        assert len(result["weekly_projections"]) == 4

    def test_convert_currency_known_pair(self):
        result = treasury_tools.convert_currency("USD", "EUR", 1000.0)
        assert "converted_amount" in result
        assert result["converted_amount"] > 0
        assert result["from_currency"] == "USD"

    def test_convert_currency_unknown_pair(self):
        result = treasury_tools.convert_currency("USD", "JPY", 1000.0)
        assert "error" in result

    def test_execute_fx_hedge(self):
        result = treasury_tools.execute_fx_hedge("USD/EUR", 100000.0, 3)
        assert result["status"] == "active"
        assert "forward_rate" in result
        assert "hedge_id" in result

    def test_detect_payment_fraud_large_amount(self):
        result = treasury_tools.detect_payment_fraud(75000.0, "VND-001", "USD")
        assert "risk_score" in result
        assert "amount_exceeds_threshold" in result["flags"]

    def test_detect_payment_fraud_unknown_vendor(self):
        result = treasury_tools.detect_payment_fraud(1000.0, "VND-UNKNOWN", "USD")
        assert "unknown_vendor" in result["flags"]

    def test_reconcile_bank_statement_known_account(self):
        result = treasury_tools.reconcile_bank_statement("BA-USD-001", 342000.00)
        assert result["status"] == "RECONCILED"

    def test_reconcile_bank_statement_variance(self):
        result = treasury_tools.reconcile_bank_statement("BA-USD-001", 300000.00)
        assert result["status"] == "VARIANCE_DETECTED"

    def test_reconcile_bank_statement_not_found(self):
        result = treasury_tools.reconcile_bank_statement("BA-FAKE", 1000.0)
        assert "error" in result


# ---------------------------------------------------------------------------
# Supply Chain tools
# ---------------------------------------------------------------------------

class TestSupplyChainTools:
    def test_select_optimal_supplier_returns_winner(self):
        result = supply_chain_tools.select_optimal_supplier("SKU-A", 100, "balanced")
        assert "recommended_supplier" in result
        assert result["recommended_supplier"].startswith("SUP-")
        assert isinstance(result["all_suppliers_ranked"], list)

    def test_select_optimal_supplier_cost_priority(self):
        result = supply_chain_tools.select_optimal_supplier("SKU-A", 50, "cost")
        assert "recommended_supplier" in result

    def test_forecast_demand_known_sku(self):
        result = supply_chain_tools.forecast_demand("SKU-A", months_ahead=3)
        assert "forecast" in result
        assert len(result["forecast"]) == 3
        assert result["total_forecasted"] > 0

    def test_forecast_demand_unknown_sku(self):
        result = supply_chain_tools.forecast_demand("SKU-FAKE", months_ahead=2)
        assert "error" in result

    def test_track_shipment_found(self):
        result = supply_chain_tools.track_shipment("SHIP-001")
        assert result["status"] == "in_transit"
        assert "days_until_eta" in result

    def test_track_shipment_not_found(self):
        result = supply_chain_tools.track_shipment("SHIP-999")
        assert "error" in result

    def test_assess_supply_chain_risk(self):
        result = supply_chain_tools.assess_supply_chain_risk("SUP-001")
        assert result["overall_risk"] in ("LOW", "MEDIUM", "HIGH")
        assert isinstance(result["risk_factors"], list)

    def test_assess_supply_chain_risk_not_found(self):
        result = supply_chain_tools.assess_supply_chain_risk("SUP-999")
        assert "error" in result

    def test_optimize_freight_cost(self):
        result = supply_chain_tools.optimize_freight_cost("Chicago", "Los Angeles", 500.0)
        assert "optimal_carrier" in result
        assert result["optimal_cost"] > 0
        assert len(result["all_options"]) == 3
        # Optimal should be cheapest
        costs = [o["total_cost"] for o in result["all_options"]]
        assert result["optimal_cost"] == min(costs)


# ---------------------------------------------------------------------------
# HR tools
# ---------------------------------------------------------------------------

class TestHRTools:
    def test_analyze_skills_gap_found(self):
        result = hr_tools.analyze_skills_gap("EMP-002")
        assert "missing_skills" in result
        assert isinstance(result["missing_skills"], list)
        assert result["training_priority"] in ("HIGH", "MEDIUM", "LOW")
        assert 0 <= result["skill_coverage_pct"] <= 100

    def test_analyze_skills_gap_not_found(self):
        result = hr_tools.analyze_skills_gap("EMP-999")
        assert "error" in result

    def test_predict_attrition_risk(self):
        result = hr_tools.predict_attrition_risk("EMP-001")
        assert "attrition_risk_score" in result
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert isinstance(result["recommended_actions"], list)

    def test_predict_attrition_risk_not_found(self):
        result = hr_tools.predict_attrition_risk("EMP-999")
        assert "error" in result

    def test_process_payroll(self):
        result = hr_tools.process_payroll("EMP-001", "2025-01")
        assert result["status"] == "processed"
        assert result["gross_pay"] > 0
        assert result["net_pay"] < result["gross_pay"]
        assert result["total_deductions"] > 0

    def test_process_payroll_not_found(self):
        result = hr_tools.process_payroll("EMP-999", "2025-01")
        assert "error" in result

    def test_check_labor_law_compliance(self):
        result = hr_tools.check_labor_law_compliance("EMP-001")
        assert "compliant" in result
        assert isinstance(result["issues"], list)

    def test_check_labor_law_compliance_not_found(self):
        result = hr_tools.check_labor_law_compliance("EMP-999")
        assert "error" in result


# ---------------------------------------------------------------------------
# Sales tools
# ---------------------------------------------------------------------------

class TestSalesTools:
    def test_forecast_revenue_pipeline(self):
        result = sales_tools.forecast_revenue_pipeline(months_ahead=3)
        assert "total_pipeline" in result
        assert "weighted_pipeline" in result
        assert result["weighted_pipeline"] <= result["total_pipeline"]

    def test_assess_deal_risk_found(self):
        result = sales_tools.assess_deal_risk("OPP-001")
        assert result["overall_risk"] in ("LOW", "MEDIUM", "HIGH")
        assert isinstance(result["risk_factors"], list)

    def test_assess_deal_risk_not_found(self):
        result = sales_tools.assess_deal_risk("OPP-999")
        assert "error" in result

    def test_analyze_customer_retention_found(self):
        result = sales_tools.analyze_customer_retention("Fabrikam Inc")
        assert "churn_risk_score" in result
        assert result["churn_risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert isinstance(result["recommended_actions"], list)

    def test_analyze_customer_retention_not_found(self):
        result = sales_tools.analyze_customer_retention("Unknown Corp")
        assert "error" in result

    def test_get_project_health(self):
        result = sales_tools.get_project_health("PROJ-001")
        assert "budget_utilization_pct" in result
        assert "schedule_efficiency_index" in result
        assert isinstance(result["flags"], list)

    def test_get_project_health_not_found(self):
        result = sales_tools.get_project_health("PROJ-999")
        assert "error" in result

    def test_generate_invoice_from_milestone(self):
        result = sales_tools.generate_invoice_from_milestone("PROJ-001", "Phase 1 Complete", 50000.0)
        assert result["status"] == "issued"
        assert result["amount"] == 50000.0
        assert "invoice_id" in result

    def test_generate_invoice_from_milestone_not_found(self):
        result = sales_tools.generate_invoice_from_milestone("PROJ-999", "Phase 1", 1000.0)
        assert "error" in result


# ---------------------------------------------------------------------------
# Forecasting tools
# ---------------------------------------------------------------------------

class TestForecastingTools:
    def test_generate_financial_forecast_base(self):
        result = forecasting_tools.generate_financial_forecast("base", years_ahead=3)
        assert result["scenario"] == "base"
        assert len(result["projections"]) == 3
        for proj in result["projections"]:
            assert "revenue" in proj
            assert "ebitda_margin_pct" in proj

    def test_generate_financial_forecast_bear(self):
        result = forecasting_tools.generate_financial_forecast("bear", years_ahead=2)
        assert result["scenario"] == "bear"
        assert len(result["projections"]) == 2

    def test_generate_financial_forecast_invalid_scenario(self):
        result = forecasting_tools.generate_financial_forecast("worst_ever")
        assert "error" in result

    def test_calculate_tax_liability_us(self):
        result = forecasting_tools.calculate_tax_liability(1_000_000.0, "US")
        assert "total_tax_liability" in result
        assert result["total_tax_liability"] > 0
        assert result["jurisdiction"] == "US"

    def test_calculate_tax_liability_unknown_jurisdiction(self):
        result = forecasting_tools.calculate_tax_liability(1_000_000.0, "XY")
        assert "error" in result

    def test_run_esg_report(self):
        result = forecasting_tools.run_esg_report()
        assert "esg_score" in result
        assert result["esg_rating"] in ("A", "B", "C")
        assert isinstance(result["improvement_areas"], list)

    def test_detect_fraud_pattern_structuring(self):
        entries = [{"id": "JE-TEST", "amount": 9800.0, "vendor": "VND-X", "approver": "EMP-1"}]
        result = forecasting_tools.detect_fraud_pattern(entries)
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert any(f["pattern"] == "structuring" for f in result["fraud_indicators"])

    def test_detect_fraud_pattern_self_approval(self):
        entries = [{"id": "JE-SA", "amount": 500.0, "vendor": "VND-SAME", "approver": "VND-SAME"}]
        result = forecasting_tools.detect_fraud_pattern(entries)
        assert any(f["pattern"] == "self_approval" for f in result["fraud_indicators"])

    def test_detect_fraud_pattern_clean(self):
        entries = [{"id": "JE-OK", "amount": 1000.0, "vendor": "VND-001", "approver": "EMP-001"}]
        result = forecasting_tools.detect_fraud_pattern(entries)
        assert result["risk_level"] == "LOW"
        assert result["flags_found"] == 0

    def test_model_risk_scenario_revenue_decline(self):
        result = forecasting_tools.model_risk_scenario("revenue_decline", 20.0)
        assert "stressed_revenue" in result
        assert result["stressed_revenue"] < result["base_revenue"]
        assert "solvency_risk" in result

    def test_model_risk_scenario_invalid(self):
        result = forecasting_tools.model_risk_scenario("zombie_apocalypse", 100.0)
        assert "error" in result
