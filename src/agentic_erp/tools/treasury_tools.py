"""Simulated Cash & Bank Management / Treasury tools."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any


_BANK_ACCOUNTS: dict[str, dict] = {
    "BA-USD-001": {"id": "BA-USD-001", "currency": "USD", "balance": 342000.00, "bank": "First National", "type": "operating"},
    "BA-EUR-001": {"id": "BA-EUR-001", "currency": "EUR", "balance": 87500.00, "bank": "Deutsche Bank", "type": "operating"},
    "BA-GBP-001": {"id": "BA-GBP-001", "currency": "GBP", "balance": 42000.00, "bank": "Barclays", "type": "operating"},
    "BA-CRYPTO-001": {"id": "BA-CRYPTO-001", "currency": "XRP", "balance": 15000.00, "bank": "RippleNet", "type": "crypto"},
}

_FX_RATES: dict[str, float] = {
    "USD/EUR": 0.92, "USD/GBP": 0.79, "USD/XRP": 0.52,
    "EUR/USD": 1.09, "GBP/USD": 1.27, "XRP/USD": 1.92,
}

_LIQUIDITY_FORECASTS: list[dict] = [
    {"week": "W1", "inflows": 85000.00, "outflows": 62000.00, "net": 23000.00},
    {"week": "W2", "inflows": 91000.00, "outflows": 78000.00, "net": 13000.00},
    {"week": "W3", "inflows": 73000.00, "outflows": 88000.00, "net": -15000.00},
    {"week": "W4", "inflows": 110000.00, "outflows": 95000.00, "net": 15000.00},
]


def get_cash_position() -> dict[str, Any]:
    positions = []
    total_usd = 0.0
    for acct in _BANK_ACCOUNTS.values():
        rate = _FX_RATES.get(f"{acct['currency']}/USD", 1.0)
        usd_equiv = acct["balance"] * rate
        total_usd += usd_equiv
        positions.append({
            "account_id": acct["id"],
            "currency": acct["currency"],
            "balance": acct["balance"],
            "usd_equivalent": round(usd_equiv, 2),
        })
    return {
        "as_of": datetime.utcnow().isoformat(),
        "accounts": positions,
        "total_usd_equivalent": round(total_usd, 2),
    }


def forecast_liquidity(weeks_ahead: int = 4) -> dict[str, Any]:
    forecasts = _LIQUIDITY_FORECASTS[:weeks_ahead]
    cumulative = sum(f["net"] for f in forecasts)
    shortage_weeks = [f["week"] for f in forecasts if f["net"] < 0]
    return {
        "forecast_weeks": weeks_ahead,
        "weekly_projections": forecasts,
        "cumulative_net_cashflow": cumulative,
        "liquidity_risk": "HIGH" if shortage_weeks else "LOW",
        "shortage_weeks": shortage_weeks,
        "recommendation": "Arrange short-term credit line" if shortage_weeks else "Liquidity position healthy",
    }


def convert_currency(from_currency: str, to_currency: str, amount: float) -> dict[str, Any]:
    rate_key = f"{from_currency}/{to_currency}"
    rate = _FX_RATES.get(rate_key)
    if not rate:
        return {"error": f"No FX rate available for {rate_key}"}
    fee_rate = 0.001 if "XRP" in rate_key else 0.003
    converted = amount * rate
    fee = amount * fee_rate
    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "original_amount": amount,
        "converted_amount": round(converted, 4),
        "exchange_rate": rate,
        "fee": round(fee, 4),
        "net_received": round(converted - fee * rate, 4),
        "converted_at": datetime.utcnow().isoformat(),
    }


def execute_fx_hedge(currency_pair: str, notional_amount: float, hedge_months: int = 3) -> dict[str, Any]:
    rate = _FX_RATES.get(currency_pair, 1.0)
    forward_premium = round(random.uniform(-0.01, 0.02), 4)
    forward_rate = round(rate + forward_premium, 4)
    hedge_id = f"FXH-{random.randint(10000, 99999)}"
    maturity = (datetime.utcnow() + timedelta(days=30 * hedge_months)).date().isoformat()
    return {
        "hedge_id": hedge_id,
        "currency_pair": currency_pair,
        "notional_amount": notional_amount,
        "spot_rate": rate,
        "forward_rate": forward_rate,
        "forward_premium": forward_premium,
        "maturity_date": maturity,
        "protected_amount": round(notional_amount * forward_rate, 2),
        "status": "active",
    }


def detect_payment_fraud(transaction_amount: float, vendor_id: str, currency: str) -> dict[str, Any]:
    flags = []
    if transaction_amount > 50000:
        flags.append("amount_exceeds_threshold")
    if currency in ("XRP", "USDT") and transaction_amount > 10000:
        flags.append("large_crypto_payment")
    if vendor_id not in ("VND-001", "VND-002", "VND-003"):
        flags.append("unknown_vendor")
    risk_score = min(100, len(flags) * 33 + random.randint(0, 10))
    return {
        "transaction_amount": transaction_amount,
        "vendor_id": vendor_id,
        "currency": currency,
        "risk_score": risk_score,
        "flags": flags,
        "action_required": risk_score > 50,
        "recommendation": "HOLD_FOR_REVIEW" if risk_score > 50 else "APPROVE",
    }


def reconcile_bank_statement(account_id: str, statement_balance: float) -> dict[str, Any]:
    account = _BANK_ACCOUNTS.get(account_id)
    if not account:
        return {"error": f"Account {account_id} not found"}
    gl_balance = account["balance"]
    variance = round(gl_balance - statement_balance, 2)
    return {
        "account_id": account_id,
        "gl_balance": gl_balance,
        "statement_balance": statement_balance,
        "variance": variance,
        "status": "RECONCILED" if abs(variance) < 1.0 else "VARIANCE_DETECTED",
        "action": "None required" if abs(variance) < 1.0 else f"Investigate ${abs(variance):,.2f} variance",
        "reconciled_at": datetime.utcnow().isoformat(),
    }
