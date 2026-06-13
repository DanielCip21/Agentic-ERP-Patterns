"""Integration-style tests for new agents — Anthropic client is mocked."""

from unittest.mock import MagicMock
from agentic_erp.agents.fraud_detection_agent import FraudDetectionAgent
from agentic_erp.agents.crypto_payment_agent import CryptoPaymentAgent
from agentic_erp.agents.compliance_agent import ComplianceAgent
from agentic_erp.agents.cashflow_forecast_agent import CashFlowForecastAgent
from agentic_erp.agents.vendor_risk_agent import VendorRiskAgent
from agentic_erp.agents.game_analytics_agent import GameRevenueAnalyticsAgent


def _text_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [block]
    return resp


def _tool_then_text(tool_name: str, tool_inputs: dict, final_text: str):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_inputs
    tool_block.id = "tu_mock"

    tool_resp = MagicMock()
    tool_resp.stop_reason = "tool_use"
    tool_resp.content = [tool_block]

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = final_text

    text_resp = MagicMock()
    text_resp.stop_reason = "end_turn"
    text_resp.content = [text_block]

    return tool_resp, text_resp


# ---------------------------------------------------------------------------
# FraudDetectionAgent
# ---------------------------------------------------------------------------

class TestFraudDetectionAgent:
    def test_direct_response(self):
        client = MagicMock()
        client.messages.create.return_value = _text_response("No anomalies detected.")
        agent = FraudDetectionAgent(client=client)
        result = agent.run("Scan ACC-01 for fraud.")
        assert isinstance(result, str)

    def test_scan_transactions_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "scan_transactions", {"account_id": "ACC-01"}, "TX-1002 flagged as high-risk."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FraudDetectionAgent(client=client)
        result = agent.run("Scan ACC-01 for anomalies.")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_flag_transaction_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "flag_transaction",
            {"tx_id": "TX-1002", "reason": "Unusually large amount at odd hours"},
            "Transaction TX-1002 has been flagged.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FraudDetectionAgent(client=client)
        result = agent.run("Flag TX-1002.")
        assert isinstance(result, str)

    def test_get_account_risk_profile_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "get_account_risk_profile", {"account_id": "ACC-02"}, "ACC-02 is HIGH risk."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FraudDetectionAgent(client=client)
        result = agent.run("Get risk profile for ACC-02.")
        assert isinstance(result, str)

    def test_unknown_tool_returns_error(self):
        agent = FraudDetectionAgent(client=MagicMock())
        result = agent._dispatch_tool("nonexistent_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# CryptoPaymentAgent
# ---------------------------------------------------------------------------

class TestCryptoPaymentAgent:
    def test_initiate_payment_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "initiate_crypto_payment",
            {"vendor_id": "VND-001", "amount_usd": 5000.0, "currency": "XRP"},
            "Payment CP-XXXX initiated via RippleNet.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = CryptoPaymentAgent(client=client)
        result = agent.run("Pay VND-001 $5000 in XRP.")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_confirm_settlement_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "confirm_payment_settlement", {"payment_id": "CP-ABCD1234"}, "Payment settled on-chain."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = CryptoPaymentAgent(client=client)
        result = agent.run("Confirm settlement for CP-ABCD1234.")
        assert isinstance(result, str)

    def test_unknown_tool_returns_error(self):
        agent = CryptoPaymentAgent(client=MagicMock())
        result = agent._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# ComplianceAgent
# ---------------------------------------------------------------------------

class TestComplianceAgent:
    def test_jurisdiction_rules_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "get_jurisdiction_rules", {"country_code": "SG"}, "Singapore GST is 9%."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = ComplianceAgent(client=client)
        result = agent.run("What are Singapore's tax rules?")
        assert isinstance(result, str)

    def test_check_transaction_compliance_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "check_transaction_compliance",
            {"tx_id": "TX-1002", "jurisdiction": "US"},
            "TX-1002 breaches the US AML threshold.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = ComplianceAgent(client=client)
        result = agent.run("Check TX-1002 for US compliance.")
        assert isinstance(result, str)

    def test_generate_report_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "generate_compliance_report",
            {"period": "2026-Q2", "jurisdictions": ["US", "SG"]},
            "Compliance report generated for 2026-Q2.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = ComplianceAgent(client=client)
        result = agent.run("Generate Q2 2026 compliance report for US and SG.")
        assert isinstance(result, str)

    def test_unknown_tool_returns_error(self):
        agent = ComplianceAgent(client=MagicMock())
        result = agent._dispatch_tool("mystery_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# CashFlowForecastAgent
# ---------------------------------------------------------------------------

class TestCashFlowForecastAgent:
    def test_get_balances_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "get_account_balances", {}, "USD balance is $4.25M."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = CashFlowForecastAgent(client=client)
        result = agent.run("Show me all account balances.")
        assert isinstance(result, str)

    def test_forecast_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "forecast_cash_flow",
            {"horizon_days": 90, "scenario": "base"},
            "Net cash flow over 90 days is positive.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = CashFlowForecastAgent(client=client)
        result = agent.run("Forecast cash flow for the next 90 days.")
        assert isinstance(result, str)

    def test_fx_rates_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "get_fx_rates",
            {"base_currency": "USD", "target_currencies": ["EUR", "JPY"]},
            "EUR/USD is 0.921, JPY/USD is 153.4.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = CashFlowForecastAgent(client=client)
        result = agent.run("Get FX rates from USD to EUR and JPY.")
        assert isinstance(result, str)

    def test_unknown_tool_returns_error(self):
        agent = CashFlowForecastAgent(client=MagicMock())
        result = agent._dispatch_tool("quantum_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# VendorRiskAgent
# ---------------------------------------------------------------------------

class TestVendorRiskAgent:
    def test_vendor_profile_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "get_vendor_profile", {"vendor_id": "VND-002"}, "CloudHW Japan has 7 SLA breaches YTD."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = VendorRiskAgent(client=client)
        result = agent.run("Show profile for VND-002.")
        assert isinstance(result, str)

    def test_score_vendor_risk_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "score_vendor_risk", {"vendor_id": "VND-002"}, "VND-002 is MEDIUM risk with score 49."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = VendorRiskAgent(client=client)
        result = agent.run("Score risk for VND-002.")
        assert isinstance(result, str)

    def test_trigger_sla_payment_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "trigger_sla_payment",
            {"vendor_id": "VND-001", "contract_id": "CNT-101", "amount_usd": 50000.0},
            "Payment released to VND-001 via smart contract.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = VendorRiskAgent(client=client)
        result = agent.run("Release $50K to VND-001 under CNT-101 if SLA is met.")
        assert isinstance(result, str)

    def test_unknown_tool_returns_error(self):
        agent = VendorRiskAgent(client=MagicMock())
        result = agent._dispatch_tool("blockchain_oracle", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# GameRevenueAnalyticsAgent
# ---------------------------------------------------------------------------

class TestGameRevenueAnalyticsAgent:
    def test_player_cohort_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "get_player_cohort", {"cohort_id": "C-2024Q1"}, "C-2024Q1 has STRONG health with $48 LTV."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = GameRevenueAnalyticsAgent(client=client)
        result = agent.run("Analyse cohort C-2024Q1.")
        assert isinstance(result, str)

    def test_revenue_breakdown_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "get_revenue_breakdown",
            {"game_id": "GAME-01", "period": "2026-Q1"},
            "Realm Siege Online earned $6.5M in Q1 2026.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = GameRevenueAnalyticsAgent(client=client)
        result = agent.run("Break down GAME-01 revenue for Q1 2026.")
        assert isinstance(result, str)

    def test_forecast_game_revenue_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _tool_then_text(
            "forecast_game_revenue",
            {"game_id": "GAME-02", "horizon_months": 12},
            "Mech Blitz Arena projected to earn $38M over 12 months.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = GameRevenueAnalyticsAgent(client=client)
        result = agent.run("Forecast GAME-02 revenue for the next 12 months.")
        assert isinstance(result, str)

    def test_unknown_tool_returns_error(self):
        agent = GameRevenueAnalyticsAgent(client=MagicMock())
        result = agent._dispatch_tool("metaverse_oracle", {})
        assert "error" in result
