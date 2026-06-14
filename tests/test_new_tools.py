"""Unit tests for finance_tools, vendor_tools, and analytics_tools — no API calls required."""

import pytest
from agentic_erp.tools import finance_tools, vendor_tools, analytics_tools


# ---------------------------------------------------------------------------
# finance_tools: fraud detection
# ---------------------------------------------------------------------------

class TestScanTransactions:
    def test_returns_transactions_for_known_account(self):
        results = finance_tools.scan_transactions("ACC-01")
        assert len(results) > 0
        for tx in results:
            assert tx["account_id"] == "ACC-01"
            assert "anomaly_score" in tx
            assert 0 <= tx["anomaly_score"] <= 100

    def test_large_amount_raises_anomaly_score(self):
        results = finance_tools.scan_transactions("ACC-01")
        high_risk = [tx for tx in results if tx["amount"] > 50000]
        assert all(tx["anomaly_score"] >= 40 for tx in high_risk)

    def test_unknown_account_returns_empty(self):
        results = finance_tools.scan_transactions("ACC-UNKNOWN")
        assert results == []


class TestFlagTransaction:
    def test_flags_existing_transaction(self):
        result = finance_tools.flag_transaction("TX-1001", "Test flag")
        assert result["flagged"] is True
        assert result["tx_id"] == "TX-1001"

    def test_unknown_transaction_returns_error(self):
        result = finance_tools.flag_transaction("TX-9999", "reason")
        assert "error" in result


class TestGetAccountRiskProfile:
    def test_known_account(self):
        result = finance_tools.get_account_risk_profile("ACC-01")
        assert result["account_id"] == "ACC-01"
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    def test_unknown_account_returns_error(self):
        result = finance_tools.get_account_risk_profile("ACC-99")
        assert "error" in result


# ---------------------------------------------------------------------------
# finance_tools: crypto payments
# ---------------------------------------------------------------------------

class TestCryptoPayments:
    def test_initiate_payment_usdt(self):
        p = finance_tools.initiate_crypto_payment("VND-001", 1000.0, "USDT")
        assert p["status"] == "pending_confirmation"
        assert p["crypto_amount"] == 1000.0
        assert p["blockchain"] == "Ethereum"

    def test_initiate_payment_xrp(self):
        p = finance_tools.initiate_crypto_payment("VND-002", 500.0, "XRP")
        assert p["blockchain"] == "RippleNet"
        assert p["crypto_amount"] > 0

    def test_initiate_payment_unsupported_currency(self):
        result = finance_tools.initiate_crypto_payment("VND-001", 100.0, "DOGE")
        assert "error" in result

    def test_confirm_settlement(self):
        p = finance_tools.initiate_crypto_payment("VND-003", 250.0, "ETH")
        settled = finance_tools.confirm_payment_settlement(p["payment_id"])
        assert settled["status"] == "settled"
        assert settled["tx_hash"].startswith("0x")

    def test_get_crypto_payment_found(self):
        p = finance_tools.initiate_crypto_payment("VND-001", 750.0, "USDT")
        fetched = finance_tools.get_crypto_payment(p["payment_id"])
        assert fetched["payment_id"] == p["payment_id"]

    def test_get_crypto_payment_not_found(self):
        result = finance_tools.get_crypto_payment("CP-FAKE")
        assert "error" in result


# ---------------------------------------------------------------------------
# finance_tools: compliance
# ---------------------------------------------------------------------------

class TestComplianceTools:
    def test_get_jurisdiction_rules_known(self):
        rules = finance_tools.get_jurisdiction_rules("SG")
        assert rules["vat_rate"] == 0.09
        assert "filing_deadline" in rules

    def test_get_jurisdiction_rules_unknown(self):
        result = finance_tools.get_jurisdiction_rules("ZZ")
        assert "error" in result

    def test_check_transaction_compliance_aml_breach(self):
        result = finance_tools.check_transaction_compliance("TX-1002", "US")
        assert result["compliant"] is False
        assert len(result["issues"]) > 0

    def test_check_transaction_compliance_clean(self):
        result = finance_tools.check_transaction_compliance("TX-1003", "SG")
        assert "issues" in result

    def test_generate_compliance_report(self):
        report = finance_tools.generate_compliance_report("2026-Q2", ["US", "EU", "SG"])
        assert len(report["jurisdictions"]) == 3
        assert "report_id" in report
        for row in report["jurisdictions"]:
            assert "estimated_vat" in row


# ---------------------------------------------------------------------------
# finance_tools: cash flow
# ---------------------------------------------------------------------------

class TestCashFlowTools:
    def test_get_all_balances(self):
        bals = finance_tools.get_account_balances()
        assert "USD" in bals
        assert bals["USD"]["usd_equivalent"] > 0

    def test_get_single_currency_balance(self):
        result = finance_tools.get_account_balances(currency="EUR")
        assert result["currency"] == "EUR"

    def test_get_balance_unknown_currency(self):
        result = finance_tools.get_account_balances(currency="BTC")
        assert "error" in result

    def test_get_fx_rates(self):
        rates = finance_tools.get_fx_rates("USD", ["EUR", "SGD", "JPY"])
        assert "EUR" in rates["rates"]
        assert rates["rates"]["EUR"] is not None

    def test_forecast_cash_flow_base(self):
        fc = finance_tools.forecast_cash_flow(90, "base")
        assert len(fc["periods"]) == 3
        assert fc["summary"]["total_inflow"] > 0

    def test_forecast_cash_flow_optimistic_exceeds_pessimistic(self):
        opt = finance_tools.forecast_cash_flow(90, "optimistic")["summary"]["total_inflow"]
        pes = finance_tools.forecast_cash_flow(90, "pessimistic")["summary"]["total_inflow"]
        assert opt > pes


# ---------------------------------------------------------------------------
# vendor_tools
# ---------------------------------------------------------------------------

class TestVendorTools:
    def test_get_vendor_profile_found(self):
        v = vendor_tools.get_vendor_profile("VND-001")
        assert v["vendor_id"] == "VND-001"
        assert "on_time_delivery_pct" in v

    def test_get_vendor_profile_not_found(self):
        result = vendor_tools.get_vendor_profile("VND-999")
        assert "error" in result

    def test_score_vendor_risk_low(self):
        result = vendor_tools.score_vendor_risk("VND-001")
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert 0 <= result["risk_score"] <= 100

    def test_score_vendor_risk_higher_for_poor_sla(self):
        good = vendor_tools.score_vendor_risk("VND-001")["risk_score"]
        bad = vendor_tools.score_vendor_risk("VND-002")["risk_score"]
        assert bad > good

    def test_trigger_sla_payment_sla_met(self):
        result = vendor_tools.trigger_sla_payment("VND-001", "CNT-101", 10000.0)
        assert result["payment_triggered"] is True
        assert result["smart_contract_tx"].startswith("0x")

    def test_trigger_sla_payment_sla_not_met(self):
        result = vendor_tools.trigger_sla_payment("VND-002", "CNT-102", 50000.0)
        assert result["payment_triggered"] is False
        assert "SLA not met" in result["reason"]

    def test_trigger_sla_payment_wrong_vendor(self):
        result = vendor_tools.trigger_sla_payment("VND-001", "CNT-102", 5000.0)
        assert "error" in result

    def test_trigger_sla_payment_unknown_vendor(self):
        result = vendor_tools.trigger_sla_payment("VND-999", "CNT-101", 1000.0)
        assert "error" in result


# ---------------------------------------------------------------------------
# analytics_tools
# ---------------------------------------------------------------------------

class TestAnalyticsTools:
    def test_get_player_cohort_found(self):
        cohort = analytics_tools.get_player_cohort("C-2024Q1")
        assert cohort["cohort_id"] == "C-2024Q1"
        assert cohort["health"] in ("STRONG", "WEAK")
        assert cohort["total_cohort_value_usd"] > 0

    def test_get_player_cohort_not_found(self):
        result = analytics_tools.get_player_cohort("C-FAKE")
        assert "error" in result

    def test_get_revenue_breakdown_found(self):
        rev = analytics_tools.get_revenue_breakdown("GAME-01", "2026-Q1")
        assert rev["total_revenue_usd"] > 0
        assert "iap_usd" in rev["breakdown"]
        pct_sum = sum(v["pct_of_total"] for v in rev["breakdown"].values())
        assert abs(pct_sum - 100.0) < 1.0

    def test_get_revenue_breakdown_unknown_period(self):
        result = analytics_tools.get_revenue_breakdown("GAME-01", "2020-Q1")
        assert "error" in result

    def test_get_revenue_breakdown_unknown_game(self):
        result = analytics_tools.get_revenue_breakdown("GAME-99", "2026-Q1")
        assert "error" in result

    def test_forecast_game_revenue(self):
        fc = analytics_tools.forecast_game_revenue("GAME-02", 6)
        assert len(fc["forecast"]) == 6
        assert fc["total_projected_usd"] > 0
        assert fc["monthly_growth_rate_pct"] > 0

    def test_forecast_game_revenue_unknown_game(self):
        result = analytics_tools.forecast_game_revenue("GAME-99", 3)
        assert "error" in result
