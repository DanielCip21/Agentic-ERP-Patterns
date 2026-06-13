"""Simulated finance tools: fraud detection, crypto payments, compliance, cash flow forecasting."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# Fraud Detection
# ---------------------------------------------------------------------------

_TRANSACTIONS: dict[str, dict] = {
    "TX-1001": {"id": "TX-1001", "account_id": "ACC-01", "amount": 2500.00, "currency": "USD", "counterparty": "Vendor A", "timestamp": "2026-06-10T09:15:00Z", "flagged": False},
    "TX-1002": {"id": "TX-1002", "account_id": "ACC-01", "amount": 89000.00, "currency": "USD", "counterparty": "Unknown Entity", "timestamp": "2026-06-11T02:47:00Z", "flagged": False},
    "TX-1003": {"id": "TX-1003", "account_id": "ACC-02", "amount": 450.00, "currency": "EUR", "counterparty": "Vendor B", "timestamp": "2026-06-12T14:00:00Z", "flagged": False},
    "TX-1004": {"id": "TX-1004", "account_id": "ACC-02", "amount": 150000.00, "currency": "USD", "counterparty": "Offshore LLC", "timestamp": "2026-06-13T00:05:00Z", "flagged": False},
}

_ACCOUNT_RISK: dict[str, dict] = {
    "ACC-01": {"account_id": "ACC-01", "owner": "Global Gaming International", "risk_score": 42, "avg_tx_amount": 5000, "jurisdictions": ["US", "EU", "SG"]},
    "ACC-02": {"account_id": "ACC-02", "owner": "Global Gaming Asia", "risk_score": 71, "avg_tx_amount": 3200, "jurisdictions": ["SG", "JP", "AU"]},
}

_ANOMALY_RULES = [
    {"rule": "large_amount", "threshold": 50000, "field": "amount"},
    {"rule": "odd_hours", "hours": [0, 1, 2, 3, 4], "field": "timestamp"},
    {"rule": "unknown_counterparty", "keywords": ["Unknown", "Offshore", "Shell"]},
]


def _anomaly_score(tx: dict) -> float:
    score = 0.0
    if tx["amount"] > 50000:
        score += 40
    hour = int(tx["timestamp"][11:13])
    if hour < 5:
        score += 30
    for kw in ["Unknown", "Offshore", "Shell"]:
        if kw.lower() in tx["counterparty"].lower():
            score += 30
    return min(score, 100.0)


def scan_transactions(account_id: str, window_hours: int = 24) -> list[dict[str, Any]]:
    results = []
    for tx in _TRANSACTIONS.values():
        if tx["account_id"] == account_id:
            score = _anomaly_score(tx)
            results.append({**tx, "anomaly_score": score, "high_risk": score >= 60})
    return results


def flag_transaction(tx_id: str, reason: str) -> dict[str, Any]:
    tx = _TRANSACTIONS.get(tx_id)
    if not tx:
        return {"error": f"Transaction {tx_id} not found"}
    tx["flagged"] = True
    tx["flag_reason"] = reason
    tx["flagged_at"] = datetime.utcnow().isoformat()
    return {"tx_id": tx_id, "flagged": True, "reason": reason}


def get_account_risk_profile(account_id: str) -> dict[str, Any]:
    profile = _ACCOUNT_RISK.get(account_id)
    if not profile:
        return {"error": f"Account {account_id} not found"}
    return {**profile, "risk_level": "HIGH" if profile["risk_score"] >= 70 else "MEDIUM" if profile["risk_score"] >= 40 else "LOW"}


# ---------------------------------------------------------------------------
# Crypto Payments
# ---------------------------------------------------------------------------

_CRYPTO_PAYMENTS: dict[str, dict] = {}

_EXCHANGE_RATES = {"USDT": 1.0, "ETH": 0.000285, "XRP": 1.82}  # units per USD


def initiate_crypto_payment(vendor_id: str, amount_usd: float, currency: str = "USDT") -> dict[str, Any]:
    if currency not in _EXCHANGE_RATES:
        return {"error": f"Unsupported currency '{currency}'. Supported: {list(_EXCHANGE_RATES)}"}
    payment_id = f"CP-{uuid.uuid4().hex[:8].upper()}"
    crypto_amount = round(amount_usd * _EXCHANGE_RATES[currency], 6)
    payment = {
        "payment_id": payment_id,
        "vendor_id": vendor_id,
        "amount_usd": amount_usd,
        "crypto_amount": crypto_amount,
        "currency": currency,
        "status": "pending_confirmation",
        "blockchain": "RippleNet" if currency == "XRP" else "Ethereum",
        "tx_hash": None,
        "initiated_at": datetime.utcnow().isoformat(),
    }
    _CRYPTO_PAYMENTS[payment_id] = payment
    return payment


def get_crypto_payment(payment_id: str) -> dict[str, Any]:
    p = _CRYPTO_PAYMENTS.get(payment_id)
    if not p:
        return {"error": f"Payment {payment_id} not found"}
    return p


def confirm_payment_settlement(payment_id: str) -> dict[str, Any]:
    p = _CRYPTO_PAYMENTS.get(payment_id)
    if not p:
        return {"error": f"Payment {payment_id} not found"}
    if p["status"] == "settled":
        return {"payment_id": payment_id, "status": "already_settled"}
    p["status"] = "settled"
    p["tx_hash"] = "0x" + uuid.uuid4().hex
    p["settled_at"] = datetime.utcnow().isoformat()
    p["block_confirmations"] = random.randint(12, 30)
    return p


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------

_JURISDICTION_RULES: dict[str, dict] = {
    "US": {"vat_rate": 0.0, "withholding_tax": 0.30, "filing_deadline": "Q1 Apr 15, Q2 Jun 15, Q3 Sep 15, Q4 Jan 15", "crypto_reporting": True, "aml_threshold_usd": 10000},
    "EU": {"vat_rate": 0.20, "withholding_tax": 0.15, "filing_deadline": "Monthly VAT returns", "crypto_reporting": True, "aml_threshold_usd": 10000},
    "SG": {"vat_rate": 0.09, "withholding_tax": 0.10, "filing_deadline": "Quarterly GST returns", "crypto_reporting": True, "aml_threshold_usd": 20000},
    "JP": {"vat_rate": 0.10, "withholding_tax": 0.20, "filing_deadline": "Annual corporate tax Mar 31", "crypto_reporting": True, "aml_threshold_usd": 15000},
    "AU": {"vat_rate": 0.10, "withholding_tax": 0.10, "filing_deadline": "Quarterly BAS", "crypto_reporting": True, "aml_threshold_usd": 10000},
}


def get_jurisdiction_rules(country_code: str) -> dict[str, Any]:
    rules = _JURISDICTION_RULES.get(country_code.upper())
    if not rules:
        return {"error": f"Jurisdiction '{country_code}' not configured"}
    return {"country": country_code.upper(), **rules}


def check_transaction_compliance(tx_id: str, jurisdiction: str) -> dict[str, Any]:
    tx = _TRANSACTIONS.get(tx_id)
    if not tx:
        return {"error": f"Transaction {tx_id} not found"}
    rules = _JURISDICTION_RULES.get(jurisdiction.upper())
    if not rules:
        return {"error": f"Jurisdiction '{jurisdiction}' not configured"}
    issues = []
    if tx["amount"] >= rules["aml_threshold_usd"]:
        issues.append(f"Amount ${tx['amount']:,.2f} meets AML reporting threshold (${rules['aml_threshold_usd']:,})")
    if rules["crypto_reporting"] and tx["currency"] not in ("USD", "EUR"):
        issues.append(f"Crypto currency {tx['currency']} requires regulatory disclosure")
    return {"tx_id": tx_id, "jurisdiction": jurisdiction.upper(), "compliant": len(issues) == 0, "issues": issues}


def generate_compliance_report(period: str, jurisdictions: list[str]) -> dict[str, Any]:
    rows = []
    for j in jurisdictions:
        rules = _JURISDICTION_RULES.get(j.upper(), {})
        total = sum(tx["amount"] for tx in _TRANSACTIONS.values() if tx["amount"] > 0)
        rows.append({
            "jurisdiction": j.upper(),
            "period": period,
            "total_transactions": len(_TRANSACTIONS),
            "total_value_usd": round(total, 2),
            "estimated_vat": round(total * rules.get("vat_rate", 0), 2),
            "estimated_withholding": round(total * rules.get("withholding_tax", 0), 2),
            "filing_deadline": rules.get("filing_deadline", "N/A"),
        })
    return {"report_id": f"CR-{uuid.uuid4().hex[:6].upper()}", "generated_at": datetime.utcnow().isoformat(), "jurisdictions": rows}


# ---------------------------------------------------------------------------
# Cash Flow Forecasting
# ---------------------------------------------------------------------------

_ACCOUNT_BALANCES: dict[str, dict] = {
    "USD": {"balance": 4_250_000.00, "available": 3_800_000.00},
    "EUR": {"balance": 1_100_000.00, "available": 980_000.00},
    "SGD": {"balance": 650_000.00, "available": 620_000.00},
    "JPY": {"balance": 75_000_000.00, "available": 70_000_000.00},
}

_FX_RATES_TO_USD: dict[str, float] = {
    "USD": 1.0, "EUR": 1.085, "SGD": 0.74, "JPY": 0.0065, "XRP": 0.55, "USDT": 1.0,
}


def get_account_balances(currency: str | None = None) -> dict[str, Any]:
    if currency:
        bal = _ACCOUNT_BALANCES.get(currency.upper())
        if not bal:
            return {"error": f"No account for currency '{currency}'"}
        rate = _FX_RATES_TO_USD.get(currency.upper(), 1.0)
        return {"currency": currency.upper(), **bal, "usd_equivalent": round(bal["balance"] * rate, 2)}
    result = {}
    for cur, bal in _ACCOUNT_BALANCES.items():
        rate = _FX_RATES_TO_USD.get(cur, 1.0)
        result[cur] = {**bal, "usd_equivalent": round(bal["balance"] * rate, 2)}
    return result


def get_fx_rates(base_currency: str, target_currencies: list[str]) -> dict[str, Any]:
    base_rate = _FX_RATES_TO_USD.get(base_currency.upper())
    if not base_rate:
        return {"error": f"Base currency '{base_currency}' not supported"}
    rates = {}
    for target in target_currencies:
        target_rate = _FX_RATES_TO_USD.get(target.upper())
        if target_rate:
            rates[target.upper()] = round(target_rate / base_rate, 6)
        else:
            rates[target.upper()] = None
    return {"base": base_currency.upper(), "rates": rates, "as_of": datetime.utcnow().isoformat()}


def forecast_cash_flow(horizon_days: int = 90, scenario: str = "base") -> dict[str, Any]:
    multipliers = {"optimistic": 1.15, "base": 1.0, "pessimistic": 0.82}
    m = multipliers.get(scenario.lower(), 1.0)
    monthly_inflow = 2_100_000 * m
    monthly_outflow = 1_750_000
    net_monthly = monthly_inflow - monthly_outflow
    periods = []
    cumulative = 0.0
    for i in range(1, (horizon_days // 30) + 1):
        inflow = round(monthly_inflow * (1 + random.uniform(-0.05, 0.05)), 2)
        outflow = round(monthly_outflow * (1 + random.uniform(-0.03, 0.03)), 2)
        net = round(inflow - outflow, 2)
        cumulative += net
        periods.append({"month": i, "inflow_usd": inflow, "outflow_usd": outflow, "net_usd": net, "cumulative_usd": round(cumulative, 2)})
    return {
        "scenario": scenario,
        "horizon_days": horizon_days,
        "fx_risk_note": "EUR/USD and JPY/USD positions carry 5-8% volatility exposure",
        "periods": periods,
        "summary": {"total_inflow": round(sum(p["inflow_usd"] for p in periods), 2), "total_outflow": round(sum(p["outflow_usd"] for p in periods), 2), "net_cashflow": round(cumulative, 2)},
    }
