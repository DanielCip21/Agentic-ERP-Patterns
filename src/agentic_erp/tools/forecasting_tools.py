"""Simulated Financial Forecasting, Compliance & Advanced Analytics tools."""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any


_FINANCIAL_SCENARIOS: dict[str, dict] = {
    "base": {"revenue_growth": 0.08, "cost_inflation": 0.04, "fx_headwind": 0.01},
    "bull": {"revenue_growth": 0.15, "cost_inflation": 0.03, "fx_headwind": -0.01},
    "bear": {"revenue_growth": -0.02, "cost_inflation": 0.07, "fx_headwind": 0.03},
}

_CURRENT_FINANCIALS: dict[str, float] = {
    "revenue": 4_800_000.00,
    "cogs": 2_200_000.00,
    "opex": 850_000.00,
    "ebitda": 1_750_000.00,
}

_TAX_JURISDICTIONS: dict[str, dict] = {
    "US": {"vat_rate": 0.0, "corp_tax": 0.21, "withholding": 0.30},
    "DE": {"vat_rate": 0.19, "corp_tax": 0.30, "withholding": 0.25},
    "BR": {"vat_rate": 0.17, "corp_tax": 0.34, "withholding": 0.15},
    "SG": {"vat_rate": 0.09, "corp_tax": 0.17, "withholding": 0.10},
}

_ESG_METRICS: dict[str, Any] = {
    "co2_tonnes_ytd": 1240,
    "renewable_energy_pct": 38,
    "employee_diversity_pct": 47,
    "supplier_esg_screened_pct": 62,
    "water_usage_liters_ytd": 8_500_000,
}


def generate_financial_forecast(scenario: str = "base", years_ahead: int = 3) -> dict[str, Any]:
    params = _FINANCIAL_SCENARIOS.get(scenario)
    if not params:
        return {"error": f"Unknown scenario '{scenario}'. Choose from: {list(_FINANCIAL_SCENARIOS.keys())}"}
    projections = []
    rev = _CURRENT_FINANCIALS["revenue"]
    cogs = _CURRENT_FINANCIALS["cogs"]
    opex = _CURRENT_FINANCIALS["opex"]
    for i in range(1, years_ahead + 1):
        rev = rev * (1 + params["revenue_growth"])
        cogs = cogs * (1 + params["cost_inflation"])
        opex = opex * (1 + params["cost_inflation"] * 0.8)
        fx_impact = rev * params["fx_headwind"]
        ebitda = rev - cogs - opex - fx_impact
        projections.append({
            "year": datetime.utcnow().year + i,
            "revenue": round(rev, 2),
            "cogs": round(cogs, 2),
            "opex": round(opex, 2),
            "ebitda": round(ebitda, 2),
            "ebitda_margin_pct": round(ebitda / rev * 100, 1),
        })
    return {
        "scenario": scenario,
        "base_year": datetime.utcnow().year,
        "assumptions": params,
        "projections": projections,
        "generated_at": datetime.utcnow().isoformat(),
    }


def calculate_tax_liability(revenue: float, jurisdiction: str) -> dict[str, Any]:
    tax = _TAX_JURISDICTIONS.get(jurisdiction.upper())
    if not tax:
        return {"error": f"Jurisdiction '{jurisdiction}' not configured. Available: {list(_TAX_JURISDICTIONS.keys())}"}
    corp_tax = round(revenue * 0.25 * tax["corp_tax"], 2)
    vat = round(revenue * tax["vat_rate"], 2)
    total = corp_tax + vat
    return {
        "jurisdiction": jurisdiction.upper(),
        "gross_revenue": revenue,
        "estimated_profit": round(revenue * 0.25, 2),
        "corporate_tax": corp_tax,
        "vat": vat,
        "total_tax_liability": total,
        "effective_rate": round(total / revenue * 100, 2),
        "withholding_rate": tax["withholding"],
        "calculated_at": datetime.utcnow().isoformat(),
    }


def run_esg_report() -> dict[str, Any]:
    co2_target = 1000
    renewable_target = 50
    diversity_target = 50
    score = 0
    flags = []
    if _ESG_METRICS["co2_tonnes_ytd"] <= co2_target:
        score += 25
    else:
        flags.append({"metric": "CO2 Emissions", "status": "ABOVE_TARGET", "gap": _ESG_METRICS["co2_tonnes_ytd"] - co2_target})
    if _ESG_METRICS["renewable_energy_pct"] >= renewable_target:
        score += 25
    else:
        flags.append({"metric": "Renewable Energy", "status": "BELOW_TARGET", "gap": renewable_target - _ESG_METRICS["renewable_energy_pct"]})
    if _ESG_METRICS["employee_diversity_pct"] >= diversity_target:
        score += 25
    else:
        flags.append({"metric": "Employee Diversity", "status": "BELOW_TARGET", "gap": diversity_target - _ESG_METRICS["employee_diversity_pct"]})
    if _ESG_METRICS["supplier_esg_screened_pct"] >= 80:
        score += 25
    else:
        flags.append({"metric": "Supplier ESG Screening", "status": "BELOW_TARGET", "gap": 80 - _ESG_METRICS["supplier_esg_screened_pct"]})
    return {
        "esg_score": score,
        "esg_rating": "A" if score >= 75 else "B" if score >= 50 else "C",
        "metrics": _ESG_METRICS,
        "improvement_areas": flags,
        "report_date": datetime.utcnow().date().isoformat(),
    }


def detect_fraud_pattern(gl_entries: list[dict]) -> dict[str, Any]:
    flags = []
    for entry in gl_entries:
        if entry.get("amount", 0) > 9500 and entry.get("amount", 0) < 10000:
            flags.append({"entry_id": entry.get("id"), "pattern": "structuring", "detail": "Amount just below $10K reporting threshold"})
        if entry.get("vendor") and entry.get("vendor") == entry.get("approver"):
            flags.append({"entry_id": entry.get("id"), "pattern": "self_approval", "detail": "Vendor matches approver — possible conflict of interest"})
    risk_level = "HIGH" if len(flags) >= 2 else "MEDIUM" if flags else "LOW"
    return {
        "entries_analyzed": len(gl_entries),
        "flags_found": len(flags),
        "risk_level": risk_level,
        "fraud_indicators": flags,
        "action": "Escalate to compliance team immediately" if risk_level == "HIGH" else "Review flagged entries",
    }


def model_risk_scenario(shock_type: str, magnitude_pct: float) -> dict[str, Any]:
    rev = _CURRENT_FINANCIALS["revenue"]
    shocks = {
        "revenue_decline": {"revenue_impact": -magnitude_pct / 100, "cost_impact": 0},
        "cost_spike": {"revenue_impact": 0, "cost_impact": magnitude_pct / 100},
        "fx_devaluation": {"revenue_impact": -magnitude_pct / 200, "cost_impact": magnitude_pct / 200},
        "credit_crisis": {"revenue_impact": -magnitude_pct / 150, "cost_impact": magnitude_pct / 300},
    }
    shock = shocks.get(shock_type)
    if not shock:
        return {"error": f"Unknown shock type. Choose from: {list(shocks.keys())}"}
    stressed_rev = rev * (1 + shock["revenue_impact"])
    stressed_cogs = _CURRENT_FINANCIALS["cogs"] * (1 + shock["cost_impact"])
    stressed_ebitda = stressed_rev - stressed_cogs - _CURRENT_FINANCIALS["opex"]
    return {
        "shock_type": shock_type,
        "magnitude_pct": magnitude_pct,
        "base_revenue": rev,
        "stressed_revenue": round(stressed_rev, 2),
        "stressed_ebitda": round(stressed_ebitda, 2),
        "ebitda_change_pct": round((stressed_ebitda - _CURRENT_FINANCIALS["ebitda"]) / _CURRENT_FINANCIALS["ebitda"] * 100, 1),
        "solvency_risk": stressed_ebitda < 0,
    }
