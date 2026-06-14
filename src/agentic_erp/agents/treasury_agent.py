"""Pattern: AI-powered Cash & Treasury Management agent (crypto + fiat)."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import treasury_tools

_TOOLS = [
    {
        "name": "get_cash_position",
        "description": "Retrieve real-time global cash position across all bank accounts and currencies (including crypto).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "forecast_liquidity",
        "description": "AI-powered weekly liquidity forecast showing projected inflows, outflows, and shortage risks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "weeks_ahead": {"type": "integer", "description": "Number of weeks to forecast (default 4)"},
            },
        },
    },
    {
        "name": "convert_currency",
        "description": "Convert between currencies including crypto (XRP, USDT) and fiat (USD, EUR, GBP).",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string", "description": "Source currency code (USD, EUR, GBP, XRP)"},
                "to_currency": {"type": "string", "description": "Target currency code"},
                "amount": {"type": "number", "description": "Amount to convert"},
            },
            "required": ["from_currency", "to_currency", "amount"],
        },
    },
    {
        "name": "execute_fx_hedge",
        "description": "Execute an FX forward hedge to protect against currency fluctuations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "currency_pair": {"type": "string", "description": "Currency pair e.g. USD/EUR"},
                "notional_amount": {"type": "number", "description": "Notional amount to hedge in base currency"},
                "hedge_months": {"type": "integer", "description": "Hedge duration in months (default 3)"},
            },
            "required": ["currency_pair", "notional_amount"],
        },
    },
    {
        "name": "detect_payment_fraud",
        "description": "Run AI fraud detection on a payment transaction before authorizing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "transaction_amount": {"type": "number"},
                "vendor_id": {"type": "string"},
                "currency": {"type": "string"},
            },
            "required": ["transaction_amount", "vendor_id", "currency"],
        },
    },
    {
        "name": "reconcile_bank_statement",
        "description": "Reconcile a bank account GL balance against the external bank statement.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Bank account ID (e.g. BA-USD-001)"},
                "statement_balance": {"type": "number", "description": "Balance per bank statement"},
            },
            "required": ["account_id", "statement_balance"],
        },
    },
]

_SYSTEM_PROMPT = """You are an AI-powered Treasury Management Agent.
Your responsibilities:
- Monitor real-time global cash positions across fiat and crypto accounts
- Forecast liquidity and flag potential cash shortages before they occur
- Execute currency conversions and FX hedges to minimize FX risk
- Screen all payments for fraud before authorization
- Reconcile bank statements against the GL automatically
You support both traditional banking and blockchain-based payments (XRP, USDT).
Always recommend the most cost-effective payment method for cross-border transactions."""


class TreasuryManagementAgent(BaseERPAgent):
    """AI-driven treasury: liquidity forecasting, FX hedging, crypto payments, fraud detection."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_cash_position":
                return treasury_tools.get_cash_position()
            case "forecast_liquidity":
                return treasury_tools.forecast_liquidity(**inputs)
            case "convert_currency":
                return treasury_tools.convert_currency(**inputs)
            case "execute_fx_hedge":
                return treasury_tools.execute_fx_hedge(**inputs)
            case "detect_payment_fraud":
                return treasury_tools.detect_payment_fraud(**inputs)
            case "reconcile_bank_statement":
                return treasury_tools.reconcile_bank_statement(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
